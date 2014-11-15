from newauth.models import db
from .application import Application

class Note(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    application_id = db.Column(db.Integer(), db.ForeignKey('application.id',
                                                           ondelete='CASCADE'),
                               nullable=False)
    text = db.Column(db.Text())
    
    created_by_id = db.Column(db.Integer(), 
                           db.ForeignKey('user.id', ondelete='CASCADE'), 
                           nullable=False)
    created_at = db.Column(db.DateTime(), default=db.func.now())

    created_by = db.relationship('User')
    application = db.relationship('Application', backref='notes')
