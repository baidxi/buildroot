#!/bin/bash
rm ./output/images/*.dtb
make linux-clean-for-rebuild
make -j8
