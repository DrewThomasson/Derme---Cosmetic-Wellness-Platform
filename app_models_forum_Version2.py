from datetime import datetime
from yourapp import db

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200))
    body = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    closed = db.Column(db.Boolean, default=False)

class ForumComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContentReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(20))  # 'post' or 'comment'
    content_id = db.Column(db.Integer)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reason = db.Column(db.String(255))
    status = db.Column(db.String(32), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)