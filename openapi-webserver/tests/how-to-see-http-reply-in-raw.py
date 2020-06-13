#!/usr/bin/env python3


# Python cannot do the same as:
# curl -sS -D - -X POST --header "Content-Type: application/json" --header "Accept: application/json"  -d '{"user":"user0", "password":"admin"}' http://127.0.0.1:5000/login
# ... and show the real reply! (Including status code, the real headers (e.g. if there are double headers, Python only show one, etc...), corrupt header lines, etc....
# see https://stackoverflow.com/questions/55795582/get-http-raw-unparsed-response-in-http-client-or-python-requests
#
# best I found so far is this:


import requests
import logging

from http.client import HTTPConnection

HTTPConnection.debuglevel = 1

logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

url = "https://www.google.de/"

r = requests.get(url, stream=True)

# this print the real raw body (maybe it is compressed/gzip, then you will see binary here)
#print (r.raw.data)

#this prints the boday after e.g. applying 'Content-Encoding'
print (r.content)



