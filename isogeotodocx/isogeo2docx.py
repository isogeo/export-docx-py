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
from docxtpl import DocxTemplate, InlineImage, etree
from isogeo_pysdk import Event, IsogeoTranslator, IsogeoUtils, Metadata, Share

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
    :param dict thumbnails: dictionary of metadatas associated to an image path
    :param str url_base_edit: base url to format edit links (basically app.isogeo.com)
    :param str url_base_view: base url to format view links (basically open.isogeo.com)
    """

    def __init__(
        self,
        lang="FR",
        thumbnails: dict = None,
        url_base_edit: str = "https://app.isogeo.com",
        url_base_view: str = "https://open.isogeo.com",
    ):
        """Processing matching between Isogeo metadata and a Miscrosoft Word template."""
        super(Isogeo2docx, self).__init__()

        # ------------ VARIABLES ---------------------
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
        self.fmt = Formatter()

        # THUMBNAILS
        if thumbnails is not None and isinstance(thumbnails, dict):
            self.thumbnails = thumbnails
        else:
            self.thumbnails = {}
            logger.debug("No valid thumbnails matching table passed.")

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

        # template context starting with metadata attributes which do not require any special formatting
        context = {
            # IDENTIFICATION
            "varType": self.isogeo_tr("formatTypes", md.type),
            "varTitle": self.fmt.clean_xml(md.title),
            "varAbstract": self.fmt.clean_xml(md.abstract),
            "varNameTech": self.fmt.clean_xml(md.name),
            "varOwner": md.groupName,
            "varPath": self.fmt.clean_xml(md.path),
            # QUALITY
            "varTopologyInfo": self.fmt.clean_xml(md.topologicalConsistency),
            # HISTORY
            "varCollectContext": self.fmt.clean_xml(md.collectionContext),
            "varCollectMethod": self.fmt.clean_xml(md.collectionMethod),
            "varValidityComment": self.fmt.clean_xml(md.validityComment),
            # GEOGRAPHY
            "varEncoding": self.fmt.clean_xml(md.encoding),
            "varScale": self.fmt.clean_xml(md.scale),
            "varGeometry": self.fmt.clean_xml(md.geometry),
            "varObjectsCount": self.fmt.clean_xml(md.features),
            # METADATA
            "varMdDtCrea": utils.hlpr_datetimes(md._created).strftime(
                self.datetimes_fmt
            ),
            "varMdDtUpda": utils.hlpr_datetimes(md._modified).strftime(
                self.datetimes_fmt
            ),
            "varMdDtExp": datetime.now().strftime(self.datetimes_fmt),
        }

        # TAGS #
        # extracting & parsing tags
        li_motscles = []
        li_theminspire = []

        # default values
        context["varInspireConformity"] = self.isogeo_tr("quality", "isNotConform")

        # looping on tags
        for tag in md.tags.keys():
            # free keywords
            if tag.startswith("keyword:isogeo"):
                li_motscles.append(md.tags.get(tag))
                continue

            # INSPIRE themes
            if tag.startswith("keyword:inspire-theme"):
                li_theminspire.append(md.tags.get(tag))
                continue

            # coordinate system
            if tag.startswith("coordinate-system"):
                context["varSRS"] = md.tags.get(tag)
                continue

            # format
            if tag.startswith("format"):
                context["varFormat"] = md.tags.get(tag)
                if md.formatVersion:
                    context["varFormat"] += " " + md.formatVersion
                continue

            # INSPIRE conformity
            if tag.startswith("conformity:inspire"):
                context["varInspireConformity"] = self.isogeo_tr("quality", "isConform")
                continue

        # add tags to the template context
        context["varKeywords"] = " ; ".join(li_motscles)
        context["varKeywordsCount"] = len(li_motscles)
        context["varInspireTheme"] = " ; ".join(li_theminspire)

        # formatting links to visualize on OpenCatalog and edit on APP
        if share is not None:
            context["varViewOC"] = utils.get_view_url(
                md_id=md._id, share_id=share._id, share_token=share.urlToken
            )
        else:
            logger.debug(
                "No OpenCatalog URL for metadata: {} ({})".format(
                    md.title_or_name(), md._id
                )
            )

        # link to APP
        context["varEditAPP"] = utils.get_edit_url(md)

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

            # add it to final context
            context["varContactsCount"] = len(contacts_out)
            context["varContactsDetails"] = contacts_out

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

            # add to the final context
            context["varFieldsCount"] = len(fields_out)
            context["varFields"] = fields_out

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

            # add to the final context
            context["varEventsCount"] = len(events_out)
            context["varEvents"] = events_out

        # ---- HISTORY # -----------------------------------------------------
        # data events
        if md.created:
            context["varDataDtCrea"] = utils.hlpr_datetimes(md.created).strftime(
                self.dates_fmt
            )

        if md.modified:
            context["varDataDtUpda"] = utils.hlpr_datetimes(md.modified).strftime(
                self.dates_fmt
            )

        if md.published:
            context["varDataDtPubl"] = utils.hlpr_datetimes(md.published).strftime(
                self.dates_fmt
            )

        # validity
        if md.validFrom:
            context["varValidityStart"] = utils.hlpr_datetimes(md.validFrom).strftime(
                self.dates_fmt
            )

        # end validity date
        if md.validTo:
            context["varValidityEnd"] = utils.hlpr_datetimes(md.validTo).strftime(
                self.dates_fmt
            )

        # ---- SPECIFICATIONS # -----------------------------------------------
        if md.specifications:
            context["varSpecifications"] = self.fmt.specifications(
                md_specifications=md.specifications
            )

        # ---- CGUs # --------------------------------------------------------
        if md.conditions:
            context["varConditions"] = self.fmt.conditions(md_conditions=md.conditions)

        # ---- LIMITATIONS # -------------------------------------------------
        if md.limitations:
            context["varLimitations"] = self.fmt.limitations(
                md_limitations=md.limitations
            )

        # -- THUMBNAIL -----------------------------------------------------------------
        if md._id in self.thumbnails and Path(self.thumbnails.get(md._id)).is_file():
            thumbnail = str(Path(self.thumbnails.get(md._id)).resolve())
            context["varThumbnail"] = InlineImage(docx_template, thumbnail)
            logger.info(
                "Thumbnail found for {}: {}".format(md.title_or_name(1), thumbnail)
            )

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
                "Any special character (<, <, &...)? Check: {}".format(
                    e, context.get("varEditAPP")
                )
            )
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            logger.error(
                "Encoding error: {}. "
                "Any special character (<, <, &...)? Check: {}".format(
                    e, context.get("varEditAPP")
                )
            )
        except Exception as e:
            logger.error(
                "Unexpected error: {}. Check: {}".format(e, context.get("varEditAPP"))
            )

        # end of function
        return


# ###############################################################################
# ###### Stand alone program ########
# ###################################
if __name__ == "__main__":
    """
        Standalone execution and basic tests
    """
    # ------------ Specific imports ----------------
    from csv import DictReader
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

    # misc
    METADATA_TEST_FIXTURE_UUID = environ.get("ISOGEO_FIXTURES_METADATA_COMPLETE")
    WORKGROUP_TEST_FIXTURE_UUID = environ.get("ISOGEO_WORKGROUP_TEST_UUID")

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

    # ------------ Isogeo search --------------------------
    search_results = isogeo.search(
        include="all",
        specific_md=(
            "70f1192f67ac43e5987800ead18effb2",
            "b140d9a92c20416d97c3cdc12dc12607",
        ),
    )
    isogeo.close()  # close session

    # ------------ REAL START ----------------------------
    # output folder
    Path("_output/").mkdir(exist_ok=True)

    # template
    template_path = Path("tests/fixtures/template_Isogeo.docx")
    assert template_path.is_file()

    # thumbnails table
    thumbnails_table_csv_path = Path("tests/fixtures/thumbnails.csv")
    assert thumbnails_table_csv_path.is_file()

    # CSV structure
    csv_headers = ["isogeo_uuid", "isogeo_title_slugged", "img_abs_path"]
    thumbnails_dict = {}
    with thumbnails_table_csv_path.open("r", newline="") as csv_thumbnails:
        reader = DictReader(csv_thumbnails, fieldnames=csv_headers)
        next(reader, None)  # skip header line
        for row in reader:
            thumbnails_dict[row.get("isogeo_uuid")] = row.get("img_abs_path")

    # instanciate
    toDocx = Isogeo2docx(thumbnails=thumbnails_dict)

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
