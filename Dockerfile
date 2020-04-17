FROM phusion/passenger-full:1.0.5
LABEL maintainer="DataKitchen Developers <dev@datakitchen.io>"

########################################################################
# Use baseimage-docker's init system.
########################################################################
CMD ["/sbin/my_init"]

########################################################################
# Create a place to copy source code
########################################################################
ENV APP_HOME=/usr/src/datakitchen
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

########################################################################
# Install pip
########################################################################
RUN apt-get update && apt-get install --yes \
    python-distribute\
    python3 \
    python3-dev \
    python3-pip

########################################################################
# Install requirements
########################################################################
RUN mkdir -p DKUtils
WORKDIR $APP_HOME/DKUtils
COPY requirements.txt .
COPY requirements-dev.txt .
RUN pip3 install -r requirements-dev.txt
RUN rm requirements.txt
RUN rm requirements-dev.txt

########################################################################
# Clean up APT when done.
########################################################################
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

########################################################################
# Add datakitchen user - the UID and GID need to be consistent across
# servers.
########################################################################
RUN groupadd datakitchen -g 1001
RUN useradd -u 1001 -g 1001 datakitchen

########################################################################
# Permissions
# Make sure everything in application directory is owned by datakitchen
########################################################################
RUN chown --recursive datakitchen:datakitchen $APP_HOME
USER datakitchen
ENV HOME=/home/datakitchen