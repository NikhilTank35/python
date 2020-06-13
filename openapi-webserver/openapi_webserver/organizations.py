# Copyright (C) 2020, Sardoodledom (github1@lotkit.org)
# All rights reserved.
#
# Although you can see the source code, it is not free and is
# protected by copyright. If you are interested in using it, please
# contact us at: github1@lotkit.org

import datetime
import logging
import os.path
from typing import Tuple, Optional


from flask_login import current_user, login_required
import flask_login

from flask import current_app as app
import flask

from openapi_webserver.database import db, User, OrganizationTranslation, ExistingRole, ExistingRoleTranslation, AllowedRoleForUser,TitleTranslation,TitleIsAllowedToDoMakeOthersTrustee,Organization
import json
import openapi_webserver.log as log
from openapi_webserver.utility import get_function_name, checkKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc
import re

def create_error_response(code: int, message: str) -> dict:
    return {'code': code, 'message': message }



def show_organizations(locale: Optional[str]):
    with app.app_context():
        all_org = db.session.query(OrganizationTranslation).filter_by(locale=locale).all()
        org_list=[]
        for org in all_org:
            org_list.append({'uid': db.session.query(Organization.uid).filter_by(id=org.organization_id).first()[0],
                             'long-name': org.long_name,
                             'short-name':org.short_name,
                             'locale':org.locale})
    return org_list



def get_all_organizations(locale: Optional[str] = None) ->  Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        log.info(message='#todo')
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

    return {"organization-list": show_organizations(locale or flask.session['current_locale'])},200

def add_organization(body:dict)  ->  Tuple[dict, int]:
  if not current_user.is_authenticated:
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
  if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
    log.info(message='#todo')
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

  #validating json
  if not bool(body):
    return create_error_response(403, 'You did not enter: locale as root key'), 403
  for key , value in body.items():
    if not re.match(r'^[a-z][a-z]$',key):
        return create_error_response(403, 'locale should be lower case with only two char'), 200
    if not checkKey(value,'short-name') or not isinstance(value['short-name'], str):
        return create_error_response(403, 'You did not enter: short-name'), 200
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9]{3}$',value['short-name']):
        return create_error_response(403, 'short-name should be first character is alphabet and 4 digit'), 200
    if not checkKey(value,'long-name') or not isinstance(value['long-name'], str):
        return create_error_response(403, 'You did not enter: long-name'), 200
    if len(value['long-name'].strip()) <= 3:
        return create_error_response(403, 'long-name should be more then three character'), 200

  try:
    unique_short_name = []
    unique_long_name = []
    #check if short name and long name is alredy present
    for key , value in body.items():
        with app.app_context():
            find_short_name = db.session.query(OrganizationTranslation).filter_by(locale=key,short_name=value['short-name']).first()
        if not find_short_name is None:
            return create_error_response(403, 'short-name already present in database. please enter unique short name'), 200

        #check for dublicate short present in same body
        if not value['short-name'] in unique_short_name:
            unique_short_name.append(value['short-name'])
        else:
            return create_error_response(403, 'Same short-name in request body'), 200
        with app.app_context():
            find_long_name = db.session.query(OrganizationTranslation).filter_by(locale=key,long_name=value['long-name']).first()
        if not find_long_name is None:
            return create_error_response(403, 'long-name already present in database. please enter unique long name'), 200

        #check for dublicate long present in same body
        if not value['long-name'] in unique_long_name:
            unique_long_name.append(value['long-name'])
        else:
            return create_error_response(403, 'Same short-name in request body'), 200

    
    #insert into org table
    newOrg = Organization()
    db.session.add(newOrg)
    
    #https://stackoverflow.com/questions/4201455/sqlalchemy-whats-the-difference-between-flush-and-commit
    #session.flush() communicates a series of operations to the database (insert, update, delete).
    # The database maintains them as pending operations in a transaction. The changes aren't persisted
    # permanently to disk, or visible to other transactions until the database receives a COMMIT for
    # the current transaction (which is what session.commit() does).
    # so without db.session.flush() we cant get newOrg.id it throw exception so I have put. 
    db.session.flush()
    
    #insert into org translation table
    for key , value in body.items():
        newOrgTrans = OrganizationTranslation(organization_id = newOrg.id,locale=key,long_name=value['long-name'],short_name=value['short-name'])
        db.session.add(newOrgTrans)

    db.session.commit()
  except IntegrityError as ie:
    db.session.rollback()
    log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  except exc.SQLAlchemyError as e:
    db.session.rollback()
    log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200


  return {'code': 200, 'message': 'Sucessfully add organization',"organization-list": show_organizations(flask.session['current_locale'])}, 200


def remove_organization(body:dict)  ->  Tuple[dict, int]:
  if not current_user.is_authenticated:
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

  if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
    log.info(message='#todo')
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

  try:
    with app.app_context():
        found_org = db.session.query(Organization).filter_by(uid=body['uid']).first()
    if found_org is None:
        return create_error_response(403, 'uid not found. Please enter valid uid.'), 403

    #delete AllowedRoleForUser based on org
    with app.app_context():
        found_role_ids = [r.id for r in db.session.query(ExistingRole.id).filter_by(organization_id=found_org.id).all()]
    for rid in found_role_ids:
        addresses = db.session.query(AllowedRoleForUser).filter(AllowedRoleForUser.existing_role_id == rid).delete(synchronize_session=False)

    #delete User based on org
    n_user = db.session.query(User).filter(User.organization_id == found_org.id).delete(synchronize_session=False)
    
    #delete ExistingRoleTranslation based on org
    for rid in found_role_ids:
        addresses = db.session.query(ExistingRoleTranslation).filter(ExistingRoleTranslation.existing_role_id == rid).delete(synchronize_session=False)
    
    #delete ExistingRole based on org
    addresses = db.session.query(ExistingRole).filter(ExistingRole.organization_id == found_org.id).delete(synchronize_session=False)

    #delete OrganizationTranslation based on org
    addresses = db.session.query(OrganizationTranslation).filter(OrganizationTranslation.organization_id == found_org.id).delete(synchronize_session=False)

    #delete Organization
    addresses = db.session.query(Organization).filter(Organization.id == found_org.id).delete(synchronize_session=False)
    
    db.session.commit()
  except IntegrityError as ie:
    db.session.rollback()
    log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  except exc.SQLAlchemyError as e:
    db.session.rollback()
    log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  return {'code': 200, 'message': 'Sucessfully remove organization',"organization-list": show_organizations(flask.session['current_locale'])}, 200


def edit_organization(body:dict)  ->  Tuple[dict, int]:
  if not current_user.is_authenticated:
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

  if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
    log.info(message='#todo')
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

  #validating json
  if not bool(body) or len (body) < 2:
    return create_error_response(403, 'You did not enter complete json'), 403

  if not checkKey(body,"uid"):
    return create_error_response(403, 'You did not enter uid'), 403

  unique_short_name = []
  unique_long_name = []

  for key , value in body.items():
    if key == "uid":
        continue
    
    if not re.match(r'^[a-z][a-z]$',key):
        return create_error_response(403, 'locale should be lower case with only two char'), 200
    
    if not checkKey(value,'short-name') or not isinstance(value['short-name'], str):
        return create_error_response(403, 'You did not enter: short-name propery'), 200
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9]{3}$',value['short-name']):
        return create_error_response(403, 'short-name should be first character is alphabet and 4 digit'), 200
    
    if not checkKey(value,'long-name') or not isinstance(value['long-name'], str):
        return create_error_response(403, 'You did not enter: long-name propery'), 200
    
    if len(value['long-name'].strip()) <= 3:
        return create_error_response(403, 'long-name should be more then three character'), 200

    #check for dublicate short present in request body
    if not value['short-name'] in unique_short_name:
        unique_short_name.append(value['short-name'])
    else:
        return create_error_response(403, 'Same short-name in request body'), 200

    #check for dublicate long present in request body
    if not value['long-name'] in unique_long_name:
        unique_long_name.append(value['long-name'])
    else:
        return create_error_response(403, 'Same long-name in request body'), 200

  try:
    with app.app_context():
        found_org = db.session.query(Organization).filter_by(uid=body["uid"]).first()

    if found_org is None:
       return create_error_response(403, 'uid not found in database'), 200
   
    for key , value in body.items():
        if key == "uid":
            continue
        found_org_trans = db.session.query(OrganizationTranslation).filter_by(organization_id=found_org.id,locale=key).first()

        if found_org_trans == None:
            #org translation not present in DB needs to insert 
            newOrgTrans = OrganizationTranslation(organization_id = found_org.id,locale=key,long_name=value['long-name'],short_name=value['short-name'])
            db.session.add(newOrgTrans)
        else:
            #org translation is present in DB there needs to update
            addresses = db.session.query(OrganizationTranslation).filter(OrganizationTranslation.id == found_org_trans.id).update({"long_name": value['long-name'],"short_name": value['short-name']})
    
    db.session.commit()
  except IntegrityError as ie:
    db.session.rollback()
    log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  except exc.SQLAlchemyError as e:
    db.session.rollback()
    log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  return {'code': 200, 'message': 'Sucessfully edit organization',"organization-list": show_organizations(flask.session['current_locale'])}, 200
