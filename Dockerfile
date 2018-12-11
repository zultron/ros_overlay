# Boilerplate
ARG IMAGE_BASE
FROM ${IMAGE_BASE}

# Customize below
RUN apt-get install -y \
    # emacsclient
    emacs25-bin-common \
    && apt-get clean
