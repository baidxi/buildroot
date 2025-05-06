##############################################################
#
# libnotify
#
##############################################################

LIBNOTIFY_VERSION = 0.8.6
LIBNOTIFY_SITE = $(call github,GNOME,libnotify,$(LIBNOTIFY_VERSION))
LIBNOTIFY_LICENSE = LGPL-2.1
LIBNOTIFY_DEPENDENCIES = gdk-pixbuf libgtk2 libgtk3

LIBNOTIFY_CONF_OPTS = \
	-Dman=false	\
	-Dgtk_doc=false \
	-Ddocbook_docs=disabled \
	-Dtests=false

$(eval $(meson-package))