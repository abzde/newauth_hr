from sqlalchemy.event import listens_for
from sqlalchemy.pool import Pool

from newauth.models import db

class InvGroup(db.Model):
# CREATE TABLE "invGroups" (
#   "groupID" integer NOT NULL,
#   "categoryID" integer DEFAULT NULL,
#   "groupName" varchar(100) DEFAULT NULL,
#   "description" varchar(3000) DEFAULT NULL,
#   "iconID" integer DEFAULT NULL,
#   "useBasePrice" integer DEFAULT NULL,
#   "allowManufacture" integer DEFAULT NULL,
#   "allowRecycler" integer DEFAULT NULL,
#   "anchored" integer DEFAULT NULL,
#   "anchorable" integer DEFAULT NULL,
#   "fittableNonSingleton" integer DEFAULT NULL,
#   "published" integer DEFAULT NULL,
#   PRIMARY KEY ("groupID")
# );

    __bind_key__ = 'eve_sde'
    __tablename__ = 'invGroups'

    group_id = db.Column('groupID', db.Integer(), primary_key=True)
    group_name = db.Column('groupName', db.String())

class InvType(db.Model):
# CREATE TABLE "invTypes" (
#   "typeID" integer NOT NULL,
#   "groupID" integer DEFAULT NULL,
#   "typeName" varchar(100) DEFAULT NULL,
#   "description" varchar(3000) DEFAULT NULL,
#   "mass" double DEFAULT NULL,
#   "volume" double DEFAULT NULL,
#   "capacity" double DEFAULT NULL,
#   "portionSize" integer DEFAULT NULL,
#   "raceID" integer  DEFAULT NULL,
#   "basePrice" decimal(19,4) DEFAULT NULL,
#   "published" integer DEFAULT NULL,
#   "marketGroupID" integer DEFAULT NULL,
#   "chanceOfDuplicating" double DEFAULT NULL,
#   PRIMARY KEY ("typeID")
# );
    __bind_key__ = 'eve_sde'
    __tablename__ = 'invTypes'

    type_id = db.Column('typeID', db.Integer(), primary_key=True)
    group_id = db.Column('groupID', db.ForeignKey('invGroups.groupID'))
    type_name = db.Column('typeName', db.String())
#    description = db.Column('description', db.String(convert_unicode='force',
#                                                     unicode_error='ignore'))
    description = db.Column('description', db.UnicodeText())
    mass = db.Column('mass', db.Float())
    volume = db.Column('volume', db.Float())
    capacity = db.Column('capacity', db.Float())
    portion_size = db.Column('portionSize', db.Integer())
    race_id = db.Column('raceID', db.Integer())
    base_price = db.Column('basePrice', db.Float())
    published  = db.Column('published', db.Integer())
    market_group_id = db.Column('marketGroupID', db.Integer())
    chance_of_duplicating = db.Column('chanceOfDuplicating', db.Float())

    group = db.relationship('InvGroup')

class StaStation(db.Model):
# CREATE TABLE "staStations" (
#   "stationID" integer NOT NULL,
#   "security" integer DEFAULT NULL,
#   "dockingCostPerVolume" double DEFAULT NULL,
#   "maxShipVolumeDockable" double DEFAULT NULL,
#   "officeRentalCost" integer DEFAULT NULL,
#   "operationID" integer  DEFAULT NULL,
#   "stationTypeID" integer DEFAULT NULL,
#   "corporationID" integer DEFAULT NULL,
#   "solarSystemID" integer DEFAULT NULL,
#   "constellationID" integer DEFAULT NULL,
#   "regionID" integer DEFAULT NULL,
#   "stationName" varchar(100) DEFAULT NULL,
#   "x" double DEFAULT NULL,
#   "y" double DEFAULT NULL,
#   "z" double DEFAULT NULL,
#   "reprocessingEfficiency" double DEFAULT NULL,
#   "reprocessingStationsTake" double DEFAULT NULL,
#   "reprocessingHangarFlag" integer  DEFAULT NULL,
#   PRIMARY KEY ("stationID")
# );
    __bind_key__ = 'eve_sde'
    __tablename__ = 'staStations'

    station_id = db.Column('stationID', db.Integer(), primary_key=True)
    station_name = db.Column('stationName', db.String())

class MapDenormalize(db.Model):
# CREATE TABLE "mapDenormalize" (
#   "itemID" integer NOT NULL,
#   "typeID" integer DEFAULT NULL,
#   "groupID" integer DEFAULT NULL,
#   "solarSystemID" integer DEFAULT NULL,
#   "constellationID" integer DEFAULT NULL,
#   "regionID" integer DEFAULT NULL,
#   "orbitID" integer DEFAULT NULL,
#   "x" double DEFAULT NULL,
#   "y" double DEFAULT NULL,
#   "z" double DEFAULT NULL,
#   "radius" double DEFAULT NULL,
#   "itemName" longtext,
#   "security" double DEFAULT NULL,
#   "celestialIndex" integer DEFAULT NULL,
#   "orbitIndex" integer DEFAULT NULL,
#   PRIMARY KEY ("itemID")
# );
    __bind_key__ = 'eve_sde'
    __tablename__ = 'mapDenormalize'

    item_id = db.Column('itemID', db.Integer(), primary_key=True)
    item_name = db.Column('itemName', db.String())
