################################################################################
#
# python-click
#
################################################################################

PYTHON_CLICK_VERSION = 8.3.3
PYTHON_CLICK_SOURCE = click-$(PYTHON_CLICK_VERSION).tar.gz
PYTHON_CLICK_SITE = https://files.pythonhosted.org/packages/bb/63/f9e1ea081ce35720d8b92acde70daaedace594dc93b693c869e0d5910718
PYTHON_CLICK_SETUP_TYPE = flit
PYTHON_CLICK_LICENSE = BSD-3-Clause
PYTHON_CLICK_LICENSE_FILES = LICENSE.txt

$(eval $(python-package))
