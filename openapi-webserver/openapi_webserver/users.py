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

from openapi_webserver.database import db, User, OrganizationTranslation, ExistingRole, ExistingRoleTranslation, AllowedRoleForUser,TitleTranslation,TitleIsAllowedToDoMakeOthersTrustee,Organization
import json
import openapi_webserver.log as log
from openapi_webserver.utility import get_function_name, checkKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy import exc

def create_error_response(code: int, message: str) -> dict:
    return {'code': code, 'message': message }


def login(body: dict) -> Tuple[dict, int]:
    log.debug(action='enter', request_body=body)

    # https://stackoverflow.com/a/19533025
    # First of all, is_anonymous() and is_authenticated() are each other's
    # inverse. You could define one as the negation of the other, if you
    # want.
    # You can use these two methods to determine if a user is logged in.
    # When nobody is logged in Flask-Login's current_user is set to an
    # AnonymousUser object. This object responds to is_authenticated() and
    # is_active() with False and to is_anonymous() with True.
    # The is_active() method has another important use. Instead of always
    # returning True like I proposed in the tutorial, you can make it
    # return False for banned or deactivated users and those users will
    # not be allowed to login.
    if current_user.is_authenticated:
        return create_error_response(500, "You are logged in! Log out first and after this come back!"), 400

    locale_to_use = None

    if 'locale' in body:
        locale_to_use = body['locale']

    found_user = None

    # valid input is using 'user' or 'email'
    if 'user' in body:
        with app.app_context():
            found_user = db.session.query(User).filter_by(login_name=body['user']).first()
    elif 'email' in body:
        with app.app_context():
            found_user = db.session.query(User).filter_by(email=body['email']).first()
    else:
        # todo log this! This can't happen!
        # todo for much later: use locale_to_use or (if not set) app.config['MY_DEFAULT_LOCALE'] for message?!
        log.info(message="No 'user' or 'email' given in request! This cannot happen!", action="will return 403 (500)")
        return create_error_response(500, 'An internal program error has happen. But maybe you have sent invalid parameters!'), 403

    if found_user is None:
        # no user of this name or email found
        # todo log this
        if 'user' in body:
            what='login_name=' + body['user']
        else:
            what='email=' + body['email']
            log.info(message="No user in DB found for '" + what + "' found.", action="will return 403 (403)")
        if 'user' in body:
            # todo for much later: use locale_to_use or (if not set) app.config['MY_DEFAULT_LOCALE'] for message?!
            return create_error_response(403, "User and/or password is wrong or User does not exists or User is not allowed to login"), 403
        else:
            return create_error_response(403, "Email and/or password is wrong or Email does not exists or User with that Email is not allowed to login"), 403

    # now compare if given password is correct
    if not passlib.hash.sha512_crypt.verify(body['password'], found_user.password):
        log.info(message="Password given by user does not match the one in DB.", action="will return 403 (403)")
        if 'user' in body:
            return create_error_response(403, "User and/or password is wrong or User does not exists or User is not allowed to login"), 403
        else:
            return create_error_response(403, "Email and/or password is wrong or Email does not exists or User with that Email is not allowed to login"), 403

    # user/email matches password -> login user
    flask_login.login_user(found_user)

    # store the current role of the user inside the cookie
    flask.session['current_role_id'] = found_user.default_role_id

    # later we need to check permissions. To make this faster we store some role info in the cookie.
    #todo: why does thos work without 'with app.app_context():'??
    role_info = db.session.query(ExistingRole).filter_by(id=found_user.default_role_id).first()
    flask.session['current_title_id'] = role_info.title_id
    flask.session['current_organization_id'] = role_info.organization_id

    # store the current locale of the user inside the cookie
    flask.session['current_locale'] = locale_to_use or found_user.default_locale

    if locale_to_use is None:
        locale_to_use = found_user.default_locale

    log.info(message="User logged in.", action="will return 200 (200)")
    return {'code': 200, 'message': 'User logged in.',
            'user': get_info_from_user(found_user, flask.session['current_locale'],
                                       flask.session['current_title_id'] == app.config['MY_AUTO_SUPERUSER_TITLE_ID'])}, 200




#https://docs.python.org/3/library/typing.html#typing.Optional
# Note that this is not the same concept as an optional argument,
# which is one that has a default. An optional argument with a default
# does not require the Optional qualifier on its type annotation just
# because it is optional. For example:
# def foo(arg: int = 0) -> None:
#    ...
# On the other hand, if an explicit value of None is allowed, the use
# of Optional is appropriate, whether the argument is optional or
# not. For example:
# def foo(arg: Optional[int] = None) -> None:
def get_info_from_user(user: User, locale: Optional[str] = None, show_hidden_info: Optional[bool] = False, show_current_session_info: Optional[bool] = True) -> dict:
    if locale is None:
        locale = app.config['MY_DEFAULT_LOCALE']

    user_dict = {}
    for attr in ['login_name', 'email', 'gender', 'given_name', 'surname', 'default_locale']:
        user_dict[attr] = user.__dict__[attr]

    with app.app_context():
        org_info = db.session.query(OrganizationTranslation).filter_by(organization_id=user.organization_id,locale=locale).first()
        role_info = db.session.query(ExistingRoleTranslation).filter_by(existing_role_id=user.default_role_id,locale=locale).first()

    user_dict['organization_long_name'] = org_info.long_name
    user_dict['organization_short_name'] = org_info.short_name
    user_dict['default_role'] = role_info.description

    allowed_role_infos = get_infolist_of_allowed_roles_for_user(user, locale, show_hidden_info)

    user_dict['allowed_roles'] = allowed_role_infos

    if show_hidden_info:
        for attr in ['id', 'is_enabled', 'annotation', 'created_at']:
            user_dict[attr] = user.__dict__[attr]

    if show_current_session_info:
        user_dict['current_locale'] = flask.session['current_locale']

        current_role = {}
        with app.app_context():
            role = db.session.query(ExistingRole).filter_by(id=flask.session['current_role_id']).first()
            role_info = db.session.query(ExistingRoleTranslation).filter_by(existing_role_id=flask.session['current_role_id'], locale=locale).first()

        current_role = {
            'name': role_info.description,
            'uid': role.uid
        }

        if show_hidden_info:
            for attr in ['id', 'created_at']: # todo  'annotation',   is_enabled?
                current_role[attr] = role.__dict__[attr]

        user_dict['current_role'] = current_role

    return user_dict

def get_infolist_of_allowed_roles_for_user(user: User, locale: str, show_hidden_info: Optional[bool] = False) -> dict:
    with app.app_context():
        #roles = db.session.query(AllowedRoleForUser.existing_role_id).filter_by(user_id=user.id).all()
        #roles = db.session.query(AllowedRoleForUser).with_entities(AllowedRoleForUser.existing_role_id).filter_by(user_id=user.id).all()
        # todo do it in one sql command (JOIN)
        #allowed_role_ids = [r.existing_role_id for r in db.session.query(AllowedRoleForUser.existing_role_id).filter_by(user_id=user.id).all()]
        allowed_roles = db.session.query(AllowedRoleForUser).filter_by(user_id=user.id).all()
        allowed_role_infos = []
        for allowed_role in allowed_roles:
            role = db.session.query(ExistingRole).filter_by(id=allowed_role.existing_role_id).first()
            role_info = db.session.query(ExistingRoleTranslation).filter_by(existing_role_id=allowed_role.existing_role_id,locale=locale).first()

            new_allowed_role_info = {'uid': role.uid,
                                     'name': role_info.description}
            if show_hidden_info:
                for attr in ['id']: # todo: add 'annotation' to schema! 'created_at' also?
                    new_allowed_role_info[attr] = allowed_role.__dict__[attr]

            allowed_role_infos.append(new_allowed_role_info)

    return allowed_role_infos


#Using @login_required here is a stupid idea:
#@login_required
#def logout() -> Tuple[dict, int]:
# flask_login.logout_user()
# return {'code': 200, 'message': 'User has been logged out.'}, 200
#
# If the user sends a cookie field with 'SID=I-do-not-exists-or-I-am-no-longer-valid'
# flask_login will reject this request by
# HTTP/1.0 401 UNAUTHORIZED
#{
#  "detail": "The server could not verify that you are authorized to access the URL requested. You either supplied the wrong credentials (e.g. a bad password), or your browser doesn't understand how to supply the credentials required.",
#  "status": 401,
#  "title": "Unauthorized",
#  "type": "about:blank"
#}
# that's bad!
# So we have to test it by ourself!

def logout() -> Tuple[dict, int]:
    if current_user.is_authenticated:
        flask_login.logout_user()
        return {'code': 200, 'message': 'User has been logged out.'}, 200

    #todo:
    # check if user has given a cookie
    # if yes, remove this cookie (by setting it to expired)
    return {'code': 401, 'message': 'You are not logged in!'}, 401



def get_user_info_without_username(locale: Optional[str] = None) -> Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403
    return {'code': 200, 'message': 'User info.',
            'user': get_info_from_user(current_user, locale or flask.session['current_locale'],
                                       flask.session['current_title_id'] == app.config['MY_AUTO_SUPERUSER_TITLE_ID'])}, 200


def get_user_info(username: str, locale: Optional[str] = None) -> Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

    if current_user.login_name == username:
        return {'code': 200, 'message': 'User info.',
                'user': get_info_from_user(current_user, locale or flask.session['current_locale'],
                                           flask.session['current_title_id'] == app.config['MY_AUTO_SUPERUSER_TITLE_ID'])}, 200

    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        return create_error_response(403, 'You are not allowed to ask info about a different user!'), 403

    with app.app_context():
        found_user = db.session.query(User).filter_by(login_name=username).first()

    if found_user is None:
        # no user of this name found
        return create_error_response(404, "No user with that name found in DB!"), 200

    return {'code': 200, 'message': 'User info.',
            'user': get_info_from_user(found_user, locale or flask.session['current_locale'], True, False)}, 200


def list_roles_i_could_switch_to(locale: Optional[str] = None) -> Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

    allowed_role_infos = get_infolist_of_allowed_roles_for_user(current_user, locale or flask.session['current_locale'],
                                                                flask.session['current_title_id'] == app.config['MY_AUTO_SUPERUSER_TITLE_ID'])

    return {'code': 200, 'message': 'Sucessfully get information.','data': allowed_role_infos}, 200


def switch_to_role(role_uid: str, locale: Optional[str] = None) -> Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

    # check if current user is allowed to switch into the role
    with app.app_context():
        role = db.session.query(ExistingRole).filter_by(uid=role_uid).first()

    if role is None:
        log.info(message="Specified role uid '{0}' does not exists".format(role_uid))
        return {'code': 404, 'message': 'Role does not exists or you are not allowed to switch to it!'}, 200

    if flask.session['current_role_id'] == role.id:
        log.info(todo='toto')
        return {'code': 406, 'message': 'Cannot switch into the specified role, because you are already in that role!'}, 200

    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']: # superuser is allowed to do everything, so we do not need to test this for him
        allowed_role = db.session.query(AllowedRoleForUser).filter_by(user_id=current_user.id, existing_role_id=role.id).first()
        if allowed_role is None:
            log.info(todo='toto')
            return {'code': 404, 'message': 'Role does not exists or you are not allowed to switch to it!'}, 200

    # OK user is allowed to switch into specified role

    # todo make this a function which also logs this role change!
    # store the current role of the user inside the cookie
    flask.session['current_role_id'] = role.id

    # later we need to check permissions. To make this faster we store some role info in the cookie.
    flask.session['current_title_id'] = role.title_id
    flask.session['current_organization_id'] = role.organization_id

    return {'code': 200, 'message': 'Role switched successfully.',
            'user': get_info_from_user(current_user, locale or flask.session['current_locale'],
                                       flask.session['current_title_id'] == app.config['MY_AUTO_SUPERUSER_TITLE_ID'])}, 200


def is_this_title_allowed_to_make_users_trustee(title_id: int):
    with app.app_context():
        allowed = db.session.query(TitleIsAllowedToDoMakeOthersTrustee).filter_by(title_id=title_id).first() # TODO is COUNT faster?
    return (allowed is not None)


def make_user_a_trustee_of_organization(username: str, organization_uid: str, locale: Optional[str] = None) -> Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

    with app.app_context():
        found_user = db.session.query(User).filter_by(login_name=username).first()
        if found_user is None:
            log.info(message='#user not found')
            return create_error_response(404, 'User or Organization does not exists or your role does not allowd the disired operation!'), 404

        found_org = db.session.query(Organization).filter_by(uid=organization_uid).first()
        if found_org is None:
            log.info(message='#org not found')
            return create_error_response(404, 'User or Organization does not exists or your role does not allowd the disired operation!'), 404

    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        # check if user allowed to do this
        # first his role must be in a title which allows this
        if not is_this_title_allowed_to_make_users_trustee(flask.session['current_title_id']):
            log.info(message='#title does not allowed todo')
            return create_error_response(404, 'User or Organization does not exists or your role does not allowd the disired operation!'), 404
        # second his role must be in the org...
        if found_org.organization_id != flask.session['current_organization_id']:
            log.info(message='#org is not yours')
            return create_error_response(404, 'User or Organization does not exists or your role does not allowd the disired operation!'), 404

    #check if role 'trustee for org' exists
    with app.app_context():
        found_trustee_existing_role = db.session.query(ExistingRole).filter_by(title_id=app.config['MY_AUTO_TRUSTEE_TITLE_ID'],organization_id=found_org.id).first()
    if found_trustee_existing_role is None:
        return create_error_response(404, "Given organization have no trustee role"), 200

    #check for if user is already in trustee role for that org
    with app.app_context():
        found_allowed_role_for_user = db.session.query(AllowedRoleForUser).filter_by(user_id=found_user.id,existing_role_id=found_trustee_existing_role.id).first() # todo or is count/existst better/faster?

    if found_allowed_role_for_user is not None:
        return create_error_response(404, "User is already a trustee of that organization"), 200

    try:
        newAllowedRoleForUser = AllowedRoleForUser(user_id = found_user.id,
                                                   existing_role_id = found_trustee_existing_role.id)
        db.session.add(newAllowedRoleForUser)
        # todo needed? db.session.flush()
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        log.info(message=str(e),error="SQLAlchemyError has happen" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200

    return {'code': 200, 'message': 'Sucessfully make as trustee.',
            'login_name': get_info_from_user(found_user,
                                             locale or flask.session['current_locale'],
                                             flask.session['current_title_id'] == app.config['MY_AUTO_SUPERUSER_TITLE_ID'],
                                             False)}, 200



def remove_user_from_being_a_trustee_of_organization(username: str, organization_uid: str, locale: Optional[str] = None) -> Tuple[dict, int]:
    if not current_user.is_authenticated:
        return create_error_response(403, 'Resource does not exists or you are not allowed to access it!'), 403

    with app.app_context():
        found_user = db.session.query(User).filter_by(login_name=username).first()
        if found_user is None:
            log.info(message='#user not found')
            return create_error_response(404, 'User or Organization does not exists or your role does not allowd the disired operation!'), 404

        found_org = db.session.query(Organization).filter_by(uid=organization_uid).first()
        if found_org is None:
            log.info(message='#org not found')
            return create_error_response(404, 'User or Organization does not exists or your role does not allowd the disired operation!'), 404

    if flask.session['current_title_id'] != app.config['MY_AUTO_SUPERUSER_TITLE_ID']:
        # check if user allowed to do this
        # first his role must be in a title which allows this
        if not is_this_title_allowed_to_make_users_trustee(flask.session['current_title_id']):
            log.info(message='#title does not allowed todo')
            return create_error_response(404, 'User or Organization does not exists or your role does not allowd the disired operation!'), 404
        # second his role must be in the org...
        if found_org.organization_id != flask.session['current_organization_id']:
            log.info(message='#org is not yours')
            return create_error_response(404, 'User or Organization does not exists or your role does not allowd the disired operation!'), 404

    #check if role 'trustee for org' exists
    with app.app_context():
        found_trustee_existing_role = db.session.query(ExistingRole).filter_by(title_id=app.config['MY_AUTO_TRUSTEE_TITLE_ID'],organization_id=found_org.id).first()
    if found_trustee_existing_role is None:
        return create_error_response(404, "Given organization have no trustee role"), 200

    #check for if user is already in trustee role for that org
    with app.app_context():
        found_allowed_role_for_user = db.session.query(AllowedRoleForUser).filter_by(user_id=found_user.id,existing_role_id=found_trustee_existing_role.id).first() # todo or is count/existst better/faster?

    if found_allowed_role_for_user is None:
        return create_error_response(404, "User is not a trustee of that organization"), 200

    log.info(id=found_allowed_role_for_user.id)

    # todo no rollback needed here right? It is only one operation....
    # todo: and: in case db.session.rollback() is needed: must this be inside app.app_context()?
    try:
        with app.app_context():
            addresses = db.session.query(AllowedRoleForUser).filter(AllowedRoleForUser.id == found_allowed_role_for_user.id).delete() #synchronize_session=False)
            db.session.commit() # MUST be inside app.app_context(), else it is a noop!
    except IntegrityError as ie:
        db.session.rollback()
        log.info(message=str(ie),error="SQLAlchemy.IntegrityError (constraint violation found) or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        log.info(message=str(e),error="SQLAlchemyError or Database chnages found" , action="will return 403 (403)")
        return create_error_response(403, "Internal Server Error"), 200

    return {'code': 200, 'message': 'Sucessfully remove as trustee',
            'login_name': get_info_from_user(found_user,
                                             locale or flask.session['current_locale'],
                                             flask.session['current_title_id'] == app.config['MY_AUTO_SUPERUSER_TITLE_ID'],
                                             False)}, 200
