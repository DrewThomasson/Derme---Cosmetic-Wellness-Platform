from datetime import datetime
from yourapp import db

class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40))
    relation = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmergencyCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255))   # stored file name (local or cloud path)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    lang = db.Column(db.String(8), default='en')
    qr_data = db.Column(db.Text)