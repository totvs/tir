FROM python:3.12

ENV DEBIAN_FRONTEND=noninteractive

USER root

RUN apt-get update && apt-get install -y \
	unixodbc-dev \
	libgtk-3-0 \
	libdbus-glib-1-2 \
	xvfb \
	curl \
	vim \
	libasound2

RUN curl -sL "https://download.mozilla.org/?product=firefox-latest&os=linux64" -o t.tar.xz && \
	tar xJf t.tar.xz -C /opt/ && \
	ln -s /opt/firefox/firefox /usr/bin/firefox && \
	rm t.tar.xz

RUN pip3 install tir_framework --upgrade && \
	find /usr -name geckodriver | xargs chmod +x

USER ${USERNAME}
