# -*- coding: utf-8 -*-
#! python3

"""
    This package is used to export Isogeo metadata into Excel workbooks usng the Isogeo Python SDK and DocxTpl (feat. Python Docx).
"""

# submodules
from .__about__ import __version__  # noqa: F401
from .isogeo2docx import Isogeo2docx  # noqa: F401

# subpackages
from .utils import *  # noqa: F401

VERSION = __version__
