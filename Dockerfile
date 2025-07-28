FROM kbase/sdkpython:3.8.0
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

RUN echo "start building docker image"

RUN apt-get update \
    && apt-get -y install python3-dev \
    && apt-get -y install wget \
    && apt-get -y install gcc

RUN pip install --upgrade pip \
    && pip3 install psutil numpy pyyaml \
    && python --version

ENV SPADES_VERSION='3.15.3'

RUN cd /opt \
    && wget https://github.com/ablab/spades/releases/download/v3.15.3/SPAdes-3.15.3-Linux.tar.gz \
    && tar -xvzf SPAdes-${SPADES_VERSION}-Linux.tar.gz \
    && rm SPAdes-${SPADES_VERSION}-Linux.tar.gz

ENV PATH $PATH:/opt/SPAdes-${SPADES_VERSION}-Linux/bin

# -----------------------------------------

COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module

WORKDIR /kb/module

RUN make

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
