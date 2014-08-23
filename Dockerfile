# Dockaer Image for minidns

FROM prologic/crux-python
MAINTAINER James Mills, prologic at shortcircuit dot net dot au

# Services
EXPOSE 53/udp

# Startup
CMD ["/app/server.py"]

# Build/Runtime Dependencies
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Application
WORKDIR /app
ADD . /app
RUN pip install .
