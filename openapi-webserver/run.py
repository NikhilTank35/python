#!/usr/bin/env python3

# Copyright (C) 2020, Sardoodledom (github1@lotkit.org)
# All rights reserved.
#
# Although you can see the source code, it is not free and is
# protected by copyright. If you are interested in using it, please
# contact us at: github1@lotkit.org

import os
import openapi_webserver

# start application
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    connexion_app = openapi_webserver.create_app()
    connexion_app.run(host='127.0.0.1', port=port)
