#!/usr/bin/env python

import json
import sys
import os

FILE = "/etc/docker/daemon.json"

def init_harbor_docker(url):
    if os.path.exists(FILE):
        with open(FILE,'r') as f:
            res =json.loads(f.read())
        new_dict = dict({"insecure-registries":[url]})
        res.update(new_dict)
        with open(FILE,'w') as f:
            json.dump(res,f,indent=4)
        print("{} Written to add {}".format(new_dict,FILE))
    else:
        print("{} not Found".format(FILE))
        sys.exit(1)

if __name__ == '__main__':
    url = sys.argv[1]
    init_harbor_docker(url)