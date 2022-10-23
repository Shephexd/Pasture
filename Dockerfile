ARG LINCHFIN_IMAGE=linchfin
FROM $LINCHFIN_IMAGE AS builder

FROM python:3.8

# set args
ARG UID=1000
ARG GID=1000

# set envs
ENV PORT=8080

WORKDIR /app

RUN apt-get update \
    && apt install git -y

COPY --from=builder /opt/linchfin/build/lib/linchfin /usr/local/lib/python3.8/site-packages/linchfin
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r ./requirements.txt

COPY . /app
RUN groupadd -g $GID appuser \
    && adduser appuser --uid $UID --gid $GID
RUN python manage.py collectstatic --no-input
USER appuser

# RUN gunicorn
CMD ["/bin/bash", "/app/conf/run.sh"]
