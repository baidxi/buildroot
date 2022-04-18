#!/bin/bash
set -e
SELFDIR=`dirname \`realpath ${0}\``
MKIMAGE="${HOST_DIR}/bin/mkimage"
IMAGE_ITS="kernel.its"
OUTPUT_NAME="kernel.itb"

[ $# -eq 2 ] || {
    echo "SYNTAX: $0 <output image dir> <u-boot-with-spl image>"
    echo "Given: $@"
    exit 1
}

cp board/allwinner/generic/kernel.its "${BINARIES_DIR}"
cd "${BINARIES_DIR}"
"${MKIMAGE}" -f ${IMAGE_ITS} ${OUTPUT_NAME}
rm ${IMAGE_ITS}
cd "./../../"

board/allwinner/generic/scripts/mknanduboot.sh ${1}/${2} ${1}/u-boot-sunxi-with-nand-spl.bin
support/scripts/genimage.sh ${1} -c board/allwinner/generic/genimage-sdcard.cfg
support/scripts/genimage.sh ${1} -c board/allwinner/generic/genimage-nor.cfg
support/scripts/genimage.sh ${1} -c board/allwinner/generic/genimage-nand.cfg


# support/scripts/genimage.sh ${1} -c board/allwinner/generic/genimage-flasher.cfg
