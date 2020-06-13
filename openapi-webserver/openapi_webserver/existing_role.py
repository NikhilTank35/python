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

from openapi_webserver.database import db, User, OrganizationTranslation, ExistingRole, ExistingRoleTranslation, AllowedRoleForUser,TitleTranslation,TitleIsAllowedToDoMakeOthersTrustee,Organization,Title
import json
import openapi_webserver.log as log
from openapi_webserver.utility import get_function_name, checkKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc
import re

def create_error_response(code: int, message: str) -> dict:
     return {'code': code, 'message': message }


def show_existing_roles(locale: Optional[str]):
   all_existing_roles = db.session.query(ExistingRoleTranslation).filter_by(locale=locale).all()
   role_list=[]
   for role in all_existing_roles:
      existing_role_obj = db.session.query(ExistingRole).filter_by(id=role.existing_role_id).first()
      role_list.append({'id' : role.existing_role_id,
                     'uid':existing_role_obj.uid,
                     'title-id': existing_role_obj.title_id,
                     'organization-id':existing_role_obj.organization_id,
                     'created-at':existing_role_obj.created_at,
                     'locale':role.locale,
                     'description':role.description })
   return role_list

def get_all_existing_roles(locale: Optional[str] = None) ->  Tuple[dict, int]:
     if not current_user.is_authenticated:
          return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

     if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
          log.info(message='#todo')
          return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

     return {"existing-roles-list": show_existing_roles(locale or flask.session['current_locale'])},200

def add_existing_role(body:dict)  ->  Tuple[dict, int]:
  if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
  if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
    log.info(message='#todo')
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
  
  #validating json
  if not bool(body) or not len(body) == 3:
    return create_error_response(403, 'You did not enter complete json'), 403

  if not checkKey(body,"translation"):
     return create_error_response(403, 'You did not enter translation'), 403

  if not checkKey(body,"title-uid"):
     return create_error_response(403, 'You did not enter title-uid'), 403

  if not checkKey(body,"organization-uid"):
     return create_error_response(403, 'You did not enter organization-uid.'), 403
  
  if not isinstance(body['title-uid'], str) or not re.match(r'^title\-(\S){4,}$',body['title-uid']):
     return create_error_response(403, 'title-uid should be string with ex. title-g2g2'), 200
  if not isinstance(body['organization-uid'], str) or not re.match(r'^org\-(\S){4}$',body['organization-uid']):
     return create_error_response(403, 'organization-uid should be string with ex. org-g2g2'), 200

  if not isinstance(body['translation'], list) or len(body['translation']) == 0:
     return create_error_response(403, 'translation should be list with length of more then 0'), 200
  
  unique_locale = []  
  unique_description = []
  for r_dict in body['translation']:
     if not isinstance(r_dict, dict) or len(r_dict) != 2 :
        return create_error_response(403, 'inside translation should be multiple dict with each dict length is two'), 200
     if not checkKey(r_dict,'locale') or not isinstance(r_dict['locale'], str):
            return create_error_response(403, 'You did not enter: locale propery'), 200
     if not re.match(r'^[a-z][a-z]$',r_dict['locale']):
        return create_error_response(403, 'locale should be lower case with only two char'), 200
     if not checkKey(r_dict,'description') or not isinstance(r_dict['description'], str):
        return create_error_response(403, 'You did not enter: short-name propery'), 200
     if len(r_dict['description'].strip()) <= 9:
        return create_error_response(403, 'description should be more then nine character'), 200
     
     #check for dublicate locale present in request body
     if not r_dict['locale'] in unique_locale:
        unique_locale.append(r_dict['locale'])
     else:
        return create_error_response(403, 'Same locale in request body'), 200
    
     #check for dublicate description present in request body
     if not r_dict['description'] in unique_description:
        unique_description.append(r_dict['description'])
     else:
        return create_error_response(403, 'Same description in request body'), 200
   
  try:
    #check for existing title uid present or not
    with app.app_context():  
        found_title = db.session.query(Title).filter_by(uid=body["title-uid"]).first()
    
    if found_title is None:
       return create_error_response(403, 'title-uid not found in database'), 200

    #check for organization uid present or not
    with app.app_context():  
        found_organization = db.session.query(Organization).filter_by(uid=body["organization-uid"]).first()
    
    if found_organization is None:
       return create_error_response(403, 'organization-uid not found in database'), 200
  
     #check for existing role table like record is already present or not
    with app.app_context():  
        found_existing_role = db.session.query(ExistingRole).filter_by(title_id=found_title.id,organization_id=found_organization.id).first()
    
    if not found_existing_role is None:
       return create_error_response(403, 'record is already present.'), 200


    #insert into existing role table  
    existing_role = ExistingRole(title_id=found_title.id,organization_id=found_organization.id)
    db.session.add(existing_role)
    db.session.flush()
    #insert into existing role translation
    for r_dict in body['translation']:
       existing_role_trans = ExistingRoleTranslation(existing_role_id=existing_role.id,locale=r_dict['locale'],description=r_dict['description'])
       db.session.add(existing_role_trans)
       
    db.session.commit()   
  except IntegrityError as ie:
    db.session.rollback()
    log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  except exc.SQLAlchemyError as e:
    db.session.rollback()
    log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  return {'code': 200, 'message': 'Sucessfully add existing role',"existing-roles-list": show_existing_roles(flask.session['current_locale'])}, 200


def edit_existing_role(body:dict)  ->  Tuple[dict, int]:
   if not current_user.is_authenticated:
      return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
   if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
      log.info(message='#todo')
      return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
  
   #validating json
   if not bool(body):
      return create_error_response(403, 'You did not enter complete json'), 403

   if not checkKey(body,"uid"):
      return create_error_response(403, 'You did not enter uid'), 403      
   
   if not checkKey(body,"translation") :
      return create_error_response(403, 'You did not enter translation key'), 403
   if not isinstance(body['translation'], list) or len(body['translation']) == 0:
      return create_error_response(403, 'translation should be list with length of more then 0'), 200
   unique_locale = []  
   unique_description = []
   for r_dict in body['translation']:
      if not isinstance(r_dict, dict) or len(r_dict) != 2 :
         return create_error_response(403, 'inside translation should be multiple dict with each dict length is two'), 200
      if not checkKey(r_dict,'locale') or not isinstance(r_dict['locale'], str):
            return create_error_response(403, 'You did not enter: locale propery'), 200
      if not re.match(r'^[a-z][a-z]$',r_dict['locale']):
         return create_error_response(403, 'locale should be lower case with only two char'), 200
      if not checkKey(r_dict,'description') or not isinstance(r_dict['description'], str):
         return create_error_response(403, 'You did not enter: description propery'), 200
      if len(r_dict['description'].strip()) <= 9:
         return create_error_response(403, 'description should be more then nine character'), 200
      #check for dublicate locale present in request body
      if not r_dict['locale'] in unique_locale:
         unique_locale.append(r_dict['locale'])
      else:
         return create_error_response(403, 'Same locale in request body'), 200
      
      #check for dublicate description present in request body
      if not r_dict['description'] in unique_description:
         unique_description.append(r_dict['description'])
      else:
         return create_error_response(403, 'Same description in request body'), 200
   try:
      #check uid present in db or not 
      with app.app_context():  
         found_exist_role = db.session.query(ExistingRole).filter_by(uid=body["uid"]).first()
         
      if found_exist_role is None:
         return create_error_response(403, 'uid is not present in db'), 200
      
      #update or insert locale                 
      for r_dict in body['translation']:
         found_exist_role_trans = db.session.query(ExistingRoleTranslation).filter_by(existing_role_id=found_exist_role.id,locale=r_dict['locale']).first()
         if found_exist_role_trans == None:
            #existing_role translation not present in DB needs to insert 
            newExistingRoleTrans = ExistingRoleTranslation(existing_role_id = found_exist_role.id,locale=r_dict['locale'],description=r_dict['description'])
            db.session.add(newExistingRoleTrans)
         else:
            #existing_role translation is present in DB there needs to update
            addresses = db.session.query(ExistingRoleTranslation).filter(ExistingRoleTranslation.id == found_exist_role_trans.id).update({"locale": r_dict['locale'],"description": r_dict['description']})
      db.session.commit()   
   except IntegrityError as ie:
      db.session.rollback()
      log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
      return create_error_response(403, "Internal Server Error"), 200
   except exc.SQLAlchemyError as e:
      db.session.rollback()
      log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
      return create_error_response(403, "Internal Server Error"), 200
   return {'code': 200, 'message': 'Sucessfully edit existing role',"existing-roles-list": show_existing_roles(flask.session['current_locale'])}, 200
            
def remove_existing_role(body:dict)  ->  Tuple[dict, int]:
  if not current_user.is_authenticated:
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

  if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
    log.info(message='#todo')
    return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

  try:
    with app.app_context():
        found_existing_role = db.session.query(ExistingRole).filter_by(uid=body['uid']).first()
    if found_existing_role is None:
        return create_error_response(403, 'uid not found. Please enter valid uid.'), 403

    #delete ExistingRoleTranslation based on found_existing_role
    n_existing_role_translation = db.session.query(ExistingRoleTranslation).filter(ExistingRoleTranslation.existing_role_id == found_existing_role.id).delete(synchronize_session=False)
    
    #delete allowed role for user
    n_allowed_role_for_user = db.session.query(AllowedRoleForUser).filter(AllowedRoleForUser.existing_role_id == found_existing_role.id).delete(synchronize_session=False)
    
    #delete user based on existingRole 
    n_allowed_role_for_user = db.session.query(User).filter(User.default_role_id == found_existing_role.id).delete(synchronize_session=False)
    
    #delete ExistingRole based on found_existing_role
    addresses = db.session.query(ExistingRole).filter(ExistingRole.id == found_existing_role.id).delete(synchronize_session=False)
    
    db.session.commit()
  except IntegrityError as ie:
    db.session.rollback()
    log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  except exc.SQLAlchemyError as e:
    db.session.rollback()
    log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
    return create_error_response(403, "Internal Server Error"), 200
  return {'code': 200, 'message': 'Sucessfully remove existing role',"existing-roles-list": show_existing_roles(flask.session['current_locale'])}, 200
