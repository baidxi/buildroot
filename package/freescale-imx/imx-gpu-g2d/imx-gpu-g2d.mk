################################################################################
#
# imx-gpu-g2d
#
################################################################################

IMX_GPU_G2D_REVISION = accdd64
ifeq ($(BR2_aarch64),y)
IMX_GPU_G2D_VERSION = 6.4.11.p2.10-aarch64
else
IMX_GPU_G2D_VERSION = 6.4.11.p2.10-arm
endif
IMX_GPU_G2D_SITE = $(FREESCALE_IMX_SITE)
IMX_GPU_G2D_SOURCE = imx-gpu-g2d-$(IMX_GPU_G2D_VERSION)-$(IMX_GPU_G2D_REVISION).bin
IMX_GPU_G2D_DEPENDENCIES = imx-gpu-viv
IMX_GPU_G2D_INSTALL_STAGING = YES

IMX_GPU_G2D_LICENSE = NXP Semiconductor Software License Agreement
IMX_GPU_G2D_LICENSE_FILES = EULA COPYING SCR-imx-gpu-g2d.txt
IMX_GPU_G2D_REDISTRIBUTE = NO

define IMX_GPU_G2D_EXTRACT_CMDS
	$(call NXP_EXTRACT_HELPER,$(IMX_GPU_G2D_DL_DIR)/$(IMX_GPU_G2D_SOURCE))
endef

IMX_GPU_G2D_SUBDIR = $(if $(BR2_PACKAGE_FREESCALE_IMX_PLATFORM_IMX8MM),mx8mm,)

define IMX_GPU_G2D_INSTALL_STAGING_CMDS
	cp -a $(@D)/g2d/usr/lib/$(IMX_GPU_G2D_SUBDIR)/libg2d*  $(STAGING_DIR)/usr/lib/
endef

define IMX_GPU_G2D_INSTALL_TARGET_CMDS
	cp -a $(@D)/g2d/usr/lib/$(IMX_GPU_G2D_SUBDIR)/libg2d*  $(TARGET_DIR)/usr/lib/
endef

$(eval $(generic-package))
