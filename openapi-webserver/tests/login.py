#!/usr/bin/env python3

import requests


url = 'http://localhost:5000/login'
headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
json_str='{"user":"user0", "password":"admin"}'

#import json
#json_obj= {"user":"user0", "password":"admin"}
#r = requests.post(url, data=json.dumps(json_obj), headers=headers)


r = requests.post(url, data=json_str, headers=headers)
print(r.status_code)
#[print(key, value) for key, value in r.headers]
for key, value in r.headers.items():
    print(key + ': ' + value)
print (r.text)
