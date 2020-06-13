#!/usr/bin/env python3

import requests


# from https://stackoverflow.com/questions/20658572/python-requests-print-entire-http-request-raw/23816211#23816211

def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".
    
    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


req = requests.Request('POST','http://stackoverflow.com',headers={'X-Custom':'Test'},data='a=1&b=2')
prepared = req.prepare()
pretty_print_POST(prepared)

s = requests.Session()
s.send(prepared)
