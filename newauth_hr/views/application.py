from flask import redirect, url_for, render_template, request, jsonify,\
        session, flash, current_app, abort
from flask.ext.classy import FlaskView, route
from flask.ext.wtf import Form
from wtforms import fields, validators

from newauth.eveapi import EveAPIQuery, AuthenticationException
from newauth.models import AuthContact, APIKey, db
from ..models import Application, ApplicationStatus

class APIForm(Form):
    key_id = fields.IntegerField('Key ID', [validators.Required()])
    vcode = fields.StringField('vCode', [validators.Required()])

class ApplicationForm(Form):
    character = fields.IntegerField('Character', [validators.Required()])
    corporation = fields.IntegerField('Corporation', [validators.Required()])
    email = fields.StringField('Email', [validators.Email()])
    motivation = fields.TextAreaField('Motivation', [validators.Required()])


def clear_session():
    if 'api_info' in session: del session['api_info']
    if 'key_id' in session: del session['key_id']
    if 'vcode' in session: del session['vcode']

class ApplicationView(FlaskView):
    route_base = '/'

    @route('/', methods=['GET', 'POST'])
    def index(self):
        clear_session()

        api_form = APIForm()
        if api_form.validate_on_submit():
            print(api_form)
            api = EveAPIQuery(key_id=api_form.key_id.data,
                              vcode=api_form.vcode.data)
            try:
                api_info = api.get('account/APIKeyInfo')
            except AuthenticationException:
                flash('Invalid API key', 'danger')
                return redirect(url_for('.ApplicationView:index'))

            requirements = current_app.config['EVE']['requirements']
            if api_info.accessMask != requirements['internal']['mask']:
                flash('Invalid API mask', 'danger')
                return redirect(url_for('.ApplicationView:index'))
            
            if requirements['internal']['expires'] == False and\
               api_info.expires:
                flash("Please provide a  API key that doesn't expire")
                return redirect(url_for('.ApplicationView:index'))

            session['api_info'] = api_info
            session['key_id'] = api_form.key_id.data
            session['vcode'] = api_form.vcode.data

            return redirect(url_for('.ApplicationView:application'))

        return render_template('api.html', api_form=api_form)

    @route('/application/', methods=['GET', 'POST'])
    def application(self):
        if not session.get('api_info', None):
            flash('Invalid session', 'warning')
            return redirect(url_for('.ApplicationView:index'))
        else:
            api_info = session['api_info']

        application_form = ApplicationForm()
        characters = api_info['characters']['row']
        corporations = AuthContact.query.filter_by(internal=True).all()

        if application_form.validate_on_submit():
            # check submitted character is in api key's characters
            for character in characters:
                if application_form.character.data == character['characterID']:
                    character_name = character['characterName']
                    current_corp_id = character['corporationID']
                    current_corp_name = character['corporationName']
                    if character['allianceID']:
                        current_alliance_id = character['allianceID']
                        current_alliance_name = character['allianceName']
                    else:
                        current_alliance_id = None
                        current_alliance_name = None
                    break
            else:
                flash('Invalid character', 'danger')
                return redirect(url_for('.ApplicationView:index'))
            
            # check submitted corporation is in internal corporation list
            if application_form.corporation.data \
               not in [c.id for c in corporations]:
                flash('Invalid corporation', 'danger')
                return redirect(url_for('.ApplicationView:index'))

            key_id, vcode = session['key_id'], session['vcode']
            api_key = APIKey.query.filter_by(
                key_id=key_id, vcode=vcode).first()
            if not api_key:
                api_key = APIKey(key_id=session['key_id'], vcode=session['vcode'])
            api_key.update_api_key()
            db.session.add(api_key)

            application = Application.query.filter_by(
                api_key=api_key, status=ApplicationStatus.pending.value).first()

            if application:
                flash('You already have a pending application', 'warning')
                return redirect(url_for('.ApplicationView:index'))

            application = Application(
                corporation_id=application_form.corporation.data,
                email=application_form.email.data,
                motivation=application_form.motivation.data,
                api_key=api_key,
                status=ApplicationStatus.pending.value,
                character_id=application_form.character.data,
                character_name=character_name,
                current_corporation_id=current_corp_id,
                current_corporation_name=current_corp_name,
                current_alliance_id=current_alliance_id,
                current_alliance_name=current_alliance_name
            )
            db.session.add(application)
            db.session.commit()
    
            clear_session()
            
            return render_template('success.html')
        else:
            for field, errors in application_form.errors.items():
                for error in errors:
                    flash("Error in {} field - {}".format(
                        getattr(application_form, field).label.text,
                        error), 'danger')

        return render_template('apply.html', application_form=application_form,
                               characters=characters, corporations=corporations)



