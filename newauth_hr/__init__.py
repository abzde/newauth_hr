from pkg_resources import resource_string
from flask import render_template, abort, flash, redirect, url_for,\
        current_app, request, Blueprint
from flask.ext.login import current_user
from flask.ext.classy import FlaskView, route
from sqlalchemy.event import listens_for


from newauth.models import db, User, Group
from .models.application import ApplicationStatus
from .views import AdminView, ApplicationView
from . import assets

blueprint = Blueprint('hr', __name__, static_folder='public',
                      template_folder='templates', url_prefix='/hr')

AdminView.register(blueprint)
ApplicationView.register(blueprint)

class HR(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        @listens_for(db.get_engine(app, 'eve_sde'), 'connect')
        def on_connect(dbapi_conn, connection_record):
            dbapi_conn.text_factory = str

        app.config.setdefault('HR_GROUP', app.config['ADMIN_GROUP'])
        
        app.register_blueprint(blueprint)

        app.navbar['extra'].append((
            'fa-inbox', 'HR', 'hr.AdminView:index', AdminView._can_access))

    
        app.logger.debug('HR initialized')
