# -*- coding: UTF-8 -*-
#! python3

"""
    Usage from the repo root folder:

    ```python
    python -m unittest tests.test_export_docx
    ```
"""

# #############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import json
from os import environ, path
from tempfile import mkstemp
import unittest

# 3rd party
from docxtpl import DocxTemplate
from isogeo_pysdk import Metadata

# target
from modules import Isogeo2docx

# #############################################################################
# ######## Globals #################
# ##################################


# #############################################################################
# ########## Classes ###############
# ##################################


class TestExportDocx(unittest.TestCase):
    """Test export to Microsoft Word DOCX."""

    def setUp(self):
        """Executed before each test."""
        # API response samples
        self.search_all_includes = path.normpath(
            r"tests/fixtures/api_search_complete.json"
        )
        # template
        self.word_template = path.normpath(r"tests/fixtures/template_Isogeo.docx")

        # target class instanciation
        self.to_docx = Isogeo2docx()

    def tearDown(self):
        """Executed after each test."""
        pass

    # -- Export ---------------------------------------------------------------
    def test_metadata_export(self):
        """Test search results export"""
        # temp output file
        # out_docx = mkstemp(prefix="i2o_test_docx_")
        # load tags fixtures
        with open(self.search_all_includes, "r") as f:
            search = json.loads(f.read())
        # load template
        tpl = DocxTemplate(self.word_template)
        # run
        for md in search.get("results")[:20]:
            metadata = Metadata.clean_attributes(md)
            # output path
            out_docx = mkstemp(prefix="i2o_test_docx_")
            out_docx_path = out_docx[1] + ".docx"
            # templating
            tpl = DocxTemplate(self.word_template)
            self.to_docx.md2docx(tpl, metadata)
            # save
            tpl.save(out_docx_path)
            del tpl


# #############################################################################
# ##### Stand alone program ########
# ##################################
if __name__ == "__main__":
    unittest.main()
