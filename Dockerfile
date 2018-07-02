FROM debian:buster
MAINTAINER Rafal Fusik <rafalfusik@gmail.com>

USER root

RUN \
  apt-get update && \
  apt-get -y install -f && \
  apt-get -y install curl unzip ca-certificates gnupg2 && \
  apt-get -y install libxi6 libgconf-2-4

RUN \
  echo '**** Set up python **** ' \
  && apt-get install -y python python-dev python-distribute python-pip \
  && pip install pyvirtualdisplay \
  && pip install xvfbwrapper \
  && echo '**** Set up selenium, pytest **** ' \
  && pip install -U selenium \
  && pip install -U pytest pandas \
  && echo 'Setting up xvfb ...' \
  && apt-get -y install xvfb

RUN set -xe \
    && curl -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

RUN \
  echo '**** Create scraper directory  **** ' \
  && mkdir /usr/local/scraper

RUN \
    echo '**** Install chromedriver     **** ' && \
    CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    mkdir -p /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    curl -sS -o /tmp/chromedriver_linux64.zip http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip -qq /tmp/chromedriver_linux64.zip -d /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    rm /tmp/chromedriver_linux64.zip && \
    chmod +x /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver && \
    ln -fs /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver /usr/local/bin/chromedriver

RUN \
  echo '**** Copy test framework ****'

COPY test.py /usr/local/scraper
COPY scrape.py /usr/local/scraper
COPY webactions.py /usr/local/scraper
COPY urls.csv /usr/local/scraper


RUN \
  echo 'Awesome .... All went well !'
