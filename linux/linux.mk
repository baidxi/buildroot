################################################################################
#
# Linux kernel target
#
################################################################################

LINUX_VERSION = $(call qstrip,$(BR2_LINUX_KERNEL_VERSION))
LINUX_LICENSE = GPL-2.0
ifeq ($(BR2_LINUX_KERNEL_LATEST_VERSION),y)
LINUX_LICENSE_FILES = \
	COPYING \
	LICENSES/preferred/GPL-2.0 \
	LICENSES/exceptions/Linux-syscall-note
endif
LINUX_CPE_ID_VENDOR = linux
LINUX_CPE_ID_PRODUCT = linux_kernel
LINUX_CPE_ID_PREFIX = cpe:2.3:o

# Compute LINUX_SOURCE and LINUX_SITE from the configuration
ifeq ($(BR2_LINUX_KERNEL_CUSTOM_TARBALL),y)
LINUX_TARBALL = $(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_TARBALL_LOCATION))
LINUX_SITE = $(patsubst %/,%,$(dir $(LINUX_TARBALL)))
LINUX_SOURCE = $(notdir $(LINUX_TARBALL))
else ifeq ($(BR2_LINUX_KERNEL_CUSTOM_GIT),y)
LINUX_SITE = $(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_REPO_URL))
LINUX_SITE_METHOD = git
ifeq ($(BR2_LINUX_KERNEL_CUSTOM_REPO_GIT_SUBMODULES),y)
LINUX_GIT_SUBMODULES = YES
endif
else ifeq ($(BR2_LINUX_KERNEL_CUSTOM_HG),y)
LINUX_SITE = $(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_REPO_URL))
LINUX_SITE_METHOD = hg
else ifeq ($(BR2_LINUX_KERNEL_CUSTOM_SVN),y)
LINUX_SITE = $(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_REPO_URL))
LINUX_SITE_METHOD = svn
else ifeq ($(BR2_LINUX_KERNEL_LATEST_CIP_VERSION)$(BR2_LINUX_KERNEL_LATEST_CIP_RT_VERSION),y)
LINUX_SOURCE = linux-cip-$(LINUX_VERSION).tar.gz
LINUX_SITE = https://git.kernel.org/pub/scm/linux/kernel/git/cip/linux-cip.git/snapshot
else ifneq ($(findstring -rc,$(LINUX_VERSION)),)
# Since 4.12-rc1, -rc kernels are generated from cgit. This also works for
# older -rc kernels.
LINUX_SITE = https://git.kernel.org/torvalds/t
else
LINUX_SOURCE = linux-$(LINUX_VERSION).tar.xz
ifeq ($(findstring x2.6.,x$(LINUX_VERSION)),x2.6.)
LINUX_SITE = $(BR2_KERNEL_MIRROR)/linux/kernel/v2.6
else
LINUX_SITE = $(BR2_KERNEL_MIRROR)/linux/kernel/v$(firstword $(subst ., ,$(LINUX_VERSION))).x
endif
endif

ifeq ($(BR2_LINUX_KERNEL)$(BR2_LINUX_KERNEL_LATEST_VERSION),y)
BR_NO_CHECK_HASH_FOR += $(LINUX_SOURCE)
endif

LINUX_PATCHES = $(call qstrip,$(BR2_LINUX_KERNEL_PATCH))

# We have no way to know the hashes for user-supplied patches.
BR_NO_CHECK_HASH_FOR += $(notdir $(LINUX_PATCHES))

# We rely on the generic package infrastructure to download and apply
# remote patches (downloaded from ftp, http or https). For local
# patches, we can't rely on that infrastructure, because there might
# be directories in the patch list (unlike for other packages).
LINUX_PATCH = $(filter ftp://% http://% https://%,$(LINUX_PATCHES))

# while the kernel is built for the target, the build may need various
# host libraries depending on config (and version), so use
# HOST_MAKE_ENV here. In particular, this ensures that our
# host-pkgconf will look for host libraries and not target ones.
LINUX_MAKE_ENV = \
	$(HOST_MAKE_ENV) \
	BR_BINARIES_DIR=$(BINARIES_DIR)

LINUX_INSTALL_IMAGES = YES
LINUX_DEPENDENCIES = \
	host-kmod \
	$(BR2_MAKE_HOST_DEPENDENCY)
LINUX_MAKE = $(BR2_MAKE)

# The kernel CONFIG_EXTRA_FIRMWARE feature requires firmware files at build
# time. Make sure they are available before the kernel builds.
LINUX_DEPENDENCIES += \
	$(if $(BR2_PACKAGE_INTEL_MICROCODE),intel-microcode) \
	$(if $(BR2_PACKAGE_LINUX_FIRMWARE),linux-firmware) \
	$(if $(BR2_PACKAGE_FIRMWARE_IMX),firmware-imx) \
	$(if $(BR2_PACKAGE_WIRELESS_REGDB),wireless-regdb)

# Starting with 4.16, the generated kconfig parser code is no longer
# shipped with the kernel sources, so we need flex and bison, but
# only if the host does not have them.
LINUX_KCONFIG_DEPENDENCIES = \
	$(BR2_BISON_HOST_DEPENDENCY) \
	$(BR2_FLEX_HOST_DEPENDENCY) \
	$(BR2_MAKE_HOST_DEPENDENCY)

# Starting with 4.18, the kconfig in the kernel calls the
# cross-compiler to check its capabilities. So we need the
# toolchain before we can call the configurators.
LINUX_KCONFIG_DEPENDENCIES += toolchain

# host tools needed for kernel compression
ifeq ($(BR2_LINUX_KERNEL_LZ4),y)
LINUX_DEPENDENCIES += host-lz4
else ifeq ($(BR2_LINUX_KERNEL_LZMA),y)
LINUX_DEPENDENCIES += host-lzma
else ifeq ($(BR2_LINUX_KERNEL_LZO),y)
LINUX_DEPENDENCIES += host-lzop
else ifeq ($(BR2_LINUX_KERNEL_XZ),y)
LINUX_DEPENDENCIES += host-xz
else ifeq ($(BR2_LINUX_KERNEL_ZSTD),y)
LINUX_DEPENDENCIES += host-zstd
endif
LINUX_COMPRESSION_OPT_$(BR2_LINUX_KERNEL_GZIP) += CONFIG_KERNEL_GZIP
LINUX_COMPRESSION_OPT_$(BR2_LINUX_KERNEL_LZ4) += CONFIG_KERNEL_LZ4
LINUX_COMPRESSION_OPT_$(BR2_LINUX_KERNEL_LZMA) += CONFIG_KERNEL_LZMA
LINUX_COMPRESSION_OPT_$(BR2_LINUX_KERNEL_LZO) += CONFIG_KERNEL_LZO
LINUX_COMPRESSION_OPT_$(BR2_LINUX_KERNEL_XZ) += CONFIG_KERNEL_XZ
LINUX_COMPRESSION_OPT_$(BR2_LINUX_KERNEL_ZSTD) += CONFIG_KERNEL_ZSTD
LINUX_COMPRESSION_OPT_$(BR2_LINUX_KERNEL_UNCOMPRESSED) += CONFIG_KERNEL_UNCOMPRESSED

ifeq ($(BR2_LINUX_KERNEL_NEEDS_HOST_OPENSSL),y)
LINUX_DEPENDENCIES += host-openssl
endif

ifeq ($(BR2_LINUX_KERNEL_NEEDS_HOST_LIBELF),y)
LINUX_DEPENDENCIES += host-elfutils host-pkgconf
endif

ifeq ($(BR2_LINUX_KERNEL_NEEDS_HOST_PAHOLE),y)
LINUX_DEPENDENCIES += host-pahole
else
define LINUX_FIXUP_CONFIG_PAHOLE_CHECK
	$(Q)if grep -q "^CONFIG_DEBUG_INFO_BTF=y" $(KCONFIG_DOT_CONFIG); then \
		echo "To use CONFIG_DEBUG_INFO_BTF, enable host-pahole (BR2_LINUX_KERNEL_NEEDS_HOST_PAHOLE)" 1>&2; \
		exit 1; \
	fi
endef
endif

ifeq ($(BR2_LINUX_KERNEL_NEEDS_HOST_PYTHON3),y)
LINUX_DEPENDENCIES += $(BR2_PYTHON3_HOST_DEPENDENCY)
endif

# If host-uboot-tools is selected by the user, assume it is needed to
# create a custom image
ifeq ($(BR2_PACKAGE_HOST_UBOOT_TOOLS),y)
LINUX_DEPENDENCIES += host-uboot-tools
endif

ifneq ($(ARCH_XTENSA_OVERLAY_FILE),)
define LINUX_XTENSA_OVERLAY_EXTRACT
	$(call arch-xtensa-overlay-extract,$(@D),linux)
endef
LINUX_POST_EXTRACT_HOOKS += LINUX_XTENSA_OVERLAY_EXTRACT
LINUX_EXTRA_DOWNLOADS += $(ARCH_XTENSA_OVERLAY_URL)
endif

# We don't want to run depmod after installing the kernel. It's done in a
# target-finalize hook, to encompass modules installed by packages.
# Disable building host tools with -Werror: newer gcc versions can be
# extra picky about some code (https://bugs.busybox.net/show_bug.cgi?id=14826)
LINUX_MAKE_FLAGS = \
	HOSTCC="$(HOSTCC) $(subst -I/,-isystem /,$(subst -I /,-isystem /,$(HOST_CFLAGS))) $(HOST_LDFLAGS)" \
	ARCH=$(KERNEL_ARCH) \
	KCFLAGS="$(LINUX_CFLAGS)" \
	INSTALL_MOD_PATH=$(TARGET_DIR) \
	CROSS_COMPILE="$(TARGET_CROSS)" \
	WERROR=0 \
	REGENERATE_PARSERS=1 \
	DEPMOD=$(HOST_DIR)/sbin/depmod

ifeq ($(BR2_REPRODUCIBLE),y)
LINUX_MAKE_ENV += \
	KBUILD_BUILD_VERSION=1 \
	KBUILD_BUILD_USER=buildroot \
	KBUILD_BUILD_HOST=buildroot \
	KBUILD_BUILD_TIMESTAMP="$(shell LC_ALL=C TZ='UTC' date -d @$(SOURCE_DATE_EPOCH))"
endif

# gcc-8 started warning about function aliases that have a
# non-matching prototype.  This seems rather useful in general, but it
# causes tons of warnings in the Linux kernel, where we rely on
# abusing those aliases for system call entry points, in order to
# sanitize the arguments passed from user space in registers.
# https://gcc.gnu.org/bugzilla/show_bug.cgi?id=82435
ifeq ($(BR2_TOOLCHAIN_GCC_AT_LEAST_8),y)
LINUX_CFLAGS += -Wno-attribute-alias
endif

# Disable FDPIC if enabled by default in toolchain
ifeq ($(BR2_BINFMT_FDPIC),y)
LINUX_CFLAGS += -mno-fdpic
endif

ifeq ($(BR2_LINUX_KERNEL_DTB_OVERLAY_SUPPORT),y)
LINUX_MAKE_ENV += DTC_FLAGS=-@
endif

# Get the real Linux version, which tells us where kernel modules are
# going to be installed in the target filesystem.
# Filter out 'w' from MAKEFLAGS, to workaround a bug in make 4.1 (#13141)
LINUX_VERSION_PROBED = `MAKEFLAGS='$(filter-out w,$(MAKEFLAGS))' $(BR2_MAKE) $(LINUX_MAKE_FLAGS) -C $(LINUX_DIR) --no-print-directory -s kernelrelease 2>/dev/null`

LINUX_DTS_NAME += $(call qstrip,$(BR2_LINUX_KERNEL_INTREE_DTS_NAME))
LINUX_DTSO_NAMES += $(call qstrip,$(BR2_LINUX_KERNEL_INTREE_DTSO_NAMES))

# We keep only the .dts files, so that the user can specify both .dts
# and .dtsi files in BR2_LINUX_KERNEL_CUSTOM_DTS_PATH. Both will be
# copied to arch/<arch>/boot/dts, but only the .dts files will
# actually be generated as .dtb.
LINUX_CUSTOM_DTS_PATH = $(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_DTS_PATH))
LINUX_DTS_NAME += $(basename $(filter %.dts,$(notdir $(LINUX_CUSTOM_DTS_PATH))))
LINUX_DTSO_NAMES += $(basename $(filter %.dtso,$(notdir $(LINUX_CUSTOM_DTS_PATH))))

LINUX_KERNEL_CUSTOM_DTS_DIR = $(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_DTS_DIR))
ifneq ($(LINUX_KERNEL_CUSTOM_DTS_DIR),)
# Use evaluation-during-assignment using := to avoid any re-evaluation
# of LINUX_DTS_LIST when LINUX_DTS_NAME is used.
LINUX_DTS_LIST := $(shell find $(LINUX_KERNEL_CUSTOM_DTS_DIR) -name '*.dts' -printf '%P\n' 2>/dev/null)
LINUX_DTSO_LIST := $(shell find $(LINUX_KERNEL_CUSTOM_DTS_DIR) -name '*.dtso' -printf '%P\n' 2>/dev/null)
LINUX_DTS_NAME += $(basename $(LINUX_DTS_LIST))
LINUX_DTSO_NAMES += $(basename $(LINUX_DTSO_LIST))

define LINUX_COPY_CUSTOM_DTS_FILES
	$(foreach d, $(LINUX_KERNEL_CUSTOM_DTS_DIR), \
		@$(call MESSAGE,"Copying devicetree overlay $(d)")$(sep) \
		$(Q)$(call SYSTEM_RSYNC,$(d),$(LINUX_ARCH_PATH)/boot/dts/)$(sep))
endef
endif

LINUX_KERNEL_APPENDED_FILES = $(call qstrip,$(BR2_LINUX_KERNEL_APPENDED_FILES))
ifneq ($(LINUX_KERNEL_APPENDED_FILES),)
define LINUX_COPY_CUSTOM_APPEND_FILES
	$(foreach d, $(LINUX_KERNEL_APPENDED_FILES), \
		$(Q)$(call SYSTEM_RSYNC,$(d),$(LINUX_DIR)/)$(sep))
endef
endif

LINUX_DTBS = $(addsuffix .dtb,$(LINUX_DTS_NAME)) $(addsuffix .dtbo,$(LINUX_DTSO_NAMES))

ifeq ($(BR2_LINUX_KERNEL_IMAGE_TARGET_CUSTOM),y)
LINUX_IMAGE_NAME = $(call qstrip,$(BR2_LINUX_KERNEL_IMAGE_NAME))
LINUX_TARGET_NAME = $(call qstrip,$(BR2_LINUX_KERNEL_IMAGE_TARGET_NAME))
ifeq ($(LINUX_IMAGE_NAME),)
LINUX_IMAGE_NAME = $(LINUX_TARGET_NAME)
endif
else
ifeq ($(BR2_LINUX_KERNEL_UIMAGE),y)
LINUX_IMAGE_NAME = uImage
else ifeq ($(BR2_LINUX_KERNEL_APPENDED_UIMAGE),y)
LINUX_IMAGE_NAME = uImage
else ifeq ($(BR2_LINUX_KERNEL_BZIMAGE),y)
LINUX_IMAGE_NAME = bzImage
else ifeq ($(BR2_LINUX_KERNEL_ZIMAGE),y)
LINUX_IMAGE_NAME = zImage
else ifeq ($(BR2_LINUX_KERNEL_ZIMAGE_EPAPR),y)
LINUX_IMAGE_NAME = zImage.epapr
else ifeq ($(BR2_LINUX_KERNEL_APPENDED_ZIMAGE),y)
LINUX_IMAGE_NAME = zImage
else ifeq ($(BR2_LINUX_KERNEL_CUIMAGE),y)
LINUX_IMAGE_NAME = cuImage.$(firstword $(LINUX_DTS_NAME))
else ifeq ($(BR2_LINUX_KERNEL_SIMPLEIMAGE),y)
LINUX_IMAGE_NAME = simpleImage.$(firstword $(LINUX_DTS_NAME))
else ifeq ($(BR2_LINUX_KERNEL_IMAGE),y)
LINUX_IMAGE_NAME = Image
else ifeq ($(BR2_LINUX_KERNEL_IMAGEGZ),y)
LINUX_IMAGE_NAME = Image.gz
else ifeq ($(BR2_LINUX_KERNEL_LINUX_BIN),y)
LINUX_IMAGE_NAME = linux.bin
else ifeq ($(BR2_LINUX_KERNEL_VMLINUX_BIN),y)
LINUX_IMAGE_NAME = vmlinux.bin
else ifeq ($(BR2_LINUX_KERNEL_VMLINUX_EFI),y)
LINUX_IMAGE_NAME = vmlinux.efi
else ifeq ($(BR2_LINUX_KERNEL_VMLINUX),y)
LINUX_IMAGE_NAME = vmlinux
else ifeq ($(BR2_LINUX_KERNEL_VMLINUZ),y)
LINUX_IMAGE_NAME = vmlinuz
else ifeq ($(BR2_LINUX_KERNEL_VMLINUZ_BIN),y)
LINUX_IMAGE_NAME = vmlinuz.bin
else ifeq ($(BR2_LINUX_KERNEL_VMLINUZ_EFI),y)
LINUX_IMAGE_NAME = vmlinuz.efi
endif
# The if-else blocks above are all the image types we know of, and all
# come from a Kconfig choice, so we know we have LINUX_IMAGE_NAME set
# to something
LINUX_TARGET_NAME = $(LINUX_IMAGE_NAME)
endif

LINUX_KERNEL_UIMAGE_LOADADDR = $(call qstrip,$(BR2_LINUX_KERNEL_UIMAGE_LOADADDR))
ifneq ($(LINUX_KERNEL_UIMAGE_LOADADDR),)
LINUX_MAKE_FLAGS += LOADADDR="$(LINUX_KERNEL_UIMAGE_LOADADDR)"
endif

# Compute the arch path, since i386 and x86_64 are in arch/x86 and not
# in arch/$(KERNEL_ARCH). Even if the kernel creates symbolic links
# for bzImage, arch/i386 and arch/x86_64 do not exist when copying the
# defconfig file.
ifeq ($(KERNEL_ARCH),i386)
LINUX_ARCH_PATH = $(LINUX_DIR)/arch/x86
else ifeq ($(KERNEL_ARCH),x86_64)
LINUX_ARCH_PATH = $(LINUX_DIR)/arch/x86
else ifeq ($(KERNEL_ARCH),sparc64)
LINUX_ARCH_PATH = $(LINUX_DIR)/arch/sparc
else
LINUX_ARCH_PATH = $(LINUX_DIR)/arch/$(KERNEL_ARCH)
endif

ifeq ($(BR2_LINUX_KERNEL_VMLINUX),y)
LINUX_IMAGE_PATH = $(LINUX_DIR)/$(LINUX_IMAGE_NAME)
else ifeq ($(BR2_LINUX_KERNEL_VMLINUZ),y)
LINUX_IMAGE_PATH = $(LINUX_DIR)/$(LINUX_IMAGE_NAME)
else ifeq ($(BR2_LINUX_KERNEL_VMLINUZ_BIN),y)
LINUX_IMAGE_PATH = $(LINUX_DIR)/$(LINUX_IMAGE_NAME)
else
LINUX_IMAGE_PATH = $(LINUX_ARCH_PATH)/boot/$(LINUX_IMAGE_NAME)
endif # BR2_LINUX_KERNEL_VMLINUX

define LINUX_APPLY_LOCAL_PATCHES
	for p in $(filter-out ftp://% http://% https://%,$(LINUX_PATCHES)) ; do \
		if test -d $$p ; then \
			$(APPLY_PATCHES) $(@D) $$p \*.patch || exit 1 ; \
		else \
			$(APPLY_PATCHES) $(@D) `dirname $$p` `basename $$p` || exit 1; \
		fi \
	done
endef

LINUX_POST_PATCH_HOOKS += LINUX_APPLY_LOCAL_PATCHES

# Older versions break on gcc 10+ because of redefined symbols
define LINUX_DROP_YYLLOC
	$(Q)grep -Z -l -r -E '^YYLTYPE yylloc;$$' $(@D) \
	|xargs -0 -r $(SED) '/^YYLTYPE yylloc;$$/d'
endef
LINUX_POST_PATCH_HOOKS += LINUX_DROP_YYLLOC

# Kernel version < 5.6 breaks if host-gcc version is >= 10 and
# 'yylloc' symbol is removed in previous hook, due to missing
# '%locations' bison directive in dtc-parser.y.  See:
# https://bugs.busybox.net/show_bug.cgi?id=14971
define LINUX_ADD_DTC_LOCATIONS
	$(Q)DTC_PARSER=$(@D)/scripts/dtc/dtc-parser.y; \
	if test -e "$${DTC_PARSER}" \
		&& ! grep -Eq '^%locations$$' "$${DTC_PARSER}" ; then \
		$(SED) '/^%{$$/i %locations' "$${DTC_PARSER}"; \
	fi
endef
LINUX_POST_PATCH_HOOKS += LINUX_ADD_DTC_LOCATIONS

# Older linux kernels use deprecated perl constructs in timeconst.pl
# that were removed for perl 5.22+ so it breaks on newer distributions
# Try a dry-run patch to see if this applies, if it does go ahead
define LINUX_TRY_PATCH_TIMECONST
	@if patch -p1 --dry-run -f -s -d $(@D) <$(LINUX_PKGDIR)/0001-timeconst.pl-Eliminate-Perl-warning.patch.conditional >/dev/null ; then \
		$(APPLY_PATCHES) $(@D) $(LINUX_PKGDIR) 0001-timeconst.pl-Eliminate-Perl-warning.patch.conditional ; \
	fi
endef
LINUX_POST_PATCH_HOOKS += LINUX_TRY_PATCH_TIMECONST

LINUX_KERNEL_CUSTOM_LOGO_PATH = $(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_LOGO_PATH))
ifneq ($(LINUX_KERNEL_CUSTOM_LOGO_PATH),)
LINUX_DEPENDENCIES += host-imagemagick
define LINUX_KERNEL_CUSTOM_LOGO_CONVERT
	$(HOST_DIR)/bin/convert $(LINUX_KERNEL_CUSTOM_LOGO_PATH) \
		-dither None -colors 224 -compress none \
		$(LINUX_DIR)/drivers/video/logo/logo_linux_clut224.ppm
endef
LINUX_PRE_BUILD_HOOKS += LINUX_KERNEL_CUSTOM_LOGO_CONVERT
endif

ifeq ($(BR2_LINUX_KERNEL_USE_DEFCONFIG),y)
LINUX_KCONFIG_DEFCONFIG = $(call qstrip,$(BR2_LINUX_KERNEL_DEFCONFIG))_defconfig
else ifeq ($(BR2_LINUX_KERNEL_USE_ARCH_DEFAULT_CONFIG),y)
ifeq ($(BR2_powerpc64le),y)
LINUX_KCONFIG_DEFCONFIG = ppc64le_defconfig
else ifeq ($(BR2_powerpc64),y)
LINUX_KCONFIG_DEFCONFIG = ppc64_defconfig
else ifeq ($(BR2_powerpc),y)
LINUX_KCONFIG_DEFCONFIG = ppc_defconfig
else ifeq ($(BR2_arc750d)$(BR2_arc770d),y)
LINUX_KCONFIG_DEFCONFIG = axs101_defconfig
else
LINUX_KCONFIG_DEFCONFIG = defconfig
endif
else ifeq ($(BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG),y)
LINUX_KCONFIG_FILE = $(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE))
endif
LINUX_KCONFIG_FRAGMENT_FILES = $(call qstrip,$(BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES))
LINUX_KCONFIG_EDITORS = menuconfig xconfig gconfig nconfig

# LINUX_MAKE_FLAGS overrides HOSTCC to allow the kernel build to find
# our host-openssl and host-libelf. However, this triggers a bug in
# the kconfig build script that causes it to build with
# /usr/include/ncurses.h (which is typically wchar) but link with
# $(HOST_DIR)/lib/libncurses.so (which is not).  We don't actually
# need any host-package for kconfig, so remove the HOSTCC override
# again. In addition, even though linux depends on the toolchain and
# therefore host-ccache would be ready, we use HOSTCC_NOCCACHE for
# consistency with other kconfig packages.
LINUX_KCONFIG_OPTS = $(LINUX_MAKE_FLAGS) HOSTCC="$(HOSTCC_NOCCACHE)"

# If no package has yet set it, set it from the Kconfig option
LINUX_NEEDS_MODULES ?= $(BR2_LINUX_NEEDS_MODULES)

# Make sure the Linux kernel is built with the right endianness. Not
# all architectures support
# CONFIG_CPU_BIG_ENDIAN/CONFIG_CPU_LITTLE_ENDIAN in Linux, but the
# option will be thrown away and ignored if it doesn't exist.
ifeq ($(BR2_ENDIAN),"BIG")
define LINUX_FIXUP_CONFIG_ENDIANNESS
	$(call KCONFIG_ENABLE_OPT,CONFIG_CPU_BIG_ENDIAN)
endef
else
define LINUX_FIXUP_CONFIG_ENDIANNESS
	$(call KCONFIG_ENABLE_OPT,CONFIG_CPU_LITTLE_ENDIAN)
endef
endif

# As the kernel gets compiled before root filesystems are
# built, we create a fake cpio file. It'll be
# replaced later by the real cpio archive, and the kernel will be
# rebuilt using the linux-rebuild-with-initramfs target.
ifeq ($(BR2_TARGET_ROOTFS_INITRAMFS),y)
define LINUX_KCONFIG_FIXUP_CMDS_ROOTFS_CPIO
	@mkdir -p $(BINARIES_DIR)
	$(Q)touch $(BINARIES_DIR)/rootfs.cpio
	$(call KCONFIG_SET_OPT,CONFIG_INITRAMFS_SOURCE,"$${BR_BINARIES_DIR}/rootfs.cpio")
	$(call KCONFIG_SET_OPT,CONFIG_INITRAMFS_ROOT_UID,0)
	$(call KCONFIG_SET_OPT,CONFIG_INITRAMFS_ROOT_GID,0)
endef
endif

define LINUX_KCONFIG_FIXUP_CMDS
	@$(call MESSAGE,"Updating kernel config with fixups")
	$(if $(LINUX_NEEDS_MODULES),
		$(call KCONFIG_ENABLE_OPT,CONFIG_MODULES))
	$(call KCONFIG_ENABLE_OPT,$(strip $(LINUX_COMPRESSION_OPT_y)))
	$(foreach opt, $(LINUX_COMPRESSION_OPT_),
		$(call KCONFIG_DISABLE_OPT,$(opt))
	)
	$(LINUX_FIXUP_CONFIG_ENDIANNESS)
	$(LINUX_FIXUP_CONFIG_PAHOLE_CHECK)
	$(if $(BR2_arm)$(BR2_armeb),
		$(call KCONFIG_ENABLE_OPT,CONFIG_AEABI))
	$(if $(BR2_powerpc)$(BR2_powerpc64)$(BR2_powerpc64le),
		$(call KCONFIG_ENABLE_OPT,CONFIG_PPC_DISABLE_WERROR))
	$(if $(BR2_ARC_PAGE_SIZE_4K),
		$(call KCONFIG_ENABLE_OPT,CONFIG_ARC_PAGE_SIZE_4K)
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARC_PAGE_SIZE_8K)
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARC_PAGE_SIZE_16K))
	$(if $(BR2_ARC_PAGE_SIZE_8K),
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARC_PAGE_SIZE_4K)
		$(call KCONFIG_ENABLE_OPT,CONFIG_ARC_PAGE_SIZE_8K)
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARC_PAGE_SIZE_16K))
	$(if $(BR2_ARC_PAGE_SIZE_16K),
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARC_PAGE_SIZE_4K)
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARC_PAGE_SIZE_8K)
		$(call KCONFIG_ENABLE_OPT,CONFIG_ARC_PAGE_SIZE_16K))
	$(if $(BR2_ARM64_PAGE_SIZE_4K),
		$(call KCONFIG_ENABLE_OPT,CONFIG_ARM64_4K_PAGES)
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARM64_16K_PAGES)
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARM64_64K_PAGES))
	$(if $(BR2_ARM64_PAGE_SIZE_16K),
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARM64_4K_PAGES)
		$(call KCONFIG_ENABLE_OPT,CONFIG_ARM64_16K_PAGES)
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARM64_64K_PAGES))
	$(if $(BR2_ARM64_PAGE_SIZE_64K),
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARM64_4K_PAGES)
		$(call KCONFIG_DISABLE_OPT,CONFIG_ARM64_16K_PAGES)
		$(call KCONFIG_ENABLE_OPT,CONFIG_ARM64_64K_PAGES))
	$(if $(BR2_TARGET_ROOTFS_CPIO),
		$(call KCONFIG_ENABLE_OPT,CONFIG_BLK_DEV_INITRD))
	$(LINUX_KCONFIG_FIXUP_CMDS_ROOTFS_CPIO)
	$(if $(BR2_ROOTFS_DEVICE_CREATION_STATIC),,
		$(call KCONFIG_ENABLE_OPT,CONFIG_DEVTMPFS)
		$(call KCONFIG_ENABLE_OPT,CONFIG_DEVTMPFS_MOUNT))
	$(if $(BR2_ROOTFS_DEVICE_CREATION_DYNAMIC_EUDEV),
		$(call KCONFIG_ENABLE_OPT,CONFIG_INOTIFY_USER))
	$(if $(BR2_ROOTFS_DEVICE_CREATION_DYNAMIC_MDEV),
		$(call KCONFIG_ENABLE_OPT,CONFIG_NET))
	$(if $(BR2_LINUX_KERNEL_APPENDED_DTB),
		$(call KCONFIG_ENABLE_OPT,CONFIG_ARM_APPENDED_DTB))
	$(if $(LINUX_KERNEL_CUSTOM_LOGO_PATH),
		$(call KCONFIG_ENABLE_OPT,CONFIG_FB)
		$(call KCONFIG_ENABLE_OPT,CONFIG_LOGO)
		$(call KCONFIG_ENABLE_OPT,CONFIG_LOGO_LINUX_CLUT224))
	$(call KCONFIG_DISABLE_OPT,CONFIG_GCC_PLUGINS)
	$(call KCONFIG_DISABLE_OPT,CONFIG_WERROR)
	$(PACKAGES_LINUX_CONFIG_FIXUPS)
endef

ifeq ($(BR2_LINUX_KERNEL_DTS_SUPPORT),y)
# Starting with 4.17, the generated dtc parser code is no longer
# shipped with the kernel sources, so we need flex and bison. For
# reproducibility, we use our owns rather than the host ones.
LINUX_DEPENDENCIES += host-bison host-flex

ifeq ($(BR2_LINUX_KERNEL_DTB_IS_SELF_BUILT),)
define LINUX_BUILD_DTB
	$(LINUX_MAKE_ENV) $(BR2_MAKE) $(LINUX_MAKE_FLAGS) -C $(@D) $(LINUX_DTBS)
endef
ifeq ($(BR2_LINUX_KERNEL_APPENDED_DTB),)
define LINUX_INSTALL_DTB
	# dtbs moved from arch/<ARCH>/boot to arch/<ARCH>/boot/dts since 3.8-rc1
	$(foreach dtb,$(LINUX_DTBS), \
		install -D \
			$(or $(wildcard $(LINUX_ARCH_PATH)/boot/dts/$(dtb)),$(LINUX_ARCH_PATH)/boot/$(dtb)) \
			$(1)/$(if $(BR2_LINUX_KERNEL_DTB_KEEP_DIRNAME),$(dtb),$(notdir $(dtb)))
	)
endef
endif # BR2_LINUX_KERNEL_APPENDED_DTB
endif # BR2_LINUX_KERNEL_DTB_IS_SELF_BUILT
endif # BR2_LINUX_KERNEL_DTS_SUPPORT

ifeq ($(BR2_LINUX_KERNEL_APPENDED_DTB),y)
# dtbs moved from arch/$ARCH/boot to arch/$ARCH/boot/dts since 3.8-rc1
define LINUX_APPEND_DTB
	(cd $(LINUX_ARCH_PATH)/boot; \
		for dtb in $(LINUX_DTS_NAME); do \
			if test -e $${dtb}.dtb ; then \
				dtbpath=$${dtb}.dtb ; \
			else \
				dtbpath=dts/$${dtb}.dtb ; \
			fi ; \
			cat zImage $${dtbpath} > zImage.$$(basename $${dtb}) || exit 1; \
		done)
endef
ifeq ($(BR2_LINUX_KERNEL_APPENDED_UIMAGE),y)
# We need to generate a new u-boot image that takes into
# account the extra-size added by the device tree at the end
# of the image. To do so, we first need to retrieve both load
# address and entry point for the kernel from the already
# generate uboot image before using mkimage -l.
LINUX_APPEND_DTB += ; \
	MKIMAGE_ARGS=`$(MKIMAGE) -l $(LINUX_IMAGE_PATH) |\
	sed -n -e 's/Image Name:[ ]*\(.*\)/-n \1/p' -e 's/Load Address:/-a/p' -e 's/Entry Point:/-e/p'`; \
	for dtb in $(LINUX_DTS_NAME); do \
		$(MKIMAGE) -A $(MKIMAGE_ARCH) -O linux \
			-T kernel -C none $${MKIMAGE_ARGS} \
			-d $(LINUX_ARCH_PATH)/boot/zImage.$${dtb} $(LINUX_IMAGE_PATH).$${dtb}; \
	done
endif
endif

# Compilation. We make sure the kernel gets rebuilt when the
# configuration has changed. We call the 'all' and
# '$(LINUX_TARGET_NAME)' targets separately because calling them in
# the same $(BR2_MAKE) invocation has shown to cause parallel build
# issues.
# The call to disable gcc-plugins is a stop-gap measure:
#   https://lore.kernel.org/buildroot/20200512095550.GW12536@scaer
define LINUX_BUILD_CMDS
	$(call KCONFIG_DISABLE_OPT,CONFIG_GCC_PLUGINS)
	$(foreach dts,$(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_DTS_PATH)), \
		cp -f $(dts) $(LINUX_ARCH_PATH)/boot/dts/
	)
	$(LINUX_COPY_CUSTOM_DTS_FILES)
	$(LINUX_COPY_CUSTOM_APPEND_FILES)
	$(LINUX_MAKE_ENV) $(BR2_MAKE) $(LINUX_MAKE_FLAGS) -C $(@D) all
	$(LINUX_MAKE_ENV) $(BR2_MAKE) $(LINUX_MAKE_FLAGS) -C $(@D) $(LINUX_TARGET_NAME)
	$(LINUX_BUILD_DTB)
	$(LINUX_APPEND_DTB)
endef

ifeq ($(BR2_LINUX_KERNEL_APPENDED_DTB),y)
# When a DTB was appended, install the potential several images with
# appended DTBs.
define LINUX_INSTALL_IMAGE
	mkdir -p $(1)
	cp $(LINUX_ARCH_PATH)/boot/$(LINUX_IMAGE_NAME).* $(1)
endef
else
# Otherwise, just install the unique image generated by the kernel
# build process.
define LINUX_INSTALL_IMAGE
	$(INSTALL) -m 0644 -D $(LINUX_IMAGE_PATH) $(1)/$(notdir $(LINUX_IMAGE_NAME))
endef
endif

ifeq ($(BR2_LINUX_KERNEL_INSTALL_TARGET),y)
define LINUX_INSTALL_KERNEL_IMAGE_TO_TARGET
	$(call LINUX_INSTALL_IMAGE,$(TARGET_DIR)/boot)
	$(call LINUX_INSTALL_DTB,$(TARGET_DIR)/boot)
endef
endif

define LINUX_INSTALL_HOST_TOOLS
	# Installing dtc (device tree compiler) as host tool, if selected
	if grep -q "CONFIG_DTC=y" $(@D)/.config; then \
		$(INSTALL) -D -m 0755 $(@D)/scripts/dtc/dtc $(HOST_DIR)/bin/linux-dtc ; \
		$(if $(BR2_PACKAGE_HOST_DTC),,ln -sf linux-dtc $(HOST_DIR)/bin/dtc;) \
	fi
endef

define LINUX_INSTALL_IMAGES_CMDS
	$(call LINUX_INSTALL_IMAGE,$(BINARIES_DIR))
	$(call LINUX_INSTALL_DTB,$(BINARIES_DIR))
endef

ifeq ($(BR2_STRIP_strip),y)
LINUX_MAKE_FLAGS += INSTALL_MOD_STRIP=1
endif

define LINUX_INSTALL_TARGET_CMDS
	$(LINUX_INSTALL_KERNEL_IMAGE_TO_TARGET)
	# Install modules and remove symbolic links pointing to build
	# directories, not relevant on the target
	@if grep -q "CONFIG_MODULES=y" $(@D)/.config; then \
		$(LINUX_MAKE_ENV) $(BR2_MAKE1) $(LINUX_MAKE_FLAGS) -C $(@D) modules_install; \
		rm -f $(TARGET_DIR)/lib/modules/$(LINUX_VERSION_PROBED)/build ; \
		rm -f $(TARGET_DIR)/lib/modules/$(LINUX_VERSION_PROBED)/source ; \
	fi
	$(LINUX_INSTALL_HOST_TOOLS)
endef

# Run depmod in a target-finalize hook, to encompass modules installed by
# packages.
define LINUX_RUN_DEPMOD
	if test -d $(TARGET_DIR)/lib/modules/$(LINUX_VERSION_PROBED) \
		&& grep -q "CONFIG_MODULES=y" $(LINUX_DIR)/.config; then \
		$(HOST_DIR)/sbin/depmod -a -b $(TARGET_DIR) $(LINUX_VERSION_PROBED); \
	fi
endef
LINUX_TARGET_FINALIZE_HOOKS += LINUX_RUN_DEPMOD

# Include all our extensions.
#
# Note: our package infrastructure uses the full-path of the last-scanned
# Makefile to determine what package we're currently defining, using the
# last directory component in the path. Additionally, the full path of
# the package directory is also stored in _PKGDIR (e.g. to find patches)
#
# As such, including other Makefiles, like below, before we call one of
# the *-package macros usually doesn't work.
#
# However, by including the in-tree extensions after the ones from the
# br2-external trees, we're back to the situation where the last Makefile
# scanned *is* included from the correct directory.
#
# NOTE: this is very fragile, and extra care must be taken to ensure that
# we always end up with an in-tree included file. That's mostly OK, because
# we do have in-tree linux-extensions.
#
include $(sort $(wildcard $(foreach ext,$(BR2_EXTERNAL_DIRS), \
	$(ext)/linux/linux-ext-*.mk)))
include $(sort $(wildcard linux/linux-ext-*.mk))

LINUX_PATCH_DEPENDENCIES += $(foreach ext,$(LINUX_EXTENSIONS),\
	$(if $(BR2_LINUX_KERNEL_EXT_$(call UPPERCASE,$(ext))),$(ext)))

LINUX_PRE_PATCH_HOOKS += $(foreach ext,$(LINUX_EXTENSIONS),\
	$(if $(BR2_LINUX_KERNEL_EXT_$(call UPPERCASE,$(ext))),\
		$(call UPPERCASE,$(ext))_PREPARE_KERNEL))

# Checks to give errors that the user can understand

# When a custom repository has been set, check for the repository version
ifeq ($(BR2_LINUX_KERNEL_CUSTOM_SVN)$(BR2_LINUX_KERNEL_CUSTOM_GIT)$(BR2_LINUX_KERNEL_CUSTOM_HG),y)
ifeq ($(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_REPO_VERSION)),)
$(error No custom repository version set. Check your BR2_LINUX_KERNEL_CUSTOM_REPO_VERSION setting)
endif
ifeq ($(call qstrip,$(BR2_LINUX_KERNEL_CUSTOM_REPO_URL)),)
$(error No custom repo URL set. Check your BR2_LINUX_KERNEL_CUSTOM_REPO_URL setting)
endif
endif

ifeq ($(BR_BUILDING),y)

ifeq ($(BR2_LINUX_KERNEL_CUSTOM_VERSION),y)
ifeq ($(LINUX_VERSION),)
$(error No custom kernel version set. Check your BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE setting)
endif
endif

ifeq ($(BR2_LINUX_KERNEL_USE_DEFCONFIG),y)
# We must use the user-supplied kconfig value, because
# LINUX_KCONFIG_DEFCONFIG will at least contain the
# trailing _defconfig
ifeq ($(call qstrip,$(BR2_LINUX_KERNEL_DEFCONFIG)),)
$(error No kernel defconfig name specified, check your BR2_LINUX_KERNEL_DEFCONFIG setting)
endif
endif

ifeq ($(BR2_LINUX_KERNEL_USE_CUSTOM_CONFIG),y)
ifeq ($(LINUX_KCONFIG_FILE),)
$(error No kernel configuration file specified, check your BR2_LINUX_KERNEL_CUSTOM_CONFIG_FILE setting)
endif
endif

ifeq ($(BR2_LINUX_KERNEL_DTS_SUPPORT):$(strip $(LINUX_DTS_NAME)),y:)
$(error No kernel device tree source specified, check your \
	BR2_LINUX_KERNEL_INTREE_DTS_NAME / BR2_LINUX_KERNEL_CUSTOM_DTS_PATH settings)
endif

ifeq ($(BR2_LINUX_KERNEL_IMAGE_TARGET_CUSTOM):$(call qstrip,$(BR2_LINUX_KERNEL_IMAGE_TARGET_NAME)),y:)
$(error No image name specified in BR2_LINUX_KERNEL_IMAGE_TARGET_NAME despite BR2_LINUX_KERNEL_IMAGE_TARGET_CUSTOM=y)
endif

endif # BR_BUILDING

$(eval $(kconfig-package))

# Support for rebuilding the kernel after the cpio archive has
# been generated.
.PHONY: linux-rebuild-with-initramfs
linux-rebuild-with-initramfs: $(LINUX_DIR)/.stamp_target_installed
linux-rebuild-with-initramfs: $(LINUX_DIR)/.stamp_images_installed
linux-rebuild-with-initramfs: rootfs-cpio
linux-rebuild-with-initramfs:
	@$(call MESSAGE,"Rebuilding kernel with initramfs")
	# Build the kernel.
	$(LINUX_MAKE_ENV) $(BR2_MAKE) $(LINUX_MAKE_FLAGS) -C $(LINUX_DIR) $(LINUX_TARGET_NAME)
	$(LINUX_APPEND_DTB)
	# Copy the kernel image(s) to its(their) final destination
	$(call LINUX_INSTALL_IMAGE,$(BINARIES_DIR))
	# If there is a .ub file copy it to the final destination
	test ! -f $(LINUX_IMAGE_PATH).ub || cp $(LINUX_IMAGE_PATH).ub $(BINARIES_DIR)
