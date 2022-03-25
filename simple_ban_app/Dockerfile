FROM python:latest

RUN python3 -m pip install flask Flask-SQLAlchemy gunicorn psycopg2

RUN mkdir -p /local/simple_ban_app
COPY . /local/simple_ban_app

WORKDIR /local/simple_ban_app
RUN python3 -m unittest discover test

HEALTHCHECK --interval=1m --timeout=30s --start-period=15s --retries=3 \
CMD curl -v --silent --header "requestor: automated_healthcheck" http://localhost:5000/healthcheck 2>&1 | grep '< HTTP/1.1 200 OK'

CMD /usr/local/bin/gunicorn wsgi:app --log-level=debug -b 0.0.0.0:5000

