#!/usr/bin/env python3

import os, sys
path = os.path.dirname(__file__)

import subprocess


code = 0

p = subprocess.Popen(
    [path + "/checker.py"] + sys.argv[1:],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

output, error = p.communicate()
output = output.decode()
error = error.decode()

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

import json
try:
    x=json.loads(output)

    print(x["public_flag_id"])
    eprint(x["private_content"])

    sys.exit(p.returncode)
except json.decoder.JSONDecodeError:
    eprint(output)
    sys.exit(p.returncode)