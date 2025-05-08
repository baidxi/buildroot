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

MOONLIGHT_DEPENDENCIES = avahi dbus expat libcurl libevdev opus libopenssl

ifeq ($(BR2_PACKAGE_SDL2),y)
MOONLIGHT_CONF_OPTS += -DENABLE_SDL:bool=ON
MOONLIGHT_DEPENDENCIES += sdl2
else
MOONLIGHT_CONF_OPTS += -DENABLE_SDL:bool=OFF
endif

ifeq ($(BR2_PACKAGE_FFMPEG),y)
MOONLIGHT_CONF_OPTS += -DENABLE_FFMPEG:bool=ON
MOONLIGHT_DEPENDENCIES += ffmpeg
else
MOONLIGHT_CONF_OPTS += -DENABLE_FFMPEG:bool=OFF
endif

ifeq ($(BR2_PACKAGE_XORG7),y)
MOONLIGHT_CONF_OPTS += -DENABLE_X11:bool=ON
MOONLIGHT_DEPENDENCIES += xlib_libX11 xlib_libXext
else
MOONLIGHT_CONF_OPTS += -DENABLE_X11:bool=OFF
endif

ifeq ($(BR2_PACKAGE_LIBCEC),y)
MOONLIGHT_CONF_OPTS += -DENABLE_CEC:bool=ON
MOONLIGHT_DEPENDENCIES += libcec
else
MOONLIGHT_CONF_OPTS += -DENABLE_CEC:bool=OFF
endif

ifeq ($(BR2_PACKAGE_PULSEAUDIO),y)
MOONLIGHT_CONF_OPTS += -DENABLE_PULSE:bool=ON
MOONLIGHT_DEPENDENCIES += pulseaudio
else
MOONLIGHT_CONF_OPTS += -DENABLE_PULSE:bool=OFF
endif


$(eval $(cmake-package))