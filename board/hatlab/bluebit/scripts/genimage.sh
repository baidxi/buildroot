#!/bin/bash
set -e
SELFDIR=`dirname \`realpath ${0}\``

[ $# -eq 2 ] || {
    echo "SYNTAX: $0 <u-boot-with-spl image> <genimage.cfg>"
    echo "Given: $@"
    exit 1
}

${SELFDIR}/mknanduboot.sh ${1}/${2} ${1}/u-boot-sunxi-with-nand-spl.bin
support/scripts/genimage.sh ${1} -c board/hatlab/bluebit/genimage-sdcard.cfg
