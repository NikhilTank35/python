
import sys
import time
import datetime

# todo is there a portable way for this?
# https://docs.python.org/3/library/sys.html#sys._getframe says:
#CPython implementation detail: [...]
#It is not guaranteed to exist in all implementations of Python.
#
# Is this portable? :
#import traceback
#return traceback.extract_stack(None, 2)[0][2]
#
def get_function_name(depth=1):
    """
    :return: name of caller
    """
    return sys._getframe(depth).f_code.co_name


# highly influenced by
# https://stackoverflow.com/questions/43491287/elegant-way-to-check-if-a-nested-key-exists-in-a-dict/43491315#43491315
def keys_exists(element, *keys):
    '''
    Check if *keys (nested) exists in `element` (dict).
    '''
    if not isinstance(element, dict):
        return False
    if len(keys) == 0:
        return False

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True

def checkKey(dict_arg, key): 
    '''
    Check if keys exists in `element` (dict).
    '''
    if not isinstance(dict_arg, dict):
        return False
    if len(dict_arg.keys()) == 0:
        return False
    if key in dict_arg.keys(): 
        return True
    else: 
        return False


def now_str() -> str:
    tz = time.timezone
    tz_str = time.strftime('{0}%H%M'.format('-' if tz<0 else '+'), time.gmtime(abs(tz))) #creates +0130 or -0130
    return datetime.datetime.today().strftime('%Y%m%d-%H%M%S {0}'.format(tz_str))
