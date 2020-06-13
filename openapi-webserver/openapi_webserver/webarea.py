# Copyright (C) 2020, Sardoodledom (github1@lotkit.org)
# All rights reserved.
#
# Although you can see the source code, it is not free and is
# protected by copyright. If you are interested in using it, please
# contact us at: github1@lotkit.org

import errno
import os
import time
import datetime
import threading
import logging
import os.path
import io
from typing import Tuple, Optional

import passlib.hash

from flask_login import current_user, login_required
import flask_login

from flask import current_app as app
import flask

from openapi_webserver.database import db, User, OrganizationTranslation, ExistingRoleTranslation, AllowedRoleForUser
import json
import openapi_webserver.log as log
from openapi_webserver.utility import now_str


#todo not completed: in progress
def create_webarea(body: dict) -> Tuple[dict, int]:
    log.debug(action='enter', request_body=body)

    print('****************************')
    print(body)
    print('****************************')

    #if not current_user.is_authenticated:
    #    return {'code': 403, 'message': 'Resource does not exists or you are not allowed to access it!'}, 403

    # todo check if user is allowed to create a new webserver!

    if 'id' in body:
        # user has explicitly stated which id he wants
        dirname = os.path.join(app.config['MY_WEBAREA_CONFIG_DIR'], str(body['id']))

        try:
            os.mkdir(dirname)
        except OSError as err:
            if err.errno == errno.EEXIST:
                return {'code': 901, 'message': 'ID already in use!'}, 200
            else:
                log.info(action='error', message="os.mkdir('{0}') returned OS error: {1}".format(dirname, err))
                return {'code': 900, 'message': 'Internal error has happen!'}, 200
    else:
        new_id = create_next_free_webarea()
        if new_id < 0:
            log.info(action='error', message="create_next_free_webarea() returned '{0}'".format(new_id))
            return {'code': 900, 'message': 'Internal error has happen!'}, 200
        dirname = os.path.join(app.config['MY_WEBAREA_CONFIG_DIR'], str(new_id))
                    
    # dirname is set here to the correct dir
    # test: I will implement one file for every option. Let me see how far I can go with that...

    print('****************************')
    print(dirname)
    print('****************************')

    create_info = { 'at' : now_str(),
                    'issue' : 'R12345, R9876',
                    'annotation': 'equivalent to abc',
                    'organization_long': 'xÄxx',    
                    'organization_short': 'xßxx',    
                    'role_info': 'zzz'    
    }

    for attr in ['login_name', 'email', 'gender', 'given_name', 'surname']:
        create_info[attr] = attr # todo current_user.__dict__[attr]


    #todo translate    flask.session['current_role_id'] 


    print(create_info)

    write_to_option_file(dirname, 'creation_info', json.dumps(create_info, indent=2, ensure_ascii=False))

    
    # accountable_info = { owner editor admin other }
    

    return {'code': 200, 'message': 'todo'}, 200


def create_next_free_webarea() -> int:
    minimal_webarea_id = 1000
    maximal_webarea_id = 1999

    for id in range(minimal_webarea_id, maximal_webarea_id+1):
        dirname = os.path.join(app.config['MY_WEBAREA_CONFIG_DIR'], str(id))
        if not os.path.exists(dirname):
            try:
                os.mkdir(dirname)
                return id
            except OSError as err:
                if err.errno != errno.EEXIST:
                    log.info(action='error', message="os.mkdir('{0}') returned OS error: {1}".format(dirname, err))
                    return -1
                log.info(action='error', message="No free webarea number found! (Searched from '{0}' up to '{1}'.)".format(minimal_webarea_id, maximal_webarea_id))
                return -1


def secure_write(fd, str):
    byte_string = str.encode('utf-8')
    try:
        len_written = os.write(fd, byte_string)
    except IOError as err:
        # great we do NOT need to handle EINTR by ourself
        # https://docs.python.org/3/library/os.html#os.write
        # Changed in version 3.5: If the system call is interrupted
        # and the signal handler does not raise an exception, the
        # function now retries the system call instead of raising an
        # InterruptedError exception (see PEP 475 for the rationale).
        #
        # so an error is an error.
        log.info(action='error', message="os.write('{0}', <byte-string>) returned OS error: {1}".format(fd, err))
        return False

    wanted_to_write_bytes = len(byte_string)
    if (len_written != wanted_to_write_bytes):
        log.info(action='error', message="os.write('{0}', <byte-string>) has written only '{1}' of the needed '{2}' bytes!".format(fd, len_written, wanted_to_write_bytes))
        return False
    
    return True


# I do not want to use real file locking, because this might create too much problems.
# I use the existence of <file>.lock! If I (this process/thread) is able to create it, I have the lock.
# else wait some time until I get it.
# In our case this is OK.
# Warning: This only works, where 'open(filename, O_WRONLY | O_CREAT | O_EXCL)' is C working...
def get_lock_for_filename(filename, max_wait_seconds=10) -> bool:
    lock_filename = filename + '.LOCK'
    end_time = int(time.time()) + max_wait_seconds

    last_err = None
    while (int(time.time()) <= end_time):
        try:
            fd = os.open(lock_filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            ok = secure_write(fd, "{0}\n{1}\n".format(os.getpid(), threading.get_ident()))
            os.close(fd)
            if ok:
                return True
            log.info(action='error', message="secure_write('{0}' ('{1}') returned False".format(fd, lock_filename))
            if not remove_lock_from_filename(filename):
                log.info(action='error', message="remove_lock_from_filename('{0}') returned False".format(filename))
            return False
        except OSError as err:
            if err.errno != errno.EEXIST:
                log.info(action='error', message="os.open('{0}', os.O_WRONLY | os.O_CREAT | os.O_EXCL) returned OS error: {1}".format(lock_filename, err))
                return False
            last_err = err
        time.sleep(0.05) # wait for the other process (who has the lock) to complete

    # no success: the other process did not complete in max_wait_seconds. Maybe it is gone?
    # todo: should I check this?
    log.info(action='error', message="os.open('{0}', os.O_WRONLY | os.O_CREAT | os.O_EXCL) last returned OS error (after waiting '{1}' seconds): {2}".format(lock_filename, max_wait_seconds, last_err))
    return False


def remove_lock_from_filename(filename):
    lock_filename = filename + '.LOCK'
    try:
        os.remove(lock_filename)
    except OSError as err:
        log.info(action='error', message="os.remove('{0}') returned OS error: {1}".format(lock_filename, err))
        return False

    return True



def write_to_option_file(dir, option, content):
    filename = os.path.join(dir, option)
    if not get_lock_for_filename(filename):
        log.info(action='error', message="get_lock_for_filename('{0}') returned False!".format(filename))
        return False

    filename_new = filename + '.NEW'

    # todo errorhandling
    file = io.open(filename_new, "w", encoding="utf-8") #todo: what does the parameter errors=strict means?
    file.write(content)
    file.close()
    
    # archive file if it already exists
    if os.path.exists(filename):
        old_dir = os.path.join(dir, 'OLD', str(datetime.date.today().year))
        new_name = os.path.join(old_dir, option + datetime.datetime.today().strftime('-%Y%m%d-%H%M%S'))
        os.makedirs(old_dir, exist_ok=True) # todo handle error
        os.rename(filename, new_name) # todo handle error

    # todo errorhandling
    os.rename(filename_new, filename)

    if not remove_lock_from_filename(filename):
        log.info(action='error', message="remove_lock_from_filename('{0}') returned False!".format(filename))
        return True # yes we return True, coz' the content is written, about the locking problem someone else must have a look

    return True


