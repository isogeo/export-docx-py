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
    """

    def __init__(self, lang="FR", output_type="Excel"):
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
        self.output_type = output_type.lower()
        self.isogeo_tr = IsogeoTranslator(lang).tr

    # ------------ Metadata sections formatter --------------------------------
    def conditions(self, md_conditions: list) -> list:
        """Render input metadata CGUs as a new list.

        :param list md_conditions: input list extracted from an Isogeo metadata
        :rtype: list(dict)
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
        """Render input metadata specifications (conformity + specification) as a new list.

        :param list md_specifications: input dictionary extracted from an Isogeo metadata

        :rtype: list(dict)
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

    # # specifications
    # fixture_specifications = [
    #     {
    #         "conformant": True,
    #         "specification": {
    #             "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
    #             "_tag": "specification:isogeo:1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
    #             "name": "CNIG CC v2014",
    #             "link": "http://cnig.gouv.fr/wp-content/uploads/2014/10/141002_Standard_CNIG_CC_diffusion.pdf",
    #             "published": "2014-10-02T00:00:00",
    #         },
    #     },
    #     {
    #         "conformant": False,
    #         "specification": {
    #             "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m20z",
    #             "_tag": "specification:1a2b3c4d5e6f7g8h9i0j11k12l13m20z:1a2b3c4d5e6f7g8h9i0j11k12l13m20z",
    #             "name": "Spécification - GT",
    #             "link": "https://www.isogeo.com",
    #             "owner": {
    #                 "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m20z",
    #                 "_tag": "owner:1a2b3c4d5e6f7g8h9i0j11k12l13m20z",
    #                 "_created": "2019-01-30T17:39:21.8947459+00:00",
    #                 "_modified": "2019-08-05T13:55:03.9109327+00:00",
    #                 "contact": {
    #                     "_id": "azerty7g8h9i0j11k12l13m20z",
    #                     "_tag": "contact:group:azerty7g8h9i0j11k12l13m20z",
    #                     "_deleted": False,
    #                     "type": "group",
    #                     "name": "Isogeo TEST - SDK Migration",
    #                     "zipCode": "33140",
    #                     "countryCode": "FR",
    #                     "available": False,
    #                 },
    #                 "canCreateMetadata": True,
    #                 "canCreateLegacyServiceLinks": True,
    #                 "areKeywordsRestricted": False,
    #                 "hasCswClient": True,
    #                 "hasScanFme": False,
    #                 "keywordsCasing": "lowercase",
    #                 "metadataLanguage": "es",
    #             },
    #         },
    #     },
    # ]
    # print(formatter.specifications(fixture_specifications))

    # CGUs - Conditions
    fixture_conditions = [
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "description": "**Gras**\n*Italique*\t\n<del>Supprimé</del>\n<cite>Citation</cite>\n\n* Élément 1\n* Élément 2\n\n1. Élément 1\n2. Élément 2\n\n[Foo](http://foo.bar)",
            "license": {
                "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "_tag": "license:isogeo:1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "name": "ODbL 1.0 - Open Database Licence",
                "link": "https://vvlibri.org/fr/licence/odbl-10/legalcode/unofficial",
            },
        },
        {
            "_id": "abc2d5177d284fd5acc18046bb3dc076",
            "description": "Hop hop hop",
            "license": {
                "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "_tag": "license:isogeo:1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "name": "ODbL 1.0 - Open Database Licence",
                "link": "https://vvlibri.org/fr/licence/odbl-10/legalcode/unofficial",
            },
        },
        {"_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n", "description": ""},
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "description": "",
            "license": {
                "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "_tag": "license:1a2b3c4d5e6f7g8h9i0j11k12l13m14n:1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "owner": {
                    "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                    "_tag": "owner:1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                    "_created": "2019-01-30T17:39:21.8947459+00:00",
                    "_modified": "2019-08-05T13:55:03.9109327+00:00",
                    "contact": {
                        "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                        "_tag": "contact:group:1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                        "_deleted": False,
                        "type": "group",
                        "name": "Isogeo TEST - SDK Migration",
                        "zipCode": "33140",
                        "countryCode": "FR",
                        "available": False,
                    },
                    "canCreateMetadata": True,
                    "canCreateLegacyServiceLinks": True,
                    "areKeywordsRestricted": False,
                    "hasCswClient": True,
                    "hasScanFme": False,
                    "keywordsCasing": "lowercase",
                    "metadataLanguage": "es",
                },
                "name": "TEST License",
                "link": "https://www.isogeo;com",
                "content": "**Description**\n\nLicence créée manuellement pour des tests automatiques.",
            },
        },
        {
            "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
            "description": "",
            "license": {
                "_id": "1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "_tag": "license:isogeo:1a2b3c4d5e6f7g8h9i0j11k12l13m14n",
                "name": "Licence ouverte ETALAB 2.0",
                "link": "https://www.etalab.gouv.fr/wp-content/uploads/2017/04/ETALAB-Licence-Ouverte-v2.0.pdf",
            },
        },
    ]
    print(formatter.conditions(fixture_conditions))
