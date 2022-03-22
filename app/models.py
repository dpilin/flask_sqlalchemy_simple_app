from app import db

class BlockList(db.Model):
    __tablename__ = "blocklist"

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String())
    ip = db.Column(db.String())
    timestamp = db.Column(db.DateTime())

