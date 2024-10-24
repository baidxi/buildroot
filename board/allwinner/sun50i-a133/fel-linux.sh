#!/bin/bash

sunxi-fel -p uboot output/images/u-boot-sunxi-with-spl.bin write 0x40080000 output/images/Image write 0x4FA00000 output/images/sun50i-a133-rfb.dtb write 0x4FF00000 output/images/rootfs.cpio.uboot

# booti 0x40080000 0x4FF00000 0x4FA00000
