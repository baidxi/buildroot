#####################################################
#
# svt-av1
#
#####################################################

SVT_AV1_VERSION = 3.0.2
SVT_AV1_SOURCE =SVT-AV1-v$(SVT_AV1_VERSION).tar.bz2
SVT_AV1_SITE = https://gitlab.com/AOMediaCodec/SVT-AV1/-/archive/v$(SVT_AV1_VERSION)
SVT_AV1_LICENSE += BSD-2-clause
SVT_AV1_LICENSE_FILES = LICENSE.md LICENSE-BSD2.md
SVT_AV1_INSTALL_STAGING = YES

$(eval $(cmake-package))