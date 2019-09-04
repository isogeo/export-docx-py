# -*- coding: UTF-8 -*-

# ------------------------------------------------------------------------------
# Name:         Isogeo to Microsoft Word 2010
# Purpose:      Get metadatas from an Isogeo share and store it into
#               a Word document for each metadata. It's one of the submodules
#               of isogeo2office (https://github.com/isogeo/isogeo-2-office).
#
# Author:       Julien Moura (@geojulien) for Isogeo
#
# Python:       2.7.x
# Created:      14/08/2014
# Updated:      28/01/2016
# ------------------------------------------------------------------------------

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
import re
from itertools import zip_longest
from xml.sax.saxutils import escape  # '<' -> '&lt;'

# 3rd party library
from isogeo_pysdk import (
    Condition,
    IsogeoTranslator,
    IsogeoUtils,
    License,
    Limitation,
    Specification,
)

# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger("isogeotodocx")  # LOG
utils = IsogeoUtils()

# ##############################################################################
# ########## Classes ###############
# ##################################


class Formatter(object):
    """Metadata formatter to avoid repeat operations on metadata during export in different formats.
    
    :param str lang: selected language
    :param str output_type: name of output type to format for. Defaults to 'Excel'
    :param tuple default_values: values used to replace missing values. Structure:
        
        (
            str_for_missing_strings_and_integers,
            str_for_missing_dates
        )
    """

    def __init__(
        self,
        lang="FR",
        output_type="Excel",
        default_values=("NR", "1970-01-01T00:00:00+00:00"),
    ):
        # locale
        self.lang = lang.lower()
        if lang == "fr":
            self.dates_fmt = "DD/MM/YYYY"
            self.locale_fmt = "fr_FR"
        else:
            self.dates_fmt = "YYYY/MM/DD"
            self.locale_fmt = "uk_UK"

        # store params and imports as attributes
        self.output_type = output_type.lower()
        self.defs = default_values
        self.isogeo_tr = IsogeoTranslator(lang).tr

    # ------------ Metadata sections formatter --------------------------------
    def conditions(self, md_cgus: list) -> list:
        """Render input metadata CGUs as a new list.

        :param dict md_cgus: input dictionary extracted from an Isogeo metadata
        """
        cgus_out = []
        for c_in in md_cgus:
            if not isinstance(c_in, dict):
                logger.error("Condition expects a dict, not '{}'".format(type(c_in)))
                continue
            cgu_out = {}
            # load condition object
            condition_in = Condition(**c_in)
            cgu_out["description"] = condition_in.description
            if isinstance(condition_in.license, License):
                lic = condition_in.license
                cgu_out["name"] = lic.name
                cgu_out["link"] = lic.link
                cgu_out["content"] = lic.content
            else:
                cgu_out["name"] = self.isogeo_tr("conditions", "noLicense")

            # store into the final list
            cgus_out.append(
                "{} {}. {} {}".format(
                    cgu_out.get("name"),
                    cgu_out.get("description", ""),
                    cgu_out.get("content", ""),
                    cgu_out.get("link", ""),
                )
            )
        # return formatted result
        return cgus_out

    def limitations(self, md_limitations: list) -> list:
        """Render input metadata limitations as a new list.

        :param dict md_limitations: input dictionary extracted from an Isogeo metadata
        """
        lims_out = []
        for l_in in md_limitations:
            limitation = {}
            # ensure other fields
            limitation["description"] = l_in.get("description", "")
            limitation["type"] = self.isogeo_tr("limitations", l_in.get("type"))
            # legal type
            if l_in.get("type") == "legal":
                limitation["restriction"] = self.isogeo_tr(
                    "restrictions", l_in.get("restriction")
                )
            else:
                pass
            # INSPIRE precision
            if "directive" in l_in.keys():
                limitation["inspire"] = l_in.get("directive").get("name")

                limitation["content"] = l_in.get("directive").get("description")

            else:
                pass

            # store into the final list
            lims_out.append(
                "{} {}. {} {} {}".format(
                    limitation.get("type"),
                    limitation.get("description", ""),
                    limitation.get("restriction", ""),
                    limitation.get("content", ""),
                    limitation.get("inspire", ""),
                )
            )
        # return formatted result
        return lims_out

    def specifications(self, md_specifications: list) -> list:
        """Render input metadata specifications as a new list.

        :param dict md_specifications: input dictionary extracted from an Isogeo metadata
        """
        specs_out = []
        for s_in in md_specifications:
            spec_in = Specification(**s_in.get("specification"))
            spec_out = {}
            # translate specification conformity
            if s_in.get("conformant"):
                spec_out["conformity"] = self.isogeo_tr("quality", "isConform")
            else:
                spec_out["conformity"] = self.isogeo_tr("quality", "isNotConform")
            # ensure other fields
            spec_out["name"] = spec_in.name
            spec_out["link"] = spec_in.link
            # make data human readable
            if spec_in.published:
                spec_date = utils.hlpr_datetimes(spec_in.published).strftime(
                    self.dates_fmt
                )
            else:
                logger.warning(
                    "Publication date is missing in the specification '{} ({})'".format(
                        spec_in.name, spec_in._tag
                    )
                )
                spec_date = ""
            spec_out["date"] = spec_date
            # store into the final list
            specs_out.append(
                "{} {} {} - {}".format(
                    spec_out.get("name"),
                    spec_out.get("date"),
                    spec_out.get("link"),
                    spec_out.get("conformity"),
                )
            )

        # return formatted result
        return specs_out

    def clean_xml(self, invalid_xml: str, mode: str = "soft", substitute: str = "_"):
        """Clean string of XML invalid characters.

        source: https://stackoverflow.com/a/13322581/2556577

        :param str invalid_xml: xml string to clean
        :param str substitute: character to use for subtistution of special chars
        :param str modeaccents: mode to apply. Available options:

          * soft [default]: remove chars which are not accepted in XML
          * strict: remove additional chars
        """
        if invalid_xml is None:
            return ""
        # assumptions:
        #   doc = *( start_tag / end_tag / text )
        #   start_tag = '<' name *attr [ '/' ] '>'
        #   end_tag = '<' '/' name '>'
        ws = r"[ \t\r\n]*"  # allow ws between any token
        # note: expand if necessary but the stricter the better
        name = "[a-zA-Z]+"
        # note: fragile against missing '"'; no "'"
        attr = '{name} {ws} = {ws} "[^"]*"'
        start_tag = "< {ws} {name} {ws} (?:{attr} {ws})* /? {ws} >"
        end_tag = "{ws}".join(["<", "/", "{name}", ">"])
        tag = "{start_tag} | {end_tag}"

        assert "{{" not in tag
        while "{" in tag:  # unwrap definitions
            tag = tag.format(**vars())

        tag_regex = re.compile("(%s)" % tag, flags=re.VERBOSE)

        # escape &, <, > in the text
        iters = [iter(tag_regex.split(invalid_xml))] * 2
        pairs = zip_longest(*iters, fillvalue="")  # iterate 2 items at a time

        # get the clean version
        clean_version = "".join(escape(text) + tag for text, tag in pairs)
        if mode == "strict":
            clean_version = re.sub(r"<.*?>", substitute, clean_version)
        else:
            pass
        return clean_version


# ###############################################################################
# ###### Stand alone program ########
# ###################################
if __name__ == "__main__":
    """Try me"""
    formatter = Formatter()
