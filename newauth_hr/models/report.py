import datetime
from enum import Enum
from flask import current_app

from newauth.models import db, celery, User
from newauth.eveapi import EveAPIQuery
from .eve import InvType, InvGroup, StaStation, MapDenormalize
from .application import Application

class ReportStatus(Enum):
    generating = 'Generating'
    finished = 'Finished'
    failed = 'Failed'

def parse_eve_date(date):
    return datetime.datetime.strptime(
        date, '%Y-%m-%d %H:%M:%S')

@celery.task
def _generate_for_user(report, user):
    report = Report.query.get(report)
    user = User.query.get(user)
    try:
        for api_key in user.api_keys:
            api = EveAPIQuery(api_key=api_key)
            for character in api_key.characters:
                report.generate_for_character(api, character.id)
    except Exception as e:
        current_app.logger.exception(e)
        db.session.rollback()
        report.status = ReportStatus.failed.value
        db.session.commit()
    else:
        report.status = ReportStatus.finished.value
        db.session.commit()

@celery.task
def _generate_for_application(report, application):
    report = Report.query.get(report)
    application = Application.query.get(application)
    try:
        api = EveAPIQuery(api_key=application.api_key)
        api_info = api.get('account/APIKeyInfo')
        for character in api_info.characters.row:
            report.generate_for_character(api, character.characterID)
    except Exception as e:
        current_app.logger.exception(e)
        db.session.rollback()
        report.status = ReportStatus.failed.value
        db.session.commit()
    else:
        report.status = ReportStatus.finished.value
        db.session.commit()

class Report(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    application_id = db.Column(db.Integer(), db.ForeignKey('application.id'))
    generated = db.Column(db.DateTime(), default=db.func.now())
    status = db.Column(db.String())

    characters = db.relationship('ReportCharacter', 
                                 cascade='all, delete-orphan')
    user = db.relationship('User')
    application = db.relationship('Application')

    def generate_for_character(self, api, character_id):
        eve_character = api.get('eve/CharacterInfo', characterID=character_id)
        character = ReportCharacter(character_id=character_id)
        character.report_id = self.id
       
        character.character_name = eve_character.characterName
        character.skill_points = eve_character.skillPoints
        character.account_balance = eve_character.accountBalance
        character.security_status = eve_character.securityStatus
        
        character.last_known_location = eve_character.lastKnownLocation or None
        character.last_known_ship = eve_character.shipTypeName or None

        character.corporation_id = eve_character.corporationID
        character.corporation_name = eve_character.corporation
        if 'alliance' in eve_character:
            character.alliance_id = eve_character.allianceID
            character.alliance_name= eve_character.alliance

        db.session.add(character)

        # History
        ReportHistory.query.filter_by(
            character_id=character.id).delete()

        for history_corp in eve_character.employmentHistory.row:
            eve_corp = api.get('corp/CorporationSheet',
                               corporationID=history_corp.corporationID)
            corp = ReportCorporation.query.get(history_corp.corporationID)
            if not corp:
                corp = ReportCorporation(id=history_corp.corporationID)
            
            corp.name = eve_corp.corporationName
            corp.ticker = eve_corp.ticker
            
            if 'allianceName' in eve_corp:
                corp.alliance_id = eve_corp.allianceID
                corp.alliance_name = eve_corp.allianceName

            db.session.add(corp)

            history = ReportHistory(
                character_id=character.id,
                corporation_id=corp.id,
                start_date=parse_eve_date(history_corp.startDate)
            )
            db.session.add(history)

            character.history.append(history)

        # Contacts
        ReportContact.query.filter_by(character_id=character.id).delete()

        eve_contacts = api.get('char/ContactList',
                               characterID=character.character_id)
        for contact in eve_contacts.contactList.row:
            character.contacts.append(
                ReportContact(
                    id=contact.contactID,
                    name=contact.contactName,
                    standing=contact.standing,
                    type=contact.contactTypeID
                )
            )

        # Standings (NPC)

        ReportStanding.query.filter_by(character_id=character.id).delete()
        
        eve_standings = api.get('char/Standings',
                                characterID=character.character_id)
        for rowset in eve_standings:
            for standing in eve_standings[rowset].row:
                character.standings.append(
                    ReportStanding(
                        id=standing.fromID,
                        name=standing.fromName,
                        standing=standing.standing
                    )
                )

        # Wallet Journal
        ReportWalletJournal.query.filter_by(character_id=character.id).delete()

        eve_wallet = api.get('char/WalletJournal',
                             characterID=character.character_id,
                             rowCount=2560)
        for entry in eve_wallet.row:
            character.wallet.append(
                ReportWalletJournal(
                    from_name=entry.ownerName1,
                    to_name=entry.ownerName2,
                    amount=entry.amount,
                    reason=entry.reason if type(entry.reason) is unicode else '',
                    date=parse_eve_date(entry.date)
                )
            )

        # Assets
        ReportAsset.query.filter_by(character_id=character.id).delete()

        api_assets = api.get('char/AssetList', characterID=character.character_id)
        for asset in ReportAsset.parse_assets(api_assets):
            character.assets.append(asset)
            db.session.add(asset)

        return character


    @classmethod
    def generate_for_user(cls, user):
        report = Report.query.filter_by(user=user,
                                        status=ReportStatus.generating.value
                                        ).first()
        if report:
            return False
        report = cls(user=user, status=ReportStatus.generating.value)
        db.session.add(report)
        db.session.commit()
        _generate_for_user.delay(report=report.id, user=user.id)
        return True
        
            
    @classmethod
    def generate_for_application(cls, application):
        
        report = Report.query.filter_by(application=application,
                                       status=ReportStatus.generating.value
                                       ).first()
        if report:
            return False
        report = cls(application=application,
                     status=ReportStatus.generating.value)
        db.session.add(report)
        db.session.commit()
        _generate_for_application.delay(report=report.id,
                                     application=application.id)
        return True



        return report

class ReportCharacter(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    report_id = db.Column(db.Integer(), db.ForeignKey('report.id'),
                          nullable=False)

    character_id = db.Column(db.Integer(), nullable=False)
    character_name = db.Column(db.String(), nullable=False)
    
    skill_points = db.Column(db.Integer(), nullable=False)
    account_balance = db.Column(db.Integer(), nullable=False)
    security_status = db.Column(db.Integer(), nullable=False)

    corporation_id = db.Column(db.Integer(), nullable=False)
    corporation_name = db.Column(db.String(), nullable=False)

    alliance_id = db.Column(db.Integer())
    alliance_name = db.Column(db.String())

    last_known_location = db.Column(db.String())
    last_known_ship = db.Column(db.String())

    history = db.relationship('ReportHistory', cascade='all, delete-orphan')
    contacts = db.relationship('ReportContact',
                               order_by='desc(ReportContact.standing)',
                               cascade='all, delete-orphan')
    standings = db.relationship('ReportStanding',
                                order_by='desc(ReportStanding.standing)',
                                cascade='all, delete-orphan')
    wallet = db.relationship('ReportWalletJournal', 
                             cascade='all, delete-orphan')
    assets = db.relationship('ReportAsset', cascade='all, delete-orphan')

class ReportCorporation(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    alliance_id = db.Column(db.Integer())
    alliance_name = db.Column(db.String())
    ticker = db.Column(db.String(), nullable=False)

class ReportHistory(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    character_id = db.Column(db.Integer(), 
                             db.ForeignKey('report_character.id'),
                             nullable=False)
    corporation_id = db.Column(db.Integer(),
                               db.ForeignKey('report_corporation.id'),
                               nullable=False)
    start_date = db.Column(db.DateTime(), nullable=False)

    corporation = db.relationship('ReportCorporation')

class ReportContact(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    character_id = db.Column(db.Integer(), 
                             db.ForeignKey('report_character.id'),
                             primary_key=True)

    name = db.Column(db.String(), nullable=False)
    standing = db.Column(db.Float(), nullable=False)
    type = db.Column(db.Integer(), nullable=False)

class ReportStanding(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    character_id = db.Column(db.Integer(), 
                             db.ForeignKey('report_character.id'),
                             primary_key=True)

    name = db.Column(db.String(), nullable=False)
    standing = db.Column(db.Float(), nullable=False)
    
class ReportWalletJournal(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    character_id = db.Column(db.Integer(), 
                             db.ForeignKey('report_character.id'),
                             nullable=False)

    to_name = db.Column(db.String(), nullable=False)
    from_name = db.Column(db.String(), nullable=False)
    amount = db.Column(db.Float(), nullable=False)
    reason = db.Column(db.String())
    date = db.Column(db.DateTime, nullable=False)

class ReportAsset(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    character_id = db.Column(db.Integer(), 
                             db.ForeignKey('report_character.id'),
                             nullable=False)
    
    item_name = db.Column(db.String(), nullable=False)
    group_name = db.Column(db.String(), nullable=False)
    quantity = db.Column(db.Integer(), nullable=False)
    location_name = db.Column(db.String())
    base_price = db.Column(db.Float())
    
    @classmethod
    def parse_assets(cls, api_assets):
        assets = []
        for api_asset in api_assets.row:
            asset = cls()
            item_type = InvType.query.get(api_asset['typeID'])
            asset.item_name = item_type.type_name

            if 'locationID' in api_asset:
                pass
            
            asset.base_price = item_type.base_price or 0
            asset.group_name = item_type.group.group_name
            asset.quantity = api_asset.quantity
            
            assets.append(asset)

            if 'contents' in api_asset:
                assets += ReportAsset.parse_assets(
                    api_asset['contents'])
        
        return assets
