# Isogeo - DOCX Exporter

[![PyPI](https://img.shields.io/pypi/v/isogeo-export-docx.svg?style=flat-square) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/isogeo-export-docx?style=flat-square)](https://pypi.org/project/isogeo-export-docx/)

[![Build Status](https://dev.azure.com/isogeo/PythonTooling/_apis/build/status/isogeo.export-docx-py?branchName=master)](https://dev.azure.com/isogeo/PythonTooling/_build/latest?definitionId=24&branchName=master) ![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/isogeo/PythonTooling/24?style=flat-square)

[![Documentation Status](https://readthedocs.org/projects/isogeo-export-docx-py/badge/?version=latest)](https://isogeo-export-docx-py.readthedocs.io/en/latest/?badge=latest) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

Python package to export Isogeo metadata into Word documents using the [Python SDK](https://pypi.org/project/isogeo-pysdk/) and [docxtpl](https://pypi.org/project/docxtpl/).

## Usage in a nutshell

1. Install:

    ```powershell
    pip install isogeo-export-docx
    ```

2. Authenticate

    ```python
    # import
    from isogeo_pysdk import Isogeo
    # API client
    isogeo = Isogeo(
        auth_mode="group",
        client_id=ISOGEO_API_GROUP_CLIENT_ID,
        client_secret=ISOGEO_API_GROUP_CLIENT_SECRET,
        auto_refresh_url="{}/oauth/token".format(ISOGEO_ID_URL),
        platform=ISOGEO_PLATFORM,
    )

    # getting a token
    isogeo.connect()
    ```

3. Make a search:

    ```python
    search = isogeo.search(include="all",)
    # close session
    isogeo.close()
    ```

4. Export:

    ```python
    # import
    from isogeotodocx import Isogeo2docx

    # output folder
    Path("_output/").mkdir(exist_ok=True)
    # template
    template_path = Path(r"tests\fixtures\template_Isogeo.docx")

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
    ```
