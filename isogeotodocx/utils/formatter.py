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
    Conformity,
    Directive,
    IsogeoTranslator,
    IsogeoUtils,
    Limitation,
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
    """

    def __init__(self, lang="FR"):
        # locale
        self.lang = lang.lower()
        if lang.lower() == "fr":
            self.dates_fmt = "%d/%m/%Y"
            self.datetimes_fmt = "%A %d %B %Y (%Hh%M)"
            self.locale_fmt = "fr_FR"
        else:
            self.dates_fmt = "%d/%m/%Y"
            self.datetimes_fmt = "%a %d %B %Y (%Hh%M)"
            self.locale_fmt = "uk_UK"

        # store params and imports as attributes
        self.isogeo_tr = IsogeoTranslator(lang).tr

    # ------------ Metadata sections formatter --------------------------------
    def conditions(self, md_conditions: list) -> list:
        """Render input metadata CGUs as a new list.

        :param list md_conditions: input list extracted from an Isogeo metadata

        :rtype: tuple(dict)
        """
        # output list
        conditions_out = []
        for c_in in md_conditions:
            # load condition object
            condition_in = Condition(**c_in)

            # build out dict
            condition = {}

            if condition_in.description and len(condition_in.description):
                condition["description"] = condition_in.description
            else:
                condition["description"] = self.isogeo_tr("conditions", "noLicense")
            if condition_in.license:
                if condition_in.license.content:
                    condition["description"] += "\n" + condition_in.license.content
                condition["link"] = condition_in.license.link
                condition["name"] = condition_in.license.name

            # add to the final list
            conditions_out.append(condition)

        # return formatted result
        return tuple(conditions_out)

    def limitations(self, md_limitations: list) -> list:
        """Format input metadata limitations as a tuple of 2 tuples of dictionaries, ready to be exported:
        one with limitations related to INSPIRE, one with other limitations.

        :param list md_limitations: input list of metadata limitations

        :rtype: tuple(tuple(dict), tuple(dict))
        """
        limitations_out = []
        for lim_in in md_limitations:
            # load limitation object
            limitation_in = Limitation(**lim_in)

            # build out dict
            limitation_out = {}

            # fill it
            limitation_out["description"] = limitation_in.description
            limitation_out["restriction"] = self.isogeo_tr(
                "restrictions", limitation_in.restriction
            )
            limitation_out["type"] = self.isogeo_tr("limitations", limitation_in.type)

            # split INSPIRE / others
            if limitation_in.directive:
                directive = Directive(**limitation_in.directive)
                limitation_out["directive"] = "{} ({})".format(
                    directive.name, directive.description
                )
            limitations_out.append(limitation_out)

        # return formatted result
        return tuple(limitations_out)

    def specifications(self, md_specifications: list) -> list:
        """Render input metadata specifications (conformity + specification) as a new list.

        :param list md_specifications: input dictionary extracted from an Isogeo metadata

        :rtype: tuple(dict)
        """
        # output list
        specifications_out = []
        for conformity in md_specifications:
            # load conformity object
            conf_in = Conformity(**conformity)
            # build out dict
            spec = {}

            # translate
            if conf_in.conformant is True:
                spec["conformant"] = self.isogeo_tr("quality", "isConform")
            else:
                spec["conformant"] = self.isogeo_tr("quality", "isNotConform")
            spec["name"] = conf_in.specification.name
            spec["link"] = conf_in.specification.link
            # publication date
            if conf_in.specification.published:
                spec["published"] = utils.hlpr_datetimes(
                    conf_in.specification.published
                ).strftime(self.dates_fmt)
            else:
                spec["published"] = ""

            # append
            specifications_out.append(spec)

        # return formatted result
        return tuple(specifications_out)

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

        if not isinstance(invalid_xml, str):
            return invalid_xml

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

    # limitations
    fixture_limitations = [
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "legal",
            "description": "**Gras**\n*Italique*\t\n<del>Supprimé</del>\n<cite>Citation</cite>\n\n* Élément 1\n* Élément 2\n\n1. Élément 1\n2. Élément 2\n\n[Foo](http://foo.bar)",
            "restriction": "license",
            "directive": {
                "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "name": "Pas de restriction d’accès public selon INSPIRE",
                "description": "Aucun des articles de la loi ne peut être invoqué pour justifier d’une restriction d’accès public.",
            },
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "security",
            "description": "**Gras**\n*Italique*\t\n<del>Supprimé</del>\n<cite>Citation</cite>\n\n* Élément 1\n* Élément 2\n\n1. Élément 1\n2. Élément 2\n\n[Foo](http://foo.bar)",
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "legal",
            "description": "",
            "restriction": "other",
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "legal",
            "description": "",
            "restriction": "patentPending",
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "legal",
            "description": "Ceci est un **copyright**",
            "restriction": "copyright",
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "legal",
            "description": "",
            "restriction": "trademark",
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "legal",
            "description": "",
            "restriction": "patent",
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "legal",
            "description": "",
            "restriction": "intellectualPropertyRights",
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "type": "legal",
            "description": "",
            "restriction": "restricted",
        },
    ]
    print(formatter.limitations(fixture_limitations))
