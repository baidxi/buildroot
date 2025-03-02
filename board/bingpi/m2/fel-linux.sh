#!/bin/bash

sunxi-fel -p uboot output/images/u-boot-sunxi-with-spl.bin write 0x41000000 output/images/zImage write 0x41800000 output/images/sun8i-t113s-mangopi-mq-r-t113.dtb write 0x41C00000 output/images/rootfs.cpio.uboot

# booti 0x41000000 0x41800000 0x41c00000
