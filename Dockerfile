FROM kbase/sdkbase2:python
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
    && pip3 install psutil \
    && python --version

ENV SPADES_VERSION='3.13.0'

RUN cd /opt \
    && wget http://cab.spbu.ru/files/release${SPADES_VERSION}/SPAdes-${SPADES_VERSION}-Linux.tar.gz \
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
