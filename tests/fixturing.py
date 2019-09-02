# -*- coding: UTF-8 -*-
#! python3

"""
    Retrieve fixtures for unit testing
    
    `python .\tests\fixturing.py`
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import json
import logging
from os import environ, path
from pathlib import Path

# 3rd party
from dotenv import load_dotenv
import urllib3

# Isogeo
from isogeo_pysdk import Isogeo

# #############################################################################
# ######## Globals #################
# ##################################

# env vars
load_dotenv("dev.env", override=True)

# log
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# API access
API_OAUTH_ID = environ.get("ISOGEO_API_GROUP_CLIENT_ID")
API_OAUTH_SECRET = environ.get("ISOGEO_API_GROUP_CLIENT_SECRET")
API_PLATFORM = environ.get("ISOGEO_PLATFORM", "qa")
ISOGEO_FIXTURES_METADATA_COMPLETE = environ.get("ISOGEO_FIXTURES_METADATA_COMPLETE")
ISOGEO_WORKGROUP_TEST_UUID = environ.get("ISOGEO_WORKGROUP_TEST_UUID")

# ignore warnings related to the QA self-signed cert
if API_PLATFORM.lower() == "qa":
    urllib3.disable_warnings()

# #############################################################################
# ########## Fixturing ###############
# ####################################

# required dirs
Path("_logs/").mkdir(exist_ok=True)
Path("_auth/").mkdir(exist_ok=True)

# auth fixture
if not Path("_auth/client_secrets.json").exists():
    # fake dict
    auth_dict = {
        "web": {
            "client_id": API_OAUTH_ID,
            "client_secret": API_OAUTH_SECRET,
            "auth_uri": "{}/oauth/authorize".format(environ.get("ISOGEO_ID_URL")),
            "token_uri": "{}/oauth/token".format(environ.get("ISOGEO_ID_URL")),
        }
    }

    # json dump
    with open("_auth/client_secrets.json", "w") as json_auth:
        json.dump(auth_dict, json_auth)

# instanciating the class
isogeo = Isogeo(
    auth_mode="group",
    client_id=API_OAUTH_ID,
    client_secret=API_OAUTH_SECRET,
    auto_refresh_url="{}/oauth/token".format(environ.get("ISOGEO_ID_URL")),
    platform=API_PLATFORM,
)
isogeo.connect()

# Downloading directly from Isogeo API
BASE_DIR = path.dirname(path.abspath(__file__))

# complete search - only Isogeo Tests
out_search_complete_tests = path.join(
    BASE_DIR, "fixtures", "api_search_complete_tests.json"
)
if not path.isfile(out_search_complete_tests):
    request = isogeo.search(
        query="owner:{}".format(ISOGEO_WORKGROUP_TEST_UUID),
        whole_results=1,
        include="all",
        augment=1,
    )
    with open(out_search_complete_tests, "w") as json_basic:
        json.dump(request, json_basic, sort_keys=True)
else:
    logging.info("JSON already exists. If you want to update it, delete it first.")

# complete search
out_search_complete = path.join(BASE_DIR, "fixtures", "api_search_complete.json")
if not path.isfile(out_search_complete):
    request = isogeo.search(whole_results=1, include="all", augment=1)
    with open(
        path.join(BASE_DIR, "fixtures", "api_search_complete.json"), "w"
    ) as json_basic:
        json.dump(request.to_dict(), json_basic, sort_keys=True)
else:
    logging.info("JSON already exists. If you want to update it, delete it first.")
