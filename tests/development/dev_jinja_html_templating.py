# -*- coding: UTF-8 -*-
#! python3

"""
    Jinja2 sample - Launched from the root of IsogeoToOffice repository

    Purpose:     Load an HTML template and replace tags values.
    Author:      Isogeo
    Python:      3.7.x
"""

# #############################################################################
# ########## Libraries #############
# ##################################
# jinja2
from jinja2 import Environment, FileSystemLoader

# #############################################################################
# ######### Main program ###########
# ##################################

# Jinja2 template environment
tpl_loader = FileSystemLoader(searchpath="./")
tpl_env = Environment(loader=tpl_loader)

# input template
# in_html_tpl = Path("tests/development/dev_template_html.html")
# template = tpl_env.get_template(in_html_tpl)
template = tpl_env.get_template("tests/development/dev_template_html.html")

# output template
out_html_file = template.render(
    title="Isogeo To Office",
    welcome_message="Isogeo To Office - HTML Templating successed",
)

with open("test_out_html_templated.html", "w") as fh:
    fh.write(out_html_file)
