# -*- coding: utf-8 -*-
#!/usr/bin/env python3

"""
    Setup script to package Isogeo PySDK Python module

    see: https://github.com/isogeo/export-docx-py/
"""

# ############################################################################
# ########## Libraries #############
# ##################################

# standard library
import pathlib

from setuptools import find_packages, setup

# package to get package metadatas
from isogeotodocx import __about__

# SETUP ######################################################################

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# setup metadata
setup(
    # meta
    name="isogeo-export-docx",
    version=__about__.__version__,
    author=__about__.__author__,
    author_email=__about__.__email__,
    description=__about__.__summary__,
    long_description=README,
    long_description_content_type="text/markdown",
    keywords="GIS metadata INSPIRE Isogeo API REST geographical data DOCX Word",
    license="LGPL3",
    url=__about__.__uri__,
    project_urls={
        "Docs": "https://isogeo-export-docx-py.readthedocs.io/",
        "Bug Reports": "{}issues/".format(__about__.__uri__),
        "Source": __about__.__uri__,
    },
    # dependencies
    install_requires=["isogeo-pysdk>=3.2,<3.4", "docxtpl==0.6.*"],
    extras_require={
        "dev": ["black", "python-dotenv"],
        "test": ["pytest", "pytest-cov"],
    },
    python_requires=">=3.6, <4",
    # packaging
    packages=find_packages(
        exclude=["contrib", "docs", "*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    include_package_data=True,
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
