# Copyright (C) 2020, Sardoodledom (github1@lotkit.org)
# All rights reserved.
#
# Although you can see the source code, it is not free and is
# protected by copyright. If you are interested in using it, please
# contact us at: github1@lotkit.org

import flask_login

# todo?
# https://flask-login.readthedocs.io/en/latest/#localization
# By default, the LoginManager uses flash to display messages when a
# user is required to log in. These messages are in English. If you
# require localization, set the localize_callback attribute of
# LoginManager to a function to be called with these messages before
# they’re sent to flash, e.g. gettext. This function will be called
# with the message and its return value will be sent to flash instead.


login_manager = flask_login.LoginManager()

