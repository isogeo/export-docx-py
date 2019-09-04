# -*- coding: UTF-8 -*-
#! python3

"""
    Get metadatas from Isogeo and dump each into a Word document. 

"""

# ##############################################################################
# ########## Libraries #############
# ##################################

# Standard library
import logging
from datetime import datetime

# 3rd party library
from docxtpl import DocxTemplate, InlineImage, RichText, etree
from isogeo_pysdk import Event, Isogeo, IsogeoTranslator, IsogeoUtils, Metadata, Share

# custom submodules
from isogeotodocx.utils import Formatter

# ##############################################################################
# ############ Globals ############
# #################################

logger = logging.getLogger("isogeo2office")
utils = IsogeoUtils()

# ##############################################################################
# ########## Classes ###############
# ##################################


class Isogeo2docx(object):
    """IsogeoToDocx class.

    :param str lang: selected language for output
    :param str url_base_edit: base url to format edit links (basically app.isogeo.com)
    :param str url_base_view: base url to format view links (basically open.isogeo.com)
    """

    def __init__(
        self,
        lang="FR",
        default_values=("NR", "1970-01-01T00:00:00+00:00"),
        url_base_edit: str = "https://app.Isogeo.com",
        url_base_view: str = "https://open.isogeo.com",
    ):
        """Common variables for Word processing.

        default_values (optional) -- values used to replace missing values.
        Must be a tuple with 2 values structure:
        (
        str_for_missing_strings_and_integers,
        str_for_missing_dates
        )


        """
        super(Isogeo2docx, self).__init__()

        # ------------ VARIABLES ---------------------
        # test variables
        if type(default_values) != tuple:
            raise TypeError(self.__init__.__doc__)
        else:
            pass
        if len(default_values) != 2:
            raise ValueError(self.__init__.__doc__)
        else:
            pass

        # set variables
        self.default_values = default_values

        # LOCALE
        if lang.lower() == "fr":
            self.dates_fmt = "%d/%m/%Y"
            self.datetimes_fmt = "%A %d %B %Y (%Hh%M)"
            self.locale_fmt = "fr_FR"
        else:
            self.dates_fmt = "%d/%m/%Y"
            self.datetimes_fmt = "%a %d %B %Y (%Hh%M)"
            self.locale_fmt = "uk_UK"

        # TRANSLATIONS
        self.isogeo_tr = IsogeoTranslator(lang).tr

        # FORMATTER
        self.fmt = Formatter(output_type="Word")

        # URLS
        utils.app_url = url_base_edit  # APP
        utils.oc_url = url_base_view  # OpenCatalog url

    def md2docx(self, docx_template: DocxTemplate, md: Metadata, share: Share = None):
        """Dump Isogeo metadata into a docx template.

        :param DocxTemplate docx_template: Word template to fill
        :param Metadata metadata: metadata to dumpinto the template
        :param Share share: share in which the metadata is. Used to build the view URL.
        """
        logger.debug(
            "Starting the export into Word .docx of {} ({})".format(
                md.title_or_name(slugged=1), md._id
            )
        )

        # TAGS #
        # extracting & parsing tags
        li_motscles = []
        li_theminspire = []
        srs = ""
        inspire_valid = "Non"
        format_lbl = ""
        fields = ["NR"]

        # looping on tags
        for tag in md.tags.keys():
            # free keywords
            if tag.startswith("keyword:isogeo"):
                li_motscles.append(md.tags.get(tag))
                continue
            else:
                pass
            # INSPIRE themes
            if tag.startswith("keyword:inspire-theme"):
                li_theminspire.append(md.tags.get(tag))
                continue
            else:
                pass
            # coordinate system
            if tag.startswith("coordinate-system"):
                srs = md.tags.get(tag)
                continue
            else:
                pass
            # format pretty print
            if tag.startswith("format"):
                format_lbl = md.tags.get(tag, self.missing_values())
                continue
            else:
                pass
            # INSPIRE conformity
            if tag.startswith("conformity:inspire"):
                inspire_valid = "Oui"
                continue
            else:
                pass

        # formatting links to visualize on OpenCatalog and edit on APP
        if share is not None:
            link_visu = utils.get_view_url(
                md_id=md._id, share_id=share._id, share_token=share.urlToken
            )
        else:
            logger.warning(
                "Unable to build the OpenCatalog URL for this metadata: {} ({})".format(
                    md.title_or_name(), md._id
                )
            )
            link_visu = ""
        link_edit = utils.get_edit_url(md)

        # ---- CONTACTS # ----------------------------------------------------
        contacts_out = []
        if md.contacts:
            # formatting contacts
            for ct_in in md.contacts:
                ct = {}
                # translate contact role
                ct["role"] = self.isogeo_tr("roles", ct_in.get("role"))
                # ensure other contacts fields
                ct["name"] = ct_in.get("contact").get("name", "NR")
                ct["organization"] = ct_in.get("contact").get("organization", "")
                ct["email"] = ct_in.get("contact").get("email", "")
                ct["phone"] = ct_in.get("contact").get("phone", "")
                ct["fax"] = ct_in.get("contact").get("fax", "")
                ct["addressLine1"] = ct_in.get("contact").get("addressLine1", "")
                ct["addressLine2"] = ct_in.get("contact").get("addressLine2", "")
                ct["zipCode"] = ct_in.get("contact").get("zipCode", "")
                ct["city"] = ct_in.get("contact").get("city", "")
                ct["countryCode"] = ct_in.get("contact").get("countryCode", "")
                # store into the final list
                contacts_out.append(ct)

        # ---- ATTRIBUTES --------------------------------------------------
        fields_out = []
        if md.type == "vectorDataset" and isinstance(md.featureAttributes, list):
            for f_in in md.featureAttributes:
                field = {}
                # ensure other fields
                field["name"] = self.fmt.clean_xml(f_in.get("name", ""))
                field["alias"] = self.fmt.clean_xml(f_in.get("alias", ""))
                field["description"] = self.fmt.clean_xml(f_in.get("description", ""))
                field["dataType"] = f_in.get("dataType", "")
                field["language"] = f_in.get("language", "")
                # store into the final list
                fields_out.append(field)

        # ---- EVENTS ------------------------------------------------------
        events_out = []
        if md.events:
            for e in md.events:
                evt = Event(**e)
                # pop creation events (already in the export document)
                if evt.kind == "creation":
                    continue
                # prevent invalid character for XML formatting in description
                evt.description = self.fmt.clean_xml(evt.description)
                # make data human readable
                evt.date = utils.hlpr_datetimes(evt.date).strftime(self.dates_fmt)
                # translate event kind
                # evt.kind = self.isogeo_tr("events", evt.kind)
                # append
                events_out.append(evt.to_dict())

        # ---- IDENTIFICATION # ----------------------------------------------
        # Resource type
        resource_type = self.isogeo_tr("formatTypes", md.type)

        # Format
        format_version = ""
        if md.format and md.type in ("rasterDataset", "vectorDataset"):
            format_version = "{0} {1} ({2})".format(
                format_lbl, md.formatVersion, md.encoding
            )

        # path to the resource
        localplace = md.path

        # ---- HISTORY # -----------------------------------------------------
        # data events
        if md.created:
            data_created = utils.hlpr_datetimes(md.created).strftime(self.dates_fmt)
        else:
            data_created = ""
        if md.modified:
            data_updated = utils.hlpr_datetimes(md.modified).strftime(self.dates_fmt)
        else:
            data_updated = ""
        if md.published:
            data_published = utils.hlpr_datetimes(md.published).strftime(self.dates_fmt)
        else:
            data_published = ""

        # validity
        if md.validFrom:
            validFrom = utils.hlpr_datetimes(md.validFrom).strftime(self.dates_fmt)
        else:
            validFrom = ""
        # end validity date
        if md.validTo:
            validTo = utils.hlpr_datetimes(md.validTo).strftime(self.dates_fmt)
        else:
            validTo = ""

        # ---- SPECIFICATIONS # -----------------------------------------------
        if md.specifications:
            specs_out = self.fmt.specifications(md_specifications=md.specifications)
        else:
            specs_out = ""

        # ---- CGUs # --------------------------------------------------------
        if md.conditions:
            cgus_out = self.fmt.conditions(md_cgus=md.conditions)
        else:
            cgus_out = ""

        # ---- LIMITATIONS # -------------------------------------------------
        if md.limitations:
            lims_out = self.fmt.limitations(md_limitations=md.limitations)
        else:
            lims_out = ""

        # ---- METADATA # ----------------------------------------------------
        md_created = utils.hlpr_datetimes(md._created).strftime(self.datetimes_fmt)
        md_updated = utils.hlpr_datetimes(md._modified).strftime(self.datetimes_fmt)

        # FILLFULLING THE TEMPLATE #
        context = {
            # "varThumbnail": InlineImage(docx_template, md.thumbnail),
            "varTitle": self.fmt.clean_xml(md.title),
            "varAbstract": self.fmt.clean_xml(md.abstract),
            "varNameTech": md.name,
            "varCollectContext": self.fmt.clean_xml(md.collectionContext),
            "varCollectMethod": self.fmt.clean_xml(md.collectionMethod),
            "varDataDtCrea": data_created,
            "varDataDtUpda": data_updated,
            "varDataDtPubl": data_published,
            "varValidityStart": validFrom,
            "varValidityEnd": validTo,
            "validityComment": self.fmt.clean_xml(md.validityComment),
            "varFormat": md.format,
            "varGeometry": md.geometry,
            "varObjectsCount": md.features,
            "varKeywords": " ; ".join(li_motscles),
            "varKeywordsCount": len(li_motscles),
            "varType": resource_type,
            "varOwner": md.groupName,
            "varScale": md.scale,
            "varTopologyInfo": self.fmt.clean_xml(md.topologicalConsistency),
            "varInspireTheme": " ; ".join(li_theminspire),
            "varInspireConformity": inspire_valid,
            "varLimitations": lims_out,
            "varCGUS": cgus_out,
            "varSpecifications": specs_out,
            "varContactsCount": len(md.contacts),
            "varContactsDetails": contacts_out,
            "varSRS": srs,
            "varPath": localplace,
            "varFieldsCount": len(fields),
            "varFields": fields_out,
            "varEventsCount": len(md.events),
            "varEvents": events_out,
            "varMdDtCrea": md_created,
            "varMdDtUpda": md_updated,
            "varMdDtExp": datetime.now().strftime(self.datetimes_fmt),
            "varViewOC": link_visu,
            "varEditAPP": link_edit,
        }

        # fillfull file
        try:
            docx_template.render(context, autoescape=True)
            logger.info(
                "Vector metadata stored: {} ({})".format(
                    md.title_or_name(slugged=1), md._id
                )
            )
        except etree.XMLSyntaxError as e:
            logger.error(
                "Invalid character in XML: {}. "
                "Any special character (<, <, &...)? Check: {}".format(e, link_edit)
            )
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            logger.error(
                "Encoding error: {}. "
                "Any special character (<, <, &...)? Check: {}".format(e, link_edit)
            )
        except Exception as e:
            logger.error("Unexpected error: {}. Check: {}".format(e, link_edit))

        # end of function
        return

    # ------------ UTILITIES ---------------------
    def missing_values(self, idx_type=0):
        """Return default values defined in the class as a tuple.

        idx_type (optional) -- index of the value type requested:

            1: for strings and integers
            2: for dates and datetimes
        """
        rpl_value = self.default_values[idx_type]
        # end of method
        return rpl_value


# ###############################################################################
# ###### Stand alone program ########
# ###################################
if __name__ == "__main__":
    """
        Standalone execution and tests
    """
    # ------------ Specific imports ----------------
    from dotenv import load_dotenv
    from logging.handlers import RotatingFileHandler
    from os import environ
    from pathlib import Path
    import urllib3

    from isogeo_pysdk import Isogeo

    # ------------ Log & debug ----------------
    logger = logging.getLogger()
    logging.captureWarnings(True)
    logger.setLevel(logging.DEBUG)
    # logger.setLevel(logging.INFO)

    log_format = logging.Formatter(
        "%(asctime)s || %(levelname)s "
        "|| %(module)s - %(lineno)d ||"
        " %(funcName)s || %(message)s"
    )

    # debug to the file
    log_file_handler = RotatingFileHandler("dev_debug.log", "a", 3000000, 1)
    log_file_handler.setLevel(logging.DEBUG)
    log_file_handler.setFormatter(log_format)

    # info to the console
    log_console_handler = logging.StreamHandler()
    log_console_handler.setLevel(logging.INFO)
    log_console_handler.setFormatter(log_format)

    logger.addHandler(log_file_handler)
    logger.addHandler(log_console_handler)

    # ------------ Real start ----------------
    # get user ID as environment variables
    load_dotenv("dev.env")

    # ignore warnings related to the QA self-signed cert
    if environ.get("ISOGEO_PLATFORM").lower() == "qa":
        urllib3.disable_warnings()

    # for oAuth2 Backend (Client Credentials Grant) Flow
    isogeo = Isogeo(
        auth_mode="group",
        client_id=environ.get("ISOGEO_API_GROUP_CLIENT_ID"),
        client_secret=environ.get("ISOGEO_API_GROUP_CLIENT_SECRET"),
        auto_refresh_url="{}/oauth/token".format(environ.get("ISOGEO_ID_URL")),
        platform=environ.get("ISOGEO_PLATFORM", "qa"),
    )

    # getting a token
    isogeo.connect()

    # misc
    METADATA_TEST_FIXTURE_UUID = environ.get("ISOGEO_FIXTURES_METADATA_COMPLETE")
    WORKGROUP_TEST_FIXTURE_UUID = environ.get("ISOGEO_WORKGROUP_TEST_UUID")

    # ------------ Isogeo search --------------------------
    search_results = isogeo.search(include="all")
    isogeo.close()  # close session

    # ------------ REAL START ----------------------------
    # output folder
    Path("_output/").mkdir(exist_ok=True)

    # template
    template_path = Path(r"tests\fixtures\template_Isogeo.docx")
    assert template_path.is_file()

    # instanciate
    toDocx = Isogeo2docx()

    # parse results and export it
    for md in search_results.results:
        # load metadata as object
        metadata = Metadata.clean_attributes(md)
        # prepare the template
        tpl = DocxTemplate(template_path.resolve())
        # fill the template
        toDocx.md2docx(docx_template=tpl, md=metadata)
        # filename
        md_name = metadata.title_or_name(slugged=1)
        uuid = "{}".format(metadata._id[:5])
        out_docx_filename = "_output/{}_{}.docx".format(md_name, uuid)

        # save it
        tpl.save(out_docx_filename)

        # delete template object
        del tpl
