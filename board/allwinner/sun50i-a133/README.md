### 1、make allwinner_r818_dshanpi_defconfig or make allwinner_a133_rfb_defconfig
### ２、sunxi-fel uboot output/images/u-boot-sunxi-with-spl.bin
### 3、fastboot oem format
### 4、fastboot flash mmc1 output/images/flash.img
### 5、fastboot reboot

###
flash.img支持通过fastboot刷入emmc和dd到SD使用，无需转换。