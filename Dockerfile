FROM python:3-alpine

ARG WORKDIR=/data/

WORKDIR $WORKDIR

RUN apk update && apk upgrade && \
  apk add bash curl gcc musl-dev libffi-dev linux-headers chromium-chromedriver chromium && \
  ln  -s /usr/bin/chromium-driver /usr/bin/chrome && \
  pip install --upgrade pip && \
  pip install flask bcrypt selenium

COPY entrypoint.sh flask_test_executor.py $WORKDIR

ENTRYPOINT ["./entrypoint.sh"]