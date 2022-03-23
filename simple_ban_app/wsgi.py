#!/bin/python3

from logging import getLogger, DEBUG, INFO
from time import sleep
from app import create_app, db
from os import getenv
from sqlalchemy.exc import OperationalError
from config import Config

db_connect_attempts = int(getenv("DB_CONNECT_ATTEMPTS", 3))

app = create_app(Config)

for i in range(db_connect_attempts):
    try:
        with app.app_context():
            db.create_all()
            break
    except OperationalError as err:
        if i + 1 == db_connect_attempts:
            app.logger.error(f"DB connection attempt failed after {i + 1} times. Please check the DB connection")
            app.logger.debug(f"The error description is next:\n\n{err}")
            exit(1)
        else:
            app.logger.info(f"Couldn't establish a DB connection. Waiting {i + 1} seconds for another attempt")
            sleep(i + 1)
    except ValueError:
        app.logger.error("The PostreSQL URI setting was not configured properly. Please check the environment variables")
        exit(1)

app.logger.info("The DB connection and Flask app were successfully initialized")

if __name__ != "__main__":
    app.logger.handlers.clear()
    gunicorn_logger = getLogger("gunicorn.error")
    app.logger.handlers.extend(gunicorn_logger.handlers)
    if app.config["DEBUG"]:
        app.logger.setLevel(DEBUG)
    else:
        app.logger.setLevel(INFO)

