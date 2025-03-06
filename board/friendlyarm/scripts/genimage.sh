#!/bin/bash
set -e
STARTDIR=`pwd`
SELFDIR=`dirname \`realpath ${0}\``
MKIMAGE="${HOST_DIR}/bin/mkimage"
IMAGE_ITS="kernel.its"
OUTPUT_NAME="kernel.itb"

[ $# -eq 2 ] || {
    echo "SYNTAX: $0 <output dir> <u-boot-with-spl image>"
    echo "Given: $@"
    exit 1
}

cp board/friendlyarm/mini210s/kernel.its "${BINARIES_DIR}"
cd ${BINARIES_DIR}
${MKIMAGE} -f ${IMAGE_ITS} ${OUTPUT_NAME}
rm ${IMAGE_ITS}

cd ${STARTDIR}/

support/scripts/genimage.sh ${1} -c board/friendlyarm/mini210s/genimage-sdcard.cfg
