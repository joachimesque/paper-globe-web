#!/usr/bin/env python3

"""Downloads and checks external front-end libs

Avoid CDNs for front-end libraries:
https://blog.wesleyac.com/posts/why-not-javascript-cdn
"""

import os
import base64
import hashlib

import requests

# https://www.srihash.org/
libs = [
    (
        "https://unpkg.com/chota@0.8.0/dist/chota.css",
        "chota-0.8.0.css",
        "sha384-rn488xVSy52er61VbV56rSIPTxXtCTcectcsH/0VOC9RwoajWF3O4ukT8bmZVCNy",
    ),
    (
        "https://unpkg.com/@hotwired/stimulus@3.1.0/dist/stimulus.js",
        "stimulus-3.1.0.js",
        "sha384-en9nbjs1h76Rr2aNc1Dbh2PNnRMRalb6SW3XpU3orOcd//1VhS0JI9FsThhPUp45",
    ),
    (
        "https://unpkg.com/@hotwired/turbo@7.1.0/dist/turbo.es2017-esm.js",
        "turbo-7.1.0.js",
        "sha384-IC4O+RUHyaU/tFZasGspkBx4Wy/yQ8LsnSeplkkGO21WQqyuZdGNViPnpzFTzdzb",
    ),
]

EXPORT_DIR = "../vendor/"

for lib in libs:
    destination = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), EXPORT_DIR, lib[1]
    )
    resource_data = requests.get(lib[0]).content

    if len(lib) > 2 and lib[2] != "":
        integrity_checksum = base64.b64encode(
            hashlib.sha384(resource_data).digest()
        ).decode("utf-8")
        if integrity_checksum == lib[2].rsplit("-", maxsplit=1)[-1]:
            print(f"{lib[1]} SRI check OK")
        else:
            raise Exception(f"SRI check failed for {lib[1]}")
    else:
        print(f"Warning: Could not check SRI for {lib[1]}")

    with open(destination, "wb") as file:
        file.write(resource_data)
