FROM python:3

MAINTAINER Dmitry Moroz "mds.freeman@gmail.com"

EXPOSE 2000

ADD server /app/src/
ADD requirements.txt /app/src/
WORKDIR /app/src/

RUN pip install -r requirements.txt

CMD ["invoke", "run-server", "-l", "DEBUG"]
