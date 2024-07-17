FROM python:3.7.9

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
	unixodbc-dev \
	libgtk-3-0 \
	libdbus-glib-1-2 \
	xvfb \
	curl \
	vim \
	libasound2

RUN curl -sL "https://download.mozilla.org/?product=firefox-latest&os=linux64" -o t.tar.bz2 && \
	tar xjf t.tar.bz2 -C /opt/ && \
	ln -s /opt/firefox/firefox /usr/bin/firefox && \
	rm t.tar.bz2

RUN pip3 install tir_framework --upgrade && \
	find /usr -name geckodriver | xargs chmod +x