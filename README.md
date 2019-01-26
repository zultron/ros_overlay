# Docker Hub automated overlay image build

This repo configures automated Docker Hub overlay image builds when
the image tag doesn't correspond to any Git branch or tag name.

The base image repo contains images that are pushed, with tags like
`upstream_id/ros:foo-10.2e98a77`.  The `10.2e98a77` portion is a version
whose major version increments on successive versions (minor version
is a hash).  We want a new push to trigger an automated overlay image
build for `my_id/ros_overlay:foo-10.2e98a77`; i.e. the same tag but
push to the Docker Hub overlay repo.


The build is triggered from the base repo with a webhook.  The build
stage hook in `hooks/build` queries the base repo.  It assumes the
pushed base image is the highest tag version and builds the overlay
image with matching tag.  The `hooks/push` script pushes the newly
built image (the default push routine will try to push the nonexistent
`my_id/ros_overlay:latest` tag and hang).

## Setting up an automated build

- Clone this repository in GitHub
- Create a new automated on Docker Hub linked to the GitHub repository
  - Define a build environment variable `BASE_REPO` with the
    `upstream_id/repo` of the base image
  - Add a build trigger (any name) and copy the trigger URL
- In the base repo, add a webhook and paste the trigger URL

If all goes well, whenever a new image is pushed to the base repo, it
will trigger a build in your overlay repo, and a new overlay image
will be built on the new base image with matching tag.
