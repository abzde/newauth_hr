from functools import wraps
from flask import current_app, render_template, redirect, url_for, flash,\
        request, abort
from flask.ext.login import current_user
from flask.ext.classy import FlaskView, route
from flask.ext.login import login_required
from flask.ext.mail import Message
from flask.ext.wtf import Form
from wtforms import fields, validators

from newauth.app import mail
from newauth.models import Group, User, GroupMembership, db
from ..models import Report, Application, ApplicationStatus, Note

class NoteForm(Form):
    text = fields.TextAreaField('Text', [validators.Required()])

def hr_group_required(f):
    @wraps(f)
    def _inner(*a, **kw):
        if AdminView._can_access():
            return f(*a, **kw)
        else:
            return abort(403)
    return _inner
 

class AdminView(FlaskView):
    decorators = [login_required, hr_group_required]

    route_base = '/admin'

    @staticmethod
    def _can_access():
        if current_user.is_admin():
            return True

        g = Group.query.filter_by(name=current_app.config['HR_GROUP']).first()
        if not g:
            raise Exception('Group {} (HR_GROUP) not found'.format(
                current_app.config['HR_GROUP']))
        if current_user.is_member_of(g):
            return True
        return False

    def index(self):
        pending = Application.query.filter_by(
            status=ApplicationStatus.pending.value).all()
        app_activity = Application.query.filter(
            Application.handled_by!=None).order_by(Application.handled_at).all()
        note_activity = Note.query.order_by(Note.created_at).all()
        activity = sorted(app_activity + note_activity, 
            key=lambda m: m.handled_at 
                          if isinstance(m, Application) 
                          else m.created_at,
            reverse=True)
        print(activity)

        return render_template('admin/index.html', pending=pending,
                               activity=activity)

    def applications(self):
        applications = Application.query.all()

        return render_template('admin/list_applications.html',
                               applications=applications)

    def users(self):
        users = User.query.all()

        return render_template('admin/list_users.html', users=users)

    @route('/application/<application_id>')
    def view_application(self, application_id):
        application = Application.query.get(application_id)
        if not application:
            return abort(404)

        report = Report.query.filter_by(application=application
                    ).order_by(Report.generated.desc()).first()

        return render_template('admin/view_application.html',
                               application=application, report=report,
                               note_form=NoteForm())

    @route('/application/<application_id>/generate')
    def generate_application_report(self, application_id):
        application = Application.query.get(application_id)

        if not application:
            return abort(404)

        if Report.generate_for_application(application):
            flash('Report generation queued.', 'success')
        else:
            flash('Report already generating.', 'warning')

        return redirect(url_for('.AdminView:view_application',
                                application_id=application.id))

    @route('/application/<application_id>/accept')
    def accept(self, application_id):
        application = Application.query.get(application_id)

        if not application:
            return abort(404)

        application.status = ApplicationStatus.accepted.value
        application.handled_by = current_user
        application.handled_on = db.func.now()
        db.session.commit()

        flash('{} accepted to {}'.format(application.character_name,
                                         application.corporation.name),
              'success')

        msg = Message(
            subject='[{}] Accepted to {}'.format(
                current_app.config['EVE']['auth_name'],
                application.corporation.name),
            recipients=[application.email],
            html=render_template('emails/accepted.html',
                                 application=application)
        )
        
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.exception(e)
            flash('HR was unable to send an email out. '
                  'Please contact an adminstrator.', 'danger')

        return redirect(url_for('.AdminView:index'))

    @route('/application/<application_id>/reject')
    def reject(self, application_id):
        application = Application.query.get(application_id)

        if not application:
            return abort(404)

        application.status = ApplicationStatus.rejected.value
        application.handled_by = current_user
        application.handled_on = db.func.now()
        db.session.commit()

        flash('{} rejected from {}'.format(application.character_name,
                                           application.corporation.name),
              'warning')
        
        msg = Message(
            subject='[{}] Rejected from {}'.format(
                current_app.config['EVE']['auth_name'],
                application.corporation.name),
            recipients=[application.email],
            html=render_template('emails/rejected.html',
                                 application=application)
        )
        
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.exception(e)
            flash('HR was unable to send an email out. '
                  'Please contact an adminstrator.', 'danger')
        
        return redirect(url_for('.AdminView:index'))

    @route('application/<application_id>/note/add', methods=['POST'])
    def add_note(self, application_id):
        application = Application.query.get(application_id)
        if not application:
            abort(404)

        note_form=NoteForm()
        if note_form.validate_on_submit():
            note = Note(
                application=application,
                created_by=current_user,
                text=note_form.text.data)
            db.session.add(note)
            db.session.commit()

        return redirect(url_for('.AdminView:view_application',
                                application_id=application.id))

    @route('application/<application_id>/note/<note_id>/delete')
    def delete_note(self, application_id, note_id):
        note = Note.query.get(note_id)
        if not note:
            abort(404)

        if not (note.created_by == current_user or current_user.is_admin()):
            abort(403)

        db.session.delete(note)
        db.session.commit()
        return redirect(url_for('.AdminView:view_application',
                                application_id=application_id))

    @route('/user/<user_id>')
    def view_user(self, user_id):
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            abort(404)

        report = Report.query.filter_by(user=user
                    ).order_by(Report.generated.desc()).first()

        return render_template('admin/view_user.html', user=user,
                                      report=report)

    @route('/user/<user_id>/generate')
    def generate_user_report(self, user_id):
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            abort(404)
        
        if Report.generate_for_user(user):
            flash('Report generation queued.', 'success')
        else:
            flash('Report already generating.', 'warning')
        
        return redirect(url_for('.AdminView:view_user', user_id=user_id))

