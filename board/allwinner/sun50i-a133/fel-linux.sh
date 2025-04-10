#!/bin/bash

sunxi-fel -p uboot output/images/u-boot-sunxi-with-spl.bin write 0x41000000 output/images/Image write 0x42800000 output/images/sun50i-a133-rfb.dtb write 0x42C00000 output/images/rootfs.cpio.uboot

# booti 0x41000000 0x42c00000 0x42800000
