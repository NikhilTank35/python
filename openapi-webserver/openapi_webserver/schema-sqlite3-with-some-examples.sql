/*
# Copyright (C) 2020, Sardoodledom (github1@lotkit.org)
# All rights reserved.
#
# Although you can see the source code, it is not free and is
# protected by copyright. If you are interested in using it, please
# contact us at: github1@lotkit.org

  Hope this works.
  Looks complicated but in real we only have:
  CREATE TABLE organization ();
  CREATE TABLE title (); -- e.g. 'manager' or 'user'
  CREATE TABLE title_is_allowed_to_do_everything (); -- for checking if the given title is allowed to do everything (== superuser)
  CREATE TABLE title_is_allowed_to_do_make_others_trustee (); -- for checking if the given title is allowed to make others a trustee
  CREATE TABLE title_is_allowed_to_do_everything_on_organization_webservers (); -- for checking if the given title is allowed to make changes to each organization webservers
  CREATE TABLE existing_role (); -- combines 'title' and 'organization' and create what we call a "role"
  CREATE TABLE user (); -- the user
  CREATE TABLE allowed_role_for_user (); -- into what roles a user can switch?
  OK, plus a few translation-tables, because we have to support multiple languages (currently only 'en' and 'de')
  A user is at every time in exact one 'role'. (If the logs in he is in 'user of his organization' (default_role_id) If applicable / allowed he can switch into another 'role'.
  Every output is done in JSON and contains biunique codes. 0 for OK, and biunique numbers for the problems.
  My first idea was to manage all the translations in one table,
  but it gets somehow confusing and I'm also afraid of duplicates (e.g. The german 'Leiter' can be 'Manager' or 'Gerät' oder 'Leiter in der Physik/Strom').
  Old/First idea:
  CREATE TABLE translation (
  id INTEGER NOT NULL PRIMARY KEY
  );
  CREATE TABLE translation_entry (
  id INTEGER NOT NULL PRIMARY KEY,
  translation_id INTEGER NOT NULL,
  locale VARCHAR(2) NOT NULL, -- correct way is to use a number, but thats overdesigned :-)
  field_text TEXT NOT NULL,
  annotation TEXT NOT NULL DEFAULT "",
  UNIQUE(translation_id, locale),
  FOREIGN KEY(translation_id) REFERENCES translation(id)
  );
  Therefore there is now a translation table for each table where this is needed. (These aren't that many in our situation.)
  Yes that almost doubles the number of tables, but it is much easier to understand and 'cleaner' (at least for me).
Be aware that we have UTF-8-content and need foreign_keys=ON;!
  see https://stackoverflow.com/questions/2614984/sqlite-sqlalchemy-how-to-enforce-foreign-keys
 */

PRAGMA encoding='UTF-8';

PRAGMA foreign_keys=ON;


CREATE TABLE organization (
  id INTEGER NOT NULL PRIMARY KEY,
  uid TEXT NOT NULL UNIQUE DEFAULT ('org-' || lower(hex(randomblob(2)))),
  created_at DATETIME NOT NULL DEFAULT (DATETIME('now')) -- in UTC
);
-- Error: column uid is not unique



CREATE TABLE organization_translation (
  id INTEGER NOT NULL PRIMARY KEY,
  organization_id INTEGER NOT NULL,
  locale VARCHAR(2) NOT NULL, -- correct way is to use a number, but thats overdesigned :-)
  long_name TEXT NOT NULL,
  short_name TEXT NOT NULL,
  annotation TEXT NOT NULL DEFAULT "",
  UNIQUE(locale, organization_id),
  UNIQUE(locale, long_name), -- in our use case this is UNIQUE!
  UNIQUE(locale, short_name), -- in our use case this is UNIQUE!
  UNIQUE(locale, long_name, short_name),
  FOREIGN KEY(organization_id) REFERENCES organization(id)
);

INSERT INTO organization (uid) VALUES('org-star');
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'en', '*', '*', 'just a star (marker for "everything")');
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'de', '*', '*', 'einfacher Stern (Kennzeichnung für "Alles")');

INSERT INTO organization (uid) VALUES('org-empty');
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'en', '', '', 'just an empty string');
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'de', '', '', 'leerer Text');

INSERT INTO organization (id) VALUES(NULL);
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'en', 'Long Name of Organization A', 'orgA', '');
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'de', 'Langname der Organization A', 'orgA', '');

INSERT INTO organization (id) VALUES(NULL);
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'en', 'Long Name of Organization B', 'orgB', '');
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'de', 'Langname der Organization B', 'orgB', '');

INSERT INTO organization (id) VALUES(NULL);
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'en', 'Long Name of Organization C', 'orgC', '');
INSERT INTO organization_translation VALUES(NULL, (SELECT rowid FROM organization ORDER BY ROWID DESC LIMIT 1), 'de', 'Langname der Organization C', 'orgC', '');



CREATE TABLE title (
  id INTEGER NOT NULL PRIMARY KEY,
  uid TEXT NOT NULL UNIQUE DEFAULT ('title-' || lower(hex(randomblob(2)))),
  created_at DATETIME NOT NULL DEFAULT (DATETIME('now')) -- in UTC
);

CREATE TABLE title_translation (
  id INTEGER NOT NULL PRIMARY KEY,
  title_id INTEGER NOT NULL,
  locale VARCHAR(2) NOT NULL, -- correct way is to use a number, but thats overdesigned :-)
  description TEXT NOT NULL,
  annotation TEXT NOT NULL DEFAULT "",
  UNIQUE(locale, title_id),
  UNIQUE(locale, description),
  FOREIGN KEY(title_id) REFERENCES title(id)
);

INSERT INTO title (uid) VALUES('title-superuser');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'en', 'superuser', '');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'de', 'Poweruser', '');

INSERT INTO title (uid) VALUES('title-manager');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'en', 'manager', '');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'de', 'Manager', '');

INSERT INTO title (uid) VALUES('title-deputy_manager');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'en', 'deputy_manager', '');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'de', 'stellvertretender Manager', '');

INSERT INTO title (uid) VALUES('title-trustee');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'en', 'trustee', '');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'de', 'Webserverbeauftrager', '');

INSERT INTO title (uid) VALUES('title-user');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'en', 'user', '');
INSERT INTO title_translation VALUES(NULL, (SELECT rowid FROM title ORDER BY ROWID DESC LIMIT 1), 'de', 'User', '');



CREATE TABLE title_is_allowed_to_do_everything (
  id INTEGER NOT NULL PRIMARY KEY,
  title_id INTEGER NOT NULL UNIQUE,
  annotation TEXT NOT NULL DEFAULT "",
  created_at DATETIME NOT NULL DEFAULT (DATETIME('now')) -- in UTC
);
INSERT INTO title_is_allowed_to_do_everything VALUES(NULL, (SELECT id FROM title WHERE uid='title-superuser'), '', DATETIME('now')); -- superuser is allowed to do everything


CREATE TABLE title_is_allowed_to_do_make_others_trustee (
  id INTEGER NOT NULL PRIMARY KEY,
  title_id INTEGER NOT NULL UNIQUE,
  annotation TEXT NOT NULL DEFAULT "",
  created_at DATETIME NOT NULL DEFAULT (DATETIME('now')) -- in UTC
);
INSERT INTO title_is_allowed_to_do_make_others_trustee VALUES(NULL, (SELECT id FROM title WHERE uid='title-manager'), '', DATETIME('now'));
INSERT INTO title_is_allowed_to_do_make_others_trustee VALUES(NULL, (SELECT id FROM title WHERE uid='title-deputy_manager'), '', DATETIME('now'));


CREATE TABLE title_is_allowed_to_do_everything_on_organization_webservers (
  id INTEGER NOT NULL PRIMARY KEY,
  title_id INTEGER NOT NULL UNIQUE,
  annotation TEXT NOT NULL DEFAULT "",
  created_at DATETIME NOT NULL DEFAULT (DATETIME('now')) -- in UTC
);
INSERT INTO title_is_allowed_to_do_everything_on_organization_webservers VALUES(NULL, (SELECT id FROM title WHERE uid='title-manager'), '', DATETIME('now'));
INSERT INTO title_is_allowed_to_do_everything_on_organization_webservers VALUES(NULL, (SELECT id FROM title WHERE uid='title-deputy_manager'), '', DATETIME('now'));
INSERT INTO title_is_allowed_to_do_everything_on_organization_webservers VALUES(NULL, (SELECT id FROM title WHERE uid='title-trustee'), '', DATETIME('now'));



CREATE TABLE existing_role (
  id INTEGER NOT NULL PRIMARY KEY,
  uid TEXT NOT NULL UNIQUE DEFAULT ('role-' || lower(hex(randomblob(2)))),
  title_id INTEGER NOT NULL,
  organization_id INTEGER NOT NULL,
  created_at DATETIME NOT NULL DEFAULT (DATETIME('now')), -- in UTC
  UNIQUE(title_id, organization_id),
  FOREIGN KEY(title_id) REFERENCES title(id),
  FOREIGN KEY(organization_id) REFERENCES organization(id)
);

CREATE TABLE existing_role_translation (
  id INTEGER NOT NULL PRIMARY KEY,
  existing_role_id INTEGER NOT NULL,
  locale VARCHAR(2) NOT NULL, -- correct way is to use a number, but thats overdesigned :-)
  description TEXT NOT NULL,
  annotation TEXT NOT NULL DEFAULT "",
  UNIQUE(existing_role_id, locale),
  UNIQUE(existing_role_id, locale, description),
  FOREIGN KEY(existing_role_id) REFERENCES existing_role(id)
);

INSERT INTO existing_role (uid, title_id, organization_id) VALUES(
  'role-superuser',
  (SELECT id FROM title WHERE uid='title-superuser'),
  (SELECT id FROM organization WHERE uid='org-star')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Superuser of the whole System', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'Poweruser des Gesamtsystems', '');


INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-user'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgA' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Standard User of Organisation A', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'User der Organisation A', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-manager'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgA' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Manager of Organisation A', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'Manager der Organisation A', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-deputy_manager'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgA' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Deputy Manager of Organisation A', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'stellvertretender Manager der Organisation A', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-trustee'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgA' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Trustee of Organisation A', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'Webserverbeauftragter der Organisation A', '');


INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-user'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgB' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Standard User of Organisation B', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'User der Organisation B', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-manager'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgB' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Manager of Organisation B', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'Manager der Organisation B', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-deputy_manager'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgB' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Deputy Manager of Organisation B', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'stellvertretender Manager der Organisation B', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-trustee'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgB' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Trustee of Organisation B', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'Webserverbeauftragter der Organisation B', '');


INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-user'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Standard User of Organisation C', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'User der Organisation C', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-manager'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Manager of Organisation C', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'Manager der Organisation C', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-deputy_manager'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Deputy Manager of Organisation C', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'stellvertretender Manager der Organisation C', '');

INSERT INTO existing_role (title_id, organization_id) VALUES(
  (SELECT id FROM title WHERE uid='title-trustee'),
  (SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en')
);
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'en', 'Trustee of Organisation C', '');
INSERT INTO existing_role_translation VALUES(NULL, (SELECT rowid FROM existing_role ORDER BY ROWID DESC LIMIT 1), 'de', 'Webserverbeauftragter der Organisation C', '');

CREATE TABLE user (
  id INTEGER NOT NULL PRIMARY KEY,
  login_name TEXT NOT NULL UNIQUE, -- all lowercase
  email TEXT NOT NULL UNIQUE, -- all lowercase
  is_enabled BOOLEAN NOT NULL, -- 0: user cannot login; 1: user can login
  gender VARCHAR(1) NOT NULL, -- u: unknown; m: male; f: female; d: divers/other
  given_name TEXT NOT NULL,
  surname TEXT NOT NULL,
  password TEXT NOT NULL,
  organization_id INTEGER NOT NULL,
  default_role_id INTEGER NOT NULL,
  default_locale INTEGER NOT NULL, -- correct way is to use a number, but thats overdesigned :-)
  annotation TEXT NOT NULL DEFAULT "",
  created_at DATETIME NOT NULL DEFAULT (DATETIME('now')), -- in UTC
  FOREIGN KEY(organization_id) REFERENCES organization(id),
  FOREIGN KEY(default_role_id) REFERENCES existing_role(id)
);

CREATE TABLE allowed_role_for_user (
  id INTEGER NOT NULL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  existing_role_id INTEGER NOT NULL,
  FOREIGN KEY(user_id) REFERENCES user(id),
  FOREIGN KEY(existing_role_id) REFERENCES existing_role(id),
  UNIQUE(user_id, existing_role_id)
);


/* Just a friendly remainder, because I forget this every time:
   This does NOT work:
   INSERT INTO user VALUES(1, 'user0', 'test@example.com', 1, 'm', 'John', 'Doe', 'pass', 1000, 1, 'en', '');
   Error: table user has 13 columns but 12 values were supplied
   INSERT INTO user VALUES(1, 'user0', 'test@example.com', 1, 'm', 'John', 'Doe', 'pass', 1000, 1, 'en', '', NULL);
   Error: NOT NULL constraint failed: user.created_at
   This works:
   INSERT INTO user(id, login_name, email, is_enabled, gender, given_name, surname, password, organization_id, default_role_id, default_locale)
   VALUES(1,'user0', 'test@example.com', 1, 'm', 'John', 'Doe', 'pass', 1000, 1, 'en');
   this works, too:
   INSERT INTO user VALUES(1,'user0', 'test@example.com', 1, 'm', 'John', 'Doe', 'pass', 1000, 1, 'en', '', DATETIME('now'));
   to receive the real date/time:
   created_at is in UTC!
   sqlite> SELECT created_at from user;
   2020-04-27 12:45:10
   sqlite>
   sqlite> SELECT datetime(created_at, 'localtime') as local_time from user;
   2020-04-27 14:45:10
   sqlite>
   sqlite> SELECT datetime(created_at||"+06:00") as local_time from user;
   2020-04-27 06:45:10
   sqlite>
   sqlite> SELECT datetime(created_at||"-06:00") as local_time from user;
   2020-04-27 18:45:10
 */


-- user0
INSERT INTO user VALUES(NULL, 'user0', 'test@example.com', 1, 'm', 'John', 'Doe',
                        '$6$rounds=656000$HX/JGIhJRVssW/Ld$w9HeBQJPdeDn7EnQWOezY7vZbJjj0PiPRiVYXsSKIqGO7msmyKik7tvV1ms6niPzYTc2zZOmUqtWIUM7bB.V10', -- passlib.hash.sha512_crypt.hash('password123')
                        (SELECT organization_id FROM organization_translation WHERE short_name='orgA' AND locale='en'),
                        (SELECT id FROM existing_role
                          WHERE
                             organization_id=(SELECT organization_id FROM organization_translation WHERE short_name='orgA' AND locale='en')
                            AND
                             title_id=(SELECT title_id FROM title_translation WHERE description='user' AND locale='en')),
                        'en',
                        '',
                         DATETIME('now'));

-- user0 can become superuser, manager of orgB, and is user of orgA

-- user0 can be in role 'user of orgA' (default)
INSERT INTO allowed_role_for_user VALUES (NULL, (SELECT id FROM user WHERE login_name='user0'),
                                          (SELECT id FROM existing_role
                                            WHERE
                                               organization_id=(SELECT organization_id FROM organization_translation WHERE short_name='orgA' AND locale='en')
                                              AND
                                               title_id=(SELECT title_id FROM title_translation WHERE description='user' AND locale='en'))
                                               );

-- user0 can be in role 'superuser'
INSERT INTO allowed_role_for_user VALUES (NULL, (SELECT id FROM user WHERE login_name='user0'),
                                          (SELECT id FROM existing_role
                                            WHERE
                                               organization_id=(SELECT organization_id FROM organization_translation WHERE short_name='*' AND locale='en')
                                              AND
                                               title_id=(SELECT title_id FROM title_translation WHERE description='superuser' AND locale='en'))
                                               );

-- user0 can be in role 'manager of orgB'
INSERT INTO allowed_role_for_user VALUES (NULL, (SELECT id FROM user WHERE login_name='user0'),
                                          (SELECT id FROM existing_role
                                            WHERE
                                               organization_id=(SELECT organization_id FROM organization_translation WHERE short_name='orgB' AND locale='en')
                                              AND
                                               title_id=(SELECT title_id FROM title_translation WHERE description='manager' AND locale='en'))
                                               );




-- user1
INSERT INTO user VALUES(NULL, 'user1', 'check@example.com', 1, 'f', 'Cäcilie', 'Müller',
                        '$6$rounds=656000$SQ4SHsYztO1mzTnC$/IYhi3ZewAU5OlDWrL/RfeJdt3y/AugGKgEqxPkSkTCM5Ec3./1r5k0VwZtSlfhUTzLNFpiyMFL5k70t0Ed8a0', -- passlib.hash.sha512_crypt.hash('password456')
                        (SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en'),
                        (SELECT id FROM existing_role
                          WHERE
                             organization_id=(SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en')
                            AND
                             title_id=(SELECT title_id FROM title_translation WHERE description='user' AND locale='en')),
                        'en',
                        '',
                        DATETIME('now'));


-- user1 can be in role 'user of orgC' (default)
INSERT INTO allowed_role_for_user VALUES (NULL, (SELECT id FROM user WHERE login_name='user1'),
                                          (SELECT id FROM existing_role
                                            WHERE
                                               organization_id=(SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en')
                                              AND
                                               title_id=(SELECT title_id FROM title_translation WHERE description='user' AND locale='en'))
                                               );




INSERT INTO user VALUES(NULL, 'user2', 'check2@example.com', 1, 'f', 'Cäcilie', 'Müller',
                        '$6$rounds=656000$SQ4SHsYztO1mzTnC$/IYhi3ZewAU5OlDWrL/RfeJdt3y/AugGKgEqxPkSkTCM5Ec3./1r5k0VwZtSlfhUTzLNFpiyMFL5k70t0Ed8a0', -- passlib.hash.sha512_crypt.hash('password456')
                        (SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en'),
                        (SELECT id FROM existing_role
                          WHERE
                             organization_id=(SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en')
                            AND
                             title_id=(SELECT title_id FROM title_translation WHERE description='user' AND locale='en')),
                        'en',
                        '',
                        DATETIME('now'));

INSERT INTO user VALUES(NULL, 'user3', 'check3@example.com', 1, 'f', 'Cäcilie', 'Müller',
                        '$6$rounds=656000$SQ4SHsYztO1mzTnC$/IYhi3ZewAU5OlDWrL/RfeJdt3y/AugGKgEqxPkSkTCM5Ec3./1r5k0VwZtSlfhUTzLNFpiyMFL5k70t0Ed8a0', -- passlib.hash.sha512_crypt.hash('password456')
                        (SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en'),
                        (SELECT id FROM existing_role
                          WHERE
                             organization_id=(SELECT organization_id FROM organization_translation WHERE short_name='orgC' AND locale='en')
                            AND
                             title_id=(SELECT title_id FROM title_translation WHERE description='user' AND locale='en')),
                        'en',
                        '',
                        DATETIME('now'));
