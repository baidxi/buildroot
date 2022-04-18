#!/bin/bash

sunxi-fel -p uboot output/images/u-boot-sunxi-with-spl.bin write 0x41000000 output/images/zImage write 0x42000000 output/images/devicetree.dtb write 0x42400000 output/images/rootfs.cpio.uboot

# bootz 0x41000000 0x42400000 0x42000000
