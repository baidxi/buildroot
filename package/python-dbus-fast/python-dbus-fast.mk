################################################################################
#
# python-dbus-fast
#
################################################################################

PYTHON_DBUS_FAST_VERSION = 4.0.4
PYTHON_DBUS_FAST_SOURCE = dbus_fast-$(PYTHON_DBUS_FAST_VERSION).tar.gz
PYTHON_DBUS_FAST_SITE = https://files.pythonhosted.org/packages/5f/cd/402b0e524bdf37d8b1d22b1d926c538bf1d2eedf115ea1d401c6c08a7d81
PYTHON_DBUS_FAST_SETUP_TYPE = poetry
PYTHON_DBUS_FAST_LICENSE = MIT
PYTHON_DBUS_FAST_LICENSE_FILES = LICENSE
PYTHON_DBUS_FAST_ENV = REQUIRE_CYTHON=1
PYTHON_DBUS_FAST_BUILD_OPTS = --skip-dependency-check
PYTHON_DBUS_FAST_DEPENDENCIES = \
	host-python-cython \
	host-python-setuptools

$(eval $(python-package))
