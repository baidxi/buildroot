#!/bin/bash
# LicheePi Zero FEL boot script
# Memory layout (V3s has 64MB DDR at 0x40000000-0x44000000):
#   zImage size ~9.8MB (0x954228), ends at 0x41954228
#   0x41000000 - zImage (kernel)
#   0x41A00000 - DTB (~20KB)
#   0x41B00000 - rootfs.cpio.uboot (~7.4MB initramfs)

sunxi-fel -p uboot \
	output/images/u-boot-sunxi-with-spl.bin \
	write 0x41000000 output/images/zImage \
	write 0x41A00000 output/images/sun8i-v3s-licheepi-zero.dtb \
	write 0x41B00000 output/images/rootfs.cpio.uboot

echo ""
echo "Images loaded. At U-Boot prompt, run:"
echo "  bootz 0x41000000 0x41B00000 0x41A00000"
