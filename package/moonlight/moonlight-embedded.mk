################################################################################
#
# moonlight-embedded
#
################################################################################

MOONLIGHT_VERSION = v2.7.0
MOONLIGHT_SITE = https://github.com/moonlight-stream/moonlight-embedded.git
MOONLIGHT_SITE_METHOD = git
MOONLIGHT_INSTALL_STAGING = YES
MOONLIGHT_GIT_SUBMODULES = YES

MOONLIGHT_DEPENDENCIES = sdl2 ffmpeg avahi dbus expat libcurl libevdev opus libopenssl

$(eval $(cmake-package))