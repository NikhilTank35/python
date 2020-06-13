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
import passlib.hash
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


def show_users() -> dict:
    user_list = []
    for user in db.session.query(User).all():
        user_list.append({'login-name': user.login_name,
                          'email': user.email,
                          'is_enabled': user.is_enabled,
                          'gender': user.gender,
                          'name': user.given_name,
                          'surname': user.surname,
                          'organization-uid': db.session.query(Organization.uid).filter_by(id=user.organization_id).first()[0],
                          'default-role-uid': db.session.query(ExistingRole.uid).filter_by(id=user.default_role_id).first()[0],
                          'default-locale': user.default_locale,
                          'created-at': user.created_at
                        })
    return user_list

def get_all_users() ->  Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        log.info(message='#todo')
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    return { "existing-users-list" : show_users()},200


def edit_user(body:dict) ->  Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        log.info(message='#todo')
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    #check if login-name is present or not
    with app.app_context():  
        found_login_name = db.session.query(User).filter_by(login_name=body["login-name"]).first()
    
    if found_login_name is None: 
        return create_error_response(403, 'login-name is not presernt in database'), 200
    
    #check if only login-name entered
    parameter_list = ["email",
                      "is_enabled",
                      "gender",
                      "name",
                      "surname",
                      "password",
                      "organization-uid",
                      "default-role-uid",
                      "default-locale"]
    
    one_of_parameter_is_given = False
    for key , value in body.items():
        if key == "login-name":
            continue
        if key in parameter_list:
            one_of_parameter_is_given = True
            break

    if one_of_parameter_is_given == False:
        return create_error_response(403, 'You did not enter edit parameters'), 200

    update_user_dict = {}
    
    try:
        #check if email present or not
        if checkKey(body,'email'):
            
            #check if email and login-name same as record then ignore this
            with app.app_context():  
                found_email_login_same = db.session.query(User).filter_by(email=body["email"],login_name=body["login-name"]).first()
            
            #if email is entered new
            if found_email_login_same is None:    
                #check if email is taken by other user
                with app.app_context():  
                    found_email = db.session.query(User).filter_by(email=body["email"]).first()
                
                if not found_email is None:
                    return create_error_response(403, 'email is taken by other user'), 200
                
                update_user_dict.update({"email":body["email"]})
        
        
        #check if is_enabled present or not
        if checkKey(body,'is_enabled'):     
            update_user_dict.update({"is_enabled":body["is_enabled"]})
            
        #check if gender present or not
        if checkKey(body,'gender'):     
            update_user_dict.update({"gender":body["gender"]})
            
        #check if gender present or not
        if checkKey(body,'gender'):     
            update_user_dict.update({"gender":body["gender"]})
        
        #check if surname present or not
        if checkKey(body,'surname'):     
            update_user_dict.update({"surname":body["surname"]})
        
        #check if password present or not
        if checkKey(body,'password'):     
            update_user_dict.update({"password":passlib.hash.sha512_crypt.hash(body["password"])})

        #check if organization-uid present or not
        if checkKey(body,'organization-uid'):
            #check if organization-uid is present in db
            with app.app_context(): 
                found_org = db.session.query(Organization).filter_by(uid=body["organization-uid"]).first()
            print(found_org)
            if found_org is None:
                return create_error_response(403, 'organization-uid not present in db'), 200
            
            update_user_dict.update({"organization_id":found_org.id})
        
        
        #check if default-role-uid present or not
        if checkKey(body,'default-role-uid'):
            
            #check if default-role-uid is present in db
            with app.app_context():  
                found_default_role = db.session.query(ExistingRole).filter_by(uid=body["default-role-uid"]).first()

            if found_default_role is None:
                return create_error_response(403, 'default-role-uid not present in db'), 200
            
            update_user_dict.update({"default_role_id":found_default_role.id})
        
        #check if locale present or not
        if checkKey(body,'default-locale'):     
            update_user_dict.update({"default_locale":body["default-locale"]})
            
        
        #update the user
        addresses = db.session.query(User).filter(User.login_name == body["login-name"]).update(update_user_dict)
        
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    return {'code': 200, 'message': 'Sucessfully edit user.',"existing-users-list":  show_users()}, 200


def remove_user(body:dict) ->  Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        log.info(message='#todo')
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    try:
        #check if user present in user table or not
        with app.app_context():  
            found_user = db.session.query(User).filter_by(login_name=body["login-name"]).first()

        if found_user is None:
            return create_error_response(403, 'login-name not found in database'), 200

        #delete AllowedRoleForUser based on that login-name
        n_allowed_role_user = db.session.query(AllowedRoleForUser).filter(AllowedRoleForUser.user_id == found_user.id).delete(synchronize_session=False)

        #delete User based on login-name
        n_user = db.session.query(User).filter(User.id == found_user.id).delete(synchronize_session=False)
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    return {'code': 200, 'message': 'Sucessfully remove user.',"existing-users-list":  show_users()}, 200

def add_user(body:dict) ->  Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    
    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        log.info(message='#todo')
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

    try:    
        #check if login-name is already presnet or not
        with app.app_context():  
            found_login_name = db.session.query(User).filter_by(login_name=body["login-name"]).first()

        if not found_login_name is None:
            return create_error_response(403, 'login-name is already present in database'), 200

        #check if email is already presnet or not
        with app.app_context():  
            found_email = db.session.query(User).filter_by(email=body["email"]).first()

        if not found_email is None:
            return create_error_response(403, 'email is already present in database'), 200

        #check if organization-uid is already presnet or not
        with app.app_context():  
            found_organization = db.session.query(Organization).filter_by(uid=body["organization-uid"]).first()

        if found_organization is None:
            return create_error_response(403, 'organization-uid is not found in database'), 200

        #check if default-role-uid is already presnet or not
        with app.app_context():  
            found_role = db.session.query(ExistingRole).filter_by(uid=body["default-role-uid"]).first()

        if found_role is None:
            return create_error_response(403, 'default-role-uid is not found in database'), 200

        #insert into User
        new_user = User(login_name=body["login-name"],
                        email=body["email"],
                        is_enabled=body["is_enabled"],
                        gender=body["gender"],
                        given_name=body["name"],
                        surname=body["surname"],
                        password=passlib.hash.sha512_crypt.hash(body["password"]),
                        organization_id=found_organization.id,
                        default_role_id=found_role.id,
                        default_locale=body["default-locale"]
                        )
        db.session.add(new_user)
          
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    return {'code': 200, 'message': 'Sucessfully add user.' ,"existing-users-list" : show_users()}, 200

