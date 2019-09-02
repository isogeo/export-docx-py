# -*- coding: UTF-8 -*-
#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals

# ----------------------------------------------------------------------------
# Name:         OpenCatalog to Excel
# Purpose:      Get metadatas from an Isogeo OpenCatlog and store it into
#               an Excel workbook.
#
# Author:       Isogeo
#
# Python:       2.7.x
# Created:      14/08/2014
# Updated:      28/01/2016
# ----------------------------------------------------------------------------

# ###########################################################################
# ########## Libraries ##########
# ###############################

# Standard library
from collections import Counter, defaultdict
import logging

# 3rd party library
from openpyxl.chart import BarChart, Reference


# ##############################################################################
# ############ Globals ############
# #################################

# LOG
logger = logging.getLogger("isogeo_to_docx")

# ############################################################################
# ######## Classes ###############
# ################################


class Stats(object):
    """Doc for Isogeo."""

    md_empty_fields = defaultdict(list)
    md_types_repartition = defaultdict(int)
    md_tags_occurences = defaultdict(int)

    def __init__(self, lang=None):
        """Instanciate stats class."""
        # self._ = _
        super(Stats, self).__init__()

    def fillfull(self):
        """Calculate fields fillfull level."""
        return "HOHOHOHO"

    def week_work(self, search_results=list):
        """Return histogram data to represent cataloging activity per week."""
        for md in search_results:
            print(md.get("type", "No md, no type"))

        return "weekly baby!"

    # def type_pie(self, sheet, total=20):
    #     """Return histogram data to represent cataloging activity per week."""
    #     data = (
    #         (_("Type"), _("Count")),
    #         (_("Vector"), self.md_types_repartition.get("vector", 0)),
    #         (_("Raster"), self.md_types_repartition.get("raster", 0)),
    #         (_("Service"), self.md_types_repartition.get("service", 0)),
    #         (_("Resource"), self.md_types_repartition.get("resource", 0)),
    #     )

    #     # write data into worksheet
    #     for row in data:
    #         sheet.append(row)

    #     # Pie chart
    #     pie = PieChart()
    #     labels = Reference(sheet, min_col=1, min_row=2, max_row=5)
    #     data = Reference(sheet, min_col=2, min_row=1, max_row=5)
    #     pie.add_data(data, titles_from_data=True)
    #     pie.set_categories(labels)
    #     pie.title = _("Metadata by types")

    #     # Cut the first slice out of the pie
    #     slice = DataPoint(idx=0, explosion=20)
    #     pie.series[0].data_points = [slice]

    #     return pie

    def keywords_bar(self, sheet, results, total=20):
        """Return histogram data to represent cataloging activity per week."""
        # tags parsing
        li_keywords = []
        li_inspire = []
        for md in results:
            li_keywords.extend(
                (
                    i.get("text")
                    for i in md.get("keywords", [])
                    if i.get("_tag").startswith("keyword:is")
                )
            )
            li_inspire.extend(
                (
                    i.get("text")
                    for i in md.get("keywords", [])
                    if i.get("_tag").startswith("keyword:in")
                )
            )
        keywords = Counter(li_keywords)
        inspire = Counter(li_inspire)

        data_k = [("Keyword", "Count")]
        for k, c in keywords.most_common(50):
            data_k.append((k, c))

        # write data into worksheet
        for row in data_k:
            sheet.append(row)

        bar = BarChart()
        bar.type = "bar"
        bar.style = 10
        bar.title = "Keywords by occurrences"
        bar.y_axis.title = "Occurences"
        bar.x_axis.title = "Keywords"

        data = Reference(sheet, min_col=2, min_row=1, max_row=50, max_col=3)
        cats = Reference(sheet, min_col=1, min_row=2, max_row=50)
        bar.add_data(data, titles_from_data=True)
        bar.set_categories(cats)
        bar.shape = 4

        return bar


# ############################################################################
# ###### Stand alone program ########
# ###################################
if __name__ == "__main__":
    """Standalone execution and tests."""
    from os import environ
    from isogeo_pysdk import Isogeo, __version__ as pysdk_version
    from openpyxl import Workbook

    # API access
    share_id = environ.get("ISOGEO_API_DEV_ID")
    share_token = environ.get("ISOGEO_API_DEV_SECRET")
    isogeo = Isogeo(client_id=share_id, client_secret=share_token)
    bearer = isogeo.connect()

    # search
    search = isogeo.search(bearer, whole_results=0, include=["keywords"])

    # workbook
    wb = Workbook()
    # ws = wb.active

    # this app
    app = Stats()
    # app.week_work(search.get("results"))
    # print(type(app.fillfull()))

    # metadata types
    ws_d = wb.create_sheet(title="Dashboard")
    # # pie = app.type_pie(ws_d,
    #                    search.get('total'))
    # # ws_d.add_chart(pie, "D1")

    bar = app.keywords_bar(ws_d, search.get("results"))
    ws_d.add_chart(bar, "A10")
    # write xlsx
    wb.save("test.xlsx")
