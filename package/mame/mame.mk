################################################################################
#
# mame
#
################################################################################

MAME_VERSION = db65a583bd2da39514a544c58362a6ac170179ac
MAME_SITE = https://github.com/libretro/mame.git
MAME_SITE_METHOD = git
MAME_LICENSE = MAME
MAME_MAKE_OPTS += \
	TOOLCHAIN=$(TARGET_CROSS) \
	CROSS_COMPILE=$(TARGET_CROSS) \
	CC=$(TARGET_CROSS)gcc \
	CXX=$(TARGET_CROSS)g++ \
	OVERRIDE_CC=$(TARGET_CROSS)gcc \
	OVERRIDE_CXX=$(TARGET_CROSS)g++ \
	OVERRIDE_LD=$(TARGET_CROSS)ld	\
	OVERRIDE_AR=$(TARGET_CROSS)ar	\
	TARGET_ARCH=$(BR2_ARCH) \
	TARGETOS=$(BR2_ARCH)

define MAME_BUILD_CMDS
	$(TARGET_MAKE_ENV) $(TARGET_CONFIGURE_ARGS) $(MAKE) -C $(@D) linux $(MAME_MAKE_OPTS)
endef

define MAME_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/root/.config/retroarch/cores
	wget -O $(TARGET_DIR)/root/.config/retroarch/cores/mame_libretro.info https://raw.githubusercontent.com/libretro/libretro-super/master/dist/info/mame_libretro.info
	$(INSTALL) -m 0755 -D $(@D)/mame_libretro.so $(TARGET_DIR)/root/.config/retroarch/cores/
endef

$(eval $(generic-package))
