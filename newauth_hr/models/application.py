from enum import Enum

from newauth.models import db

class ApplicationStatus(Enum):
    pending = 'Pending'
    accepted = 'Accepted'
    rejected = 'Rejected'

class Application(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_key.id'),
                           nullable=False)
    corporation_id = db.Column(db.Integer(), db.ForeignKey('auth_contact.id'),
                               nullable=False)

    character_id = db.Column(db.Integer(), nullable=False)
    character_name = db.Column(db.String(), nullable=False)
    current_corporation_id = db.Column(db.Integer(), nullable=False)
    current_corporation_name = db.Column(db.String(), nullable=False)
    current_alliance_id = db.Column(db.Integer())
    current_alliance_name = db.Column(db.String())

    email = db.Column(db.String(), nullable=False)
    motivation = db.Column(db.Text(), nullable=False)

    status = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=db.func.now())
    last_updated_at = db.Column(db.DateTime(), default=db.func.now())

    handled_by_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    handled_at = db.Column(db.DateTime())

    api_key = db.relationship('APIKey')
    corporation = db.relationship('AuthContact')
    handled_by = db.relationship('User')
