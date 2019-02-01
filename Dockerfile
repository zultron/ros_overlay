# Boilerplate
ARG IMAGE_BASE
FROM ${IMAGE_BASE}

#####################
# Customize below
#####################

# Configure local apt repositories
ARG DEBIAN_SUITE=stretch
ARG DEBIAN_MIRROR=http.us.debian.org
ARG DEBIAN_SECURITY_MIRROR=security.debian.org
RUN bash -c "( \
        echo deb http://${DEBIAN_MIRROR}/debian ${DEBIAN_SUITE} main; \
        echo deb http://${DEBIAN_MIRROR}/debian ${DEBIAN_SUITE}-updates main; \
        echo deb http://${DEBIAN_SECURITY_MIRROR}/debian-security \
            ${DEBIAN_SUITE}/updates main; \
        ) | tee /etc/apt/sources.list"

# Emacs
RUN apt-get update && \
    apt-get install -y \
        # emacsclient
        emacs25-bin-common \
        # lcnc
        intltool \
        tclx8.4 \
        libreadline-gplv2-dev \
    && apt-get clean
