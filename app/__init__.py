from os import getenv
from flask import Flask, Blueprint
from app.extensions import db
from smtplib import SMTP

simple_ban_app = Blueprint("simple_ban_app", __name__)
from app.routes import *


def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)
    set_db_smtp_urls(app)
    register_extensions(app)
    app.register_blueprint(simple_ban_app)
    return app

def register_extensions(app):
    db.init_app(app)
    from app.models import BlockList

def set_db_smtp_urls(app):
    if app.config["TESTING"]:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    else:
        db_host = getenv("SIMPLE_APP_DB_HOST")
        db_port = getenv("SIMPLE_APP_DB_PORT")
        db_name = getenv("SIMPLE_APP_DB_NAME")
        db_user = getenv("SIMPLE_APP_DB_USER")
        db_password = getenv("SIMPLE_APP_DB_PASSWORD")
        app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        app.config["SMTP_CLIENT"] = SMTP(getenv("SIMPLE_APP_SMTP_SERVER", "localhost"))

