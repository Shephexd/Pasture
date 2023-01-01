ARG LINCHFIN_IMAGE=linchfin
FROM $LINCHFIN_IMAGE AS builder

FROM python:3.8

# set args
ARG UID=1000
ARG GID=1000
ARG USERNAME=pasture

EXPOSE 8080

WORKDIR /app

RUN apt-get update \
    && groupadd -g $GID $USERNAME \
    && useradd -g $GID -u $UID -d /home/$USERNAME -s /bin/bash $USERNAME \
    && apt install git libgeos-dev nginx -y

COPY --from=builder /opt/linchfin/build/lib/linchfin /usr/local/lib/python3.8/site-packages/linchfin
COPY --from=builder /opt/linchfin/requirements.txt /app/linchfin_requirements.txt

COPY ./requirements.txt /app/requirements.txt

RUN pip3 install -r /app/linchfin_requirements.txt \
 && pip3 install -r /app/requirements.txt

ENV NGINX_SET_REAL_IP_FROM="10.1.0.0/16"\
    PROXY_PASS="unix:/tmp/gunicorn.sock"\
    RESOURCE_DIR="/app/pasture/resources"
COPY . /app
RUN chmod 755 /app/conf/run.sh \
    && mv /app/conf/nginx/nginx.conf /etc/nginx/nginx.conf \
    && mv /app/conf/nginx/webapp.conf /etc/nginx/conf.d/webapp.conf \
    && ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log
# RUN webapp
CMD ["/bin/bash", "/app/conf/run.sh"]