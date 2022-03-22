# This module is used to avoid circular imports of the SQLAlchemy extension in other modules

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

