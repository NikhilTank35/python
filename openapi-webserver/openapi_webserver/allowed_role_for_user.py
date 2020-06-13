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

from openapi_webserver.database import db, User, OrganizationTranslation, ExistingRole, ExistingRoleTranslation, AllowedRoleForUser, TitleTranslation, TitleIsAllowedToDoMakeOthersTrustee, Organization, Title
import json
import openapi_webserver.log as log
from openapi_webserver.utility import get_function_name, checkKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc
import re


def create_error_response(code: int, message: str) -> dict:
    return {'code': code, 'message': message}


def show_allowed_role_for_user() -> dict:
    allowed_role_for_user_list = []
    for allowed_role_for_user in db.session.query(AllowedRoleForUser).all():
        allowed_role_for_user_list.append({'id': allowed_role_for_user.id,
                          'login-name': db.session.query(User.login_name).filter_by(id=allowed_role_for_user.user_id).first()[0],
                          'existing-role-uid': db.session.query(ExistingRole.uid).filter_by(id=allowed_role_for_user.existing_role_id).first()[0]
                         })
    return allowed_role_for_user_list

def get_all_allowed_roles_for_user() ->  Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        log.info(message='#todo')
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    return { "get-all-allowed-roles-for-user-list" : show_allowed_role_for_user()},200


def add_allowed_role_for_user(body:dict) ->  Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        log.info(message='#todo')
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    try:
        #check if login-name is present in User table
        with app.app_context():
            found_user = db.session.query(User).filter_by(login_name=body["login-name"]).first()
        
        if found_user is None:
            return create_error_response(403, 'login-name not present in db'), 403
        #check if existing-role-uid is present in ExistingRole table
        with app.app_context():
            found_existing_role = db.session.query(ExistingRole).filter_by(uid=body["existing-role-uid"]).first()
        
        if found_existing_role is None:
            return create_error_response(403, 'existing-role-uid not present in db'), 403 
        
        #check if user_id and existing_role_id already present AllowedRoleForUser or not
        with app.app_context():
            found_existing_role_for_user = db.session.query(AllowedRoleForUser).filter_by(user_id=found_user.id,existing_role_id=found_existing_role.id).first()
        
        if not found_existing_role_for_user is None:
            return create_error_response(403, 'record is already present in db'), 403
        
        #insert into AllowedRoleForUser
        new_allowed_role_for_user = AllowedRoleForUser(user_id=found_user.id,existing_role_id=found_existing_role.id)
        db.session.add(new_allowed_role_for_user)
        
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    return {'code': 200, 'message': 'Sucessfully add allowed role for user.' ,"get-all-allowed-roles-for-user-list" : show_allowed_role_for_user()}, 200

def remove_allowed_role_for_user(body:dict) ->  Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        log.info(message='#todo')
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    try:
        #check if login-name is present in User table
        with app.app_context():
            found_user = db.session.query(User).filter_by(login_name=body["login-name"]).first()
        
        if found_user is None:
            return create_error_response(403, 'login-name not present in db'), 403
          
        #check if existing-role-uid is present in ExistingRole table
        with app.app_context():
            found_existing_role = db.session.query(ExistingRole).filter_by(uid=body["existing-role-uid"]).first()
        
        if found_existing_role is None:
            return create_error_response(403, 'existing-role-uid not present in db'), 403 
        
        #check if user_id and existing_role_id already present AllowedRoleForUser or not
        with app.app_context():
            found_existing_role_for_user = db.session.query(AllowedRoleForUser).filter_by(user_id=found_user.id,existing_role_id=found_existing_role.id).first()
        
        if found_existing_role_for_user is None:
            return create_error_response(403, 'record is not present in db'), 403
        
        #delete AllowedRoleForUser
        addresses = db.session.query(AllowedRoleForUser).filter(AllowedRoleForUser.id == found_existing_role_for_user.id).delete(synchronize_session=False)
        
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    return {'code': 200, 'message': 'Sucessfully remove allowed role for user.' ,"get-all-allowed-roles-for-user-list" : show_allowed_role_for_user()}, 200
