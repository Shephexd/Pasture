ARG LINCHFIN_IMAGE=linchfin
FROM $LINCHFIN_IMAGE AS builder

FROM python:3.8

# set args
ARG UID=1000
ARG GID=1000
ARG USERNAME=pasture

# set envs
ENV PORT=8080


WORKDIR /app

RUN apt-get update \
    && groupadd -g $GID $USERNAME \
    && useradd -g $GID -u $UID -d /home/$USERNAME -s /bin/bash $USERNAME \
    && apt install git libgeos-dev -y

COPY --from=builder /opt/linchfin/build/lib/linchfin /usr/local/lib/python3.8/site-packages/linchfin
COPY --from=builder /opt/linchfin/requirements.txt /app/linchfin_requirements.txt

COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r /app/linchfin_requirements.txt \
 && pip3 install -r /app/requirements.txt

COPY . /app
RUN python manage.py collectstatic --no-input \
    && chown -R $USERNAME:$USERNAME /app
USER $USERNAME

# RUN gunicorn
CMD ["/bin/bash", "/app/conf/run.sh"]
