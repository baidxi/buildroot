#!/bin/sh

# genimage will need to find the extlinux.conf
# in the binaries directory

BOARD_DIR="$(dirname "$0")"

install -m 0644 -D "${BOARD_DIR}/extlinux-sdcard.conf" "${BINARIES_DIR}/extlinux-sdcard.conf"
install -m 0644 -D "${BOARD_DIR}/extlinux-emmc.conf" "${BINARIES_DIR}/extlinux-emmc.conf"
install -m 0644 -D "${BOARD_DIR}/uboot.env" "${BINARIES_DIR}/uboot.env"