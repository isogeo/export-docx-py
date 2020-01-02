# -*- coding: UTF-8 -*-
#! python3

"""
    Retrieve fixtures for unit testing

    python ./tests/fixturing.py
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import csv
import json
import logging
from os import environ
from pathlib import Path
from random import sample

# 3rd party
from dotenv import load_dotenv
import urllib3

# Isogeo
from isogeo_pysdk import Isogeo, Metadata, MetadataSearch

# #############################################################################
# ######## Globals #################
# ##################################

# BASE DIRECTORY - Script is meant to be launched from the root of the repository
BASE_DIR = Path(__file__).parent

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

# -- RETRIEVE ISOGEO SEARCH RESULTS ----------------------------------------------------
logger.info(
    "Connecting to Isogeo API to download search results to be used by the following test."
)

# instanciating the class
isogeo = Isogeo(
    auth_mode="group",
    client_id=API_OAUTH_ID,
    client_secret=API_OAUTH_SECRET,
    auto_refresh_url="{}/oauth/token".format(environ.get("ISOGEO_ID_URL")),
    platform=API_PLATFORM,
)
isogeo.connect()

# complete search - only Isogeo Tests
out_search_complete_tests = BASE_DIR / "fixtures" / "api_search_complete_tests.json"

if not out_search_complete_tests.is_file():
    request = isogeo.search(
        query="owner:{}".format(ISOGEO_WORKGROUP_TEST_UUID),
        whole_results=1,
        include="all",
        augment=1,
    )
    with out_search_complete_tests.open("w") as json_basic:
        json.dump(request.to_dict(), json_basic, sort_keys=True)
else:
    logger.info(
        "JSON already exists at: {}. If you want to update it, delete it first.".format(
            out_search_complete_tests.resolve()
        )
    )

# complete search
out_search_complete = BASE_DIR / "fixtures" / "api_search_complete.json"

if not out_search_complete.is_file():
    request = isogeo.search(whole_results=1, include="all", augment=1)
    with out_search_complete.open("w") as json_basic:
        json.dump(request.to_dict(), json_basic, sort_keys=True)
else:
    logger.info(
        "JSON already exists at: {}. If you want to update it, delete it first.".format(
            out_search_complete.resolve()
        )
    )


# -- BUILD THUMBNAILS TABLE ------------------------------------------------------------
logger.info("Write the thumbnails table to test image insertion into Word export.")

thumbnails_table_out = BASE_DIR / "fixtures" / "thumbnails.csv"

# load previous genereated JSON
with out_search_complete.open("r") as f:
    search = json.loads(f.read())
search = MetadataSearch(**search)

fixtures_images = list(Path(BASE_DIR / "fixtures" / "img").iterdir())

with thumbnails_table_out.open("w", newline="") as csvfile:
    # CSV structure
    csv_headers = ["isogeo_uuid", "isogeo_title_slugged", "img_abs_path"]
    # write headers
    writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
    writer.writeheader()

    # pick random metadata
    metadatas = sample(search.results, len(fixtures_images))

    # parse fixtures images
    for image, md in zip(fixtures_images, metadatas):
        metadata = Metadata.clean_attributes(md)
        writer.writerow(
            {
                "isogeo_uuid": metadata._id,
                "isogeo_title_slugged": metadata.title_or_name(slugged=1),
                "img_abs_path": image.resolve(),
            }
        )

    # force a thumbnail for the fixture metadata
    writer.writerow(
        {
            "isogeo_uuid": environ.get("ISOGEO_FIXTURES_METADATA_COMPLETE"),
            "isogeo_title_slugged": "ISOGEO FIXTURES METADATA COMPLETE",
            "img_abs_path": image.resolve(),
        }
    )

logger.info("{} thumbnails associated with metadatas.".format(len(fixtures_images) + 1))
