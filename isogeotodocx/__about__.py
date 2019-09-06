# Metadata bout the package to easily retrieve informations about it.
# see: https://packaging.python.org/guides/single-sourcing-package-version/

from datetime import date

__all__ = [
    "__title__",
    "__summary__",
    "__uri__",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
]


__title__ = "Isogeo MS Word Exporter"
__summary__ = (
    "Export metadata from the Isogeo REST API into Microsoft Word documents (.docx)."
)
__uri__ = "https://pypi.org/project/isogeo-export-docx/"

__version__ = "1.1.1"

__author__ = "Isogeo"
__email__ = "dev@isogeo.com"

__license__ = "GNU Lesser General Public License v3.0"
__copyright__ = "2016 - {0}, {1}".format(date.today().year, __author__)
