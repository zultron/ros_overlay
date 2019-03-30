#!/usr/bin/python

# API call examples
#   https://gist.github.com/alexanderilyin/8cf68f85b922a7f1757ae3a74640d48a
# Docker registry API
#   https://docs.docker.com/registry/spec/api/
#   https://docs.docker.com/registry/spec/auth/token/

import os, json, base64, requests, time

class DockerRegistryAuth(object):
    _auth = dict()
    _tokens = dict()

    _params = dict(
        auth_domain="auth.docker.io",
        auth_service="registry.docker.io",
    )

    @classmethod
    def update_params(cls, params, **kwargs):
        params.update(cls._params)
        for k, v in kwargs.items():
            params[k] = v

    def __init__(self):

        # Get stuff into __dict__
        self.__dict__.update(self._params)

    def get_config_from_environment(self):
        DOCKERCFG_str = os.environ['DOCKERCFG']
        DOCKERCFG = json.loads(DOCKERCFG_str)
        for data in DOCKERCFG.values():
            if data['serveraddress'] == self.api_domain:
                return data

        raise RuntimeError("Couldn't find config for %s API" % self.api_domain)

    def get_config_from_file(self):

        config = os.path.join(os.environ['HOME'], '.docker/config.json')
        with open(config, 'r') as f:
            DOCKERCFG = json.load(f)
        for data in DOCKERCFG['auths'].values():
            if 'auth' in data:
                return data['auth']

        raise RuntimeError("Couldn't find config for %s API" % self.api_domain)

    @property
    def auth(self):
        if 'service_config' in self._params:
            return self._params['service_config']
        else:
            if 'DOCKERCFG' in os.environ:
                res = self.get_config_from_environment()['auth']
            else:
                res = self.get_config_from_file()
            self._params['service_config'] = res
            return res

    @property
    def auth_basic_headers(self):
        return dict(Authorization = "Basic %s" % self.auth)

    def auth_token_headers(self, access='pull'):
        return dict(Authorization = "Bearer %s" % self.token(access))

    def scope(self, access='pull'):
        return '%s:%s:%s' % (self.scope_prefix, self.name, access)

    def req_method(self, spec):
        # "GET /v2/<name>/tags/list" -> requests.get
        return getattr(requests, spec.split(' ', 1)[0].lower())

    def req_url(self, spec, extra_kwargs={}):
        # "GET /v2/<name>/tags/list" -> "https://domain/v2/{name}/tags/list"
        fmt = spec.split(' ', 1)[1].replace('<','{').replace('>','}')
        kwargs = dict(scope = self.scope(extra_kwargs.get('access','pull')))
        kwargs.update(self.__dict__)
        kwargs.update(extra_kwargs)
        return ("https://{api_domain}" + fmt).format(**kwargs)

    def request(self, spec, headers={},
                return_json=True, access='pull', **req_kwargs):
        req_method = self.req_method(spec)
        req_url = self.req_url(spec, req_kwargs)
        if 'Authorization' not in headers:
            headers.update(self.auth_token_headers(access))
        rsp = req_method(req_url, headers=headers)
        if not rsp.ok:
            print req_method, req_url, headers
            print rsp
            print rsp.__dict__
            print rsp.request.__dict__
            raise RuntimeError("Request failed for '%s'" % req_url)
        if return_json:
            rsp_json = rsp.json()
            rsp_json['debug'] = dict(
                headers=headers, method=req_method, url=req_url)
            rsp_json['obj'] = rsp
            return rsp_json
        else:
            return rsp


    def get_token(self, access='pull'):
        now = time.time()
        if self._tokens.get(self.scope(access),{}).get('expires',0) > now:
            # print "Reusing token for scope %s" % self.scope(access)
            return self._tokens[self.scope(access)]['token']

        spec = "GET /token?service=<auth_service>&scope=<scope>&offline_token=1"
        token = self.request(spec,
                             headers=self.auth_basic_headers,
                             api_domain=self.auth_domain)

        # print "Got new token for scope %s" % self.scope(access) # FIXME

        token['expires'] = now + token['expires_in'] - 10 # Fudge time
        self._tokens[self.scope(access)] = token
        return token['token']

    def clear_token(self, access):
        if self.scope(access) in self._tokens:
            del self._tokens[self.scope(access)]

    def token(self, access='pull'):
        return self.get_token(access)

class DockerRepo(DockerRegistryAuth):
    scope_prefix = 'repository'

    _params = dict()
    DockerRegistryAuth.update_params(
        _params, api_domain = "registry-1.docker.io")

    def __init__(self, name):
        self.name = name

        super(DockerRepo, self).__init__()

    def get_tags(self):
        spec = "GET /v2/<name>/tags/list"
        return self.request(spec)['tags']

    def get_image(self, reference):
        spec = "GET /v2/<name>/manifests/<reference>"
        headers = dict(
            Accept = "application/vnd.docker.distribution.manifest.v2+json")
        rsp = self.request(spec, reference=reference, headers=headers)
        rsp['digest'] = rsp['obj'].headers['Docker-Content-Digest']
        return rsp

    def delete_image(self, reference):
        if not reference.startswith('sha256:'):
            # Look up digest using name
            i = self.get_image(reference)
            print "Using digest %s for name %s" % (i['digest'], reference)
            reference = i['digest']

        spec = "DELETE /v2/<name>/manifests/<reference>"
        # name = repo; reference = image digest
        return self.request(spec, reference=reference, access='delete,pull,push')


if __name__ == "__main__":
    repo = os.environ.get('DOCKER_REPO','tormach/ros')
    for t in DockerRepo(repo).get_tags():
        print t
