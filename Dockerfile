FROM prologic/python-runtime:2.7
MAINTAINER James Mills, prologic at shortcircuit dot net dot au

EXPOSE 53/udp

ENTRYPOINT ["udnsd"]
CMD []

RUN apk -U add build-base python-dev linux-headers git && \
    rm -rf /var/cache/apk/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

WORKDIR /app
COPY . /app/
RUN pip install .
