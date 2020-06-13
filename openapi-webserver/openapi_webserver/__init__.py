# Copyright (C) 2020, Sardoodledom (github1@lotkit.org)
# All rights reserved.
#
# Although you can see the source code, it is not free and is
# protected by copyright. If you are interested in using it, please
# contact us at: github1@lotkit.org

import os.path
import sys
import logging
import sqlite3
import sqlalchemy

import connexion

#https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/#factories-extensions
from openapi_webserver.database import db, get_title_id_of_uid as db_get_title_id_of_uid
from openapi_webserver.session import sess
from openapi_webserver.login import login_manager


#todo: does this interfere with the SQLALCHEMY_TRACK_MODIFICATIONS = False below?
#todo: test this!
@sqlalchemy.event.listens_for(sqlalchemy.engine.Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        #print('****** encoding=UTF-8 && foreign_keys=ON ***************')
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA encoding='UTF-8';")
        cursor.execute("PRAGMA foreign_keys=ON;")

        # give SQLite more time to get DB lock if database is locked by another process
        cursor.execute("PRAGMA busy_timeout = 5000;")

        cursor.close()

#todo:
# https://stackoverflow.com/questions/58187233/is-it-possible-to-disallow-unknown-query-parameters-in-an-openapi-v3-spec
# https://stackoverflow.com/questions/56314204/how-to-return-flask-sqlalchemy-error-details
# understand transactions: https://stackoverflow.com/questions/19904176/transactions-and-sqlalchemy

def create_app():

    #Intialize custom logging
    log_formatter = logging.Formatter("%(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout) # sys.stderr
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Create the Connexion application instance
    connex_app = connexion.FlaskApp(__name__, specification_dir='openapi/')
    connex_app.add_api('spec.yaml')

    # Get the underlying Flask app instance
    app = connex_app.app

    app.config.from_mapping(
        # Do not set DEBUG, TESTING, or FLASK_ENV here or in any config.
        # Do use environment variables, if you want to set this!
        # see:
        # https://flask.palletsprojects.com/en/1.1.x/config/#environment-and-debug-features says:
        # The ENV and DEBUG config values are special because they may
        # behave inconsistently if changed after the app has begun setting
        # up. In order to set the environment and debug mode reliably,
        # Flask uses environment variables.
        # [...]
        # Using the environment variables as described above is
        # recommended. While it is possible to set ENV and DEBUG in your
        # config or code, this is strongly discouraged. They can’t be read
        # early by the flask command, and some systems or extensions may
        # have already configured themselves based on a previous value.


        # will log the queries executed and the time.
        # good for debugging if set to: True
        SQLALCHEMY_ECHO = False,

        # turning off the SQLAlchemy event system, which is on by default. The
        # event system generates events useful in event-driven programs but
        # adds significant overhead.
        # https://github.com/pallets/flask-sqlalchemy/issues/351
        # https://stackoverflow.com/questions/33738467/how-do-i-know-if-i-can-disable-sqlalchemy-track-modifications/33790196#33790196
        # https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#configuration-keys
        #todo: does this interfere with the above _set_sqlite_pragma ?
        #todo: test this!
        SQLALCHEMY_TRACK_MODIFICATIONS = False,

        # app.root_path is the absolute path to the root directory containing your app code.
        # app.instance_path is the absolute path to the instance folder.
        # os.path.dirname(app.instance_path) is the directory above the
        # instance folder. During development, this is next to or the same as
        # the root path, depending on your project layout.

        SESSION_TYPE = 'filesystem',
        SESSION_PERMANENT = False,
        SESSION_COOKIE_NAME = 'SID',
        SESSION_FILE_DIR = os.path.join(app.instance_path, 'session_cookies'),

        # make sure that we NEVER commit on teardown
        # (default is False anyway, but I want to document this)
        # https://stackoverflow.com/questions/33284334/how-to-make-flask-sqlalchemy-automatically-rollback-the-session-if-an-exception#comment82097629_33284980
        # https://github.com/mitsuhiko/flask-sqlalchemy/blob/f465142ea1643b4f0fe50540780ef9a6bf2c7e53/flask_sqlalchemy/__init__.py#L803
        # We have to commit by our own!
        # On teardown_appcontext calls self.session.remove() anyway,
        # so when I am corrent, we do not need a rollback in our code,
        # but we want to be sure!
        SQLALCHEMY_COMMIT_ON_TEARDOWN = False,

        # Our returned DICTs should be sent as utf-8 JSON:
        # I want to see this: '"surname": "Müller"'
        # Instead of this: '"surname": "M\u00fcller"'
        JSON_AS_ASCII = False,

        MY_LOG_FILENAME = os.path.join(app.instance_path, 'application.log'),
        MY_DEFAULT_LOCALE = 'en',
        MY_SCHEMA_NAME = 'schema-sqlite3-with-some-examples.sql',
        MY_DATABASE_NAME = 'webserver.db',
        MY_WEBAREA_CONFIG_DIR = os.path.join(app.instance_path, 'webarea-config')
    )

    # override current applications vars or add new by
    # optional application.conf in instance directory.
    # Format is: <variable> = <value>
    # e.g: DEBUG = False
    app.config.from_pyfile(os.path.join(app.instance_path, 'application.conf'), silent=True)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # now instance folder exists: add logging into log file
    app.config['MY_LOG_FILENAME']
    log_file_handler = logging.FileHandler(app.config['MY_LOG_FILENAME'])
    log_file_handler.setFormatter(log_formatter)
    root_logger.addHandler(log_file_handler)

    # ensure the MY_WEBAREA_CONFIG_DIR folder exists
    os.makedirs(app.config['MY_WEBAREA_CONFIG_DIR'], exist_ok=True)

    app.config['MY_DATABASE_PATH'] = os.path.join(app.instance_path, app.config['MY_DATABASE_NAME'])
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['MY_DATABASE_PATH']

    if not os.path.isfile(app.config['MY_DATABASE_PATH']):
        with sqlite3.connect(app.config['MY_DATABASE_PATH']) as db_temp:
            with app.open_resource(app.config['MY_SCHEMA_NAME']) as f:
                db_temp.executescript(f.read().decode('utf8'))

    db.init_app(app)
    sess.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        app.config['MY_AUTO_SUPERUSER_TITLE_ID'] = db_get_title_id_of_uid('title-superuser')
        app.config['MY_AUTO_TRUSTEE_TITLE_ID'] = db_get_title_id_of_uid('title-trustee')


    return connex_app
