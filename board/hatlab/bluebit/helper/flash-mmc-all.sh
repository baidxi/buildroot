#!/bin/bash
MMC=/dev/sdb
sudo umount "$MMC"1 "$MMC"2
sudo dd if=output/images/sysimage-sdcard.img of="$MMC" bs=4k
sync
