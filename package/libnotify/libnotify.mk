##############################################################
#
# libnotify
#
##############################################################

LIBNOTIFY_VERSION = 0.8.6
LIBNOTIFY_SITE = $(call github,GNOME,libnotify,$(LIBNOTIFY_VERSION))
LIBNOTIFY_LICENSE = LGPL-2.1

$(eval $(meson-package))