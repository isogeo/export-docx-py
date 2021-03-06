# -*- coding: UTF-8 -*-
#! python3

"""
    Usage from the repo root folder:

    ```python
    # for whole test
    python -m unittest tests.test_formatter
    # for specific
    python -m unittest tests.test_formatter.TestFormatter.test_conditions
    ```
"""

# #############################################################################
# ########## Libraries #############
# ##################################
# Standard library
import json
import logging
import unittest
import urllib3
from os import environ
from pathlib import Path
from random import sample
from socket import gethostname
from sys import exit, _getframe
from time import gmtime, strftime

# 3rd party
from dotenv import load_dotenv
from isogeo_pysdk import Isogeo, Metadata, MetadataSearch

# fixtures
from .fixtures.fixture_conditions import fixture_conditions
from .fixtures.fixture_limitations import fixture_limitations
from .fixtures.fixture_specifications import fixture_specifications

# target
from isogeotodocx import Formatter

# #############################################################################
# ######## Globals #################
# ##################################


if Path("dev.env").exists():
    load_dotenv("dev.env", override=True)

# host machine name - used as discriminator
hostname = gethostname()

# #############################################################################
# ########## Helpers ###############
# ##################################


def get_test_marker():
    """Returns the function name"""
    return "TEST_UNIT_IsogeoToDocx - {}".format(_getframe(1).f_code.co_name)


# #############################################################################
# ########## Classes ###############
# ##################################


class TestFormatter(unittest.TestCase):
    """Test formatter of Isogeo API results."""

    # -- Standard methods --------------------------------------------------------
    @classmethod
    def setUpClass(cls):
        """Executed when module is loaded before any test."""
        # checks
        if not environ.get("ISOGEO_API_GROUP_CLIENT_ID") or not environ.get(
            "ISOGEO_API_GROUP_CLIENT_SECRET"
        ):
            logging.critical("No API credentials set as env variables.")
            exit()
        else:
            pass

        # ignore warnings related to the QA self-signed cert
        if environ.get("ISOGEO_PLATFORM").lower() == "qa":
            urllib3.disable_warnings()

        # API connection
        cls.isogeo = Isogeo(
            auth_mode="group",
            client_id=environ.get("ISOGEO_API_GROUP_CLIENT_ID"),
            client_secret=environ.get("ISOGEO_API_GROUP_CLIENT_SECRET"),
            auto_refresh_url="{}/oauth/token".format(environ.get("ISOGEO_ID_URL")),
            platform=environ.get("ISOGEO_PLATFORM", "qa"),
        )
        # getting a token
        cls.isogeo.connect()

        # load fixture search
        search_all_includes = Path("tests/fixtures/api_search_complete.json")
        with search_all_includes.open("r") as f:
            search = json.loads(f.read())
        cls.search = MetadataSearch(**search)

        # module to test
        cls.fmt = Formatter()

    def setUp(self):
        """Executed before each test."""
        # tests stuff
        self.discriminator = "{}_{}".format(
            hostname, strftime("%Y-%m-%d_%H%M%S", gmtime())
        )

    def tearDown(self):
        """Executed after each test."""
        pass

    @classmethod
    def tearDownClass(cls):
        """Executed after the last test."""
        # close sessions
        cls.isogeo.close()

    # -- TESTS ---------------------------------------------------------

    # formatter
    def test_conditions(self):
        """Conditions formatter."""
        # filtered search
        for md in self.search.results:
            metadata = Metadata.clean_attributes(md)
            if metadata.conditions:
                # get conditions reformatted
                conditions_out = self.fmt.conditions(metadata.conditions)
                self.assertIsInstance(conditions_out, tuple)

        # fixtures
        conditions_out = self.fmt.conditions(fixture_conditions)
        self.assertIsInstance(conditions_out, tuple)
        self.assertEqual(len(conditions_out), 6)
        for i in conditions_out:
            self.assertIsInstance(i, dict)
            self.assertIn("description", i)

    def test_limitations(self):
        """Limitations formatter."""
        # filtered search
        for md in self.search.results:
            metadata = Metadata.clean_attributes(md)
            if metadata.limitations:
                # get limitations reformatted
                limitations_out = self.fmt.limitations(metadata.limitations)
                self.assertIsInstance(limitations_out, tuple)

        # fixtures
        limitations_out = self.fmt.limitations(fixture_limitations)
        self.assertIsInstance(limitations_out, tuple)
        self.assertEqual(len(limitations_out), 10)
        for i in limitations_out:
            self.assertIsInstance(i, dict)
            self.assertIn("description", i)

    def test_specifications(self):
        """Specifications formatter."""
        # filtered search
        for md in self.search.results:
            metadata = Metadata.clean_attributes(md)
            if metadata.specifications:
                # get specifications reformatted
                specs_out = self.fmt.specifications(metadata.specifications)
                self.assertIsInstance(specs_out, tuple)
            else:
                specs_no = self.fmt.specifications([])
                self.assertIsInstance(specs_no, tuple)

        # fixtures
        specs_out = self.fmt.specifications(fixture_specifications)
        self.assertIsInstance(specs_out, tuple)
        self.assertEqual(len(specs_out), 2)
        for i in specs_out:
            self.assertIsInstance(i, dict)
            self.assertIn("conformant", i)
            self.assertIn("link", i)
            self.assertIn("name", i)
            self.assertIn("published", i)


# ##############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    unittest.main()
