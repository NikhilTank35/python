import json
import multiprocessing
import threading
from openapi_webserver.utility import get_function_name, now_str
from flask_login import current_user
import flask
import logging

def get_json_logline(**kwargs):
    if not 'function' in kwargs:
        kwargs['function'] = get_function_name(2)
    if not 'timestamp' in kwargs:
        kwargs['timestamp'] = now_str()

    # todo? add user and role here instead
    if not 'user' in kwargs:
        if current_user.is_authenticated:
            kwargs['user'] = current_user.login_name
        else:
            kwargs['user'] = ''

    if not 'role' in kwargs:
        if current_user.is_authenticated:
            kwargs['role'] = flask.session['current_role_id']
            #todo
            #flask.session['current_title_id']
            #flask.session['current_organization_id']
        else:
            kwargs['role'] = ''

    # sort kwargs so we always have the same order (it's easier to look at)
    ordered_dict = {}
    sort_list = ('timestamp', 'log_level', 'user', 'role', 'function', 'request_body')
        
    for key in sort_list:
        if key in kwargs:
            ordered_dict[key]=kwargs[key]

    for key, value in kwargs.items():
        if not key in sort_list:
            ordered_dict[key]=value

    ordered_dict['pinfo'] = { 'pid': multiprocessing.current_process().pid,
                              'pname': multiprocessing.current_process().name,
                              'tid': threading.current_thread().ident,
                              'tname': threading.current_thread().name
                          }

    if 'request_body' in ordered_dict and type(ordered_dict['request_body']) is dict and 'password' in ordered_dict['request_body']:
        # there is a 'password' inside request-body. Remove this for logging.
        temp_password = ordered_dict['request_body']['password']
        ordered_dict['request_body']['password'] = '[REMOVED FOR SECURITY]'
        string_to_log = json.dumps(ordered_dict)
        ordered_dict['request_body']['password'] = temp_password
    else:
        string_to_log = json.dumps(ordered_dict)
    return '%s' % ( string_to_log)



def debug(**kwargs):
    kwargs['log_level'] = 'debug'
    return logging.debug(get_json_logline(**kwargs))

def info(**kwargs):
    kwargs['log_level'] = 'info'
    return logging.info(get_json_logline(**kwargs))

def warn(**kwargs):
    kwargs['log_level'] = 'warn'
    return logging.warning(get_json_logline(**kwargs))

def warning(**kwargs):
    kwargs['log_level'] = 'warn'
    return logging.warning(get_json_logline(**kwargs))

def error(**kwargs):
    kwargs['log_level'] = 'error'
    return logging.error(get_json_logline(**kwargs))
