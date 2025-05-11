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

cp board/jlc/tspi/kernel.its "${BINARIES_DIR}"
cd "${BINARIES_DIR}"
"${MKIMAGE}" -f ${IMAGE_ITS} ${OUTPUT_NAME}
rm ${IMAGE_ITS}
cd "./../../"

support/scripts/genimage.sh ${1} -c board/jlc/tspi/genimage.cfg


