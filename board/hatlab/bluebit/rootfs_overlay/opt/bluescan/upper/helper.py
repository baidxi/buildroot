#!/usr/bin/env python3

import struct


def le_ram2str(bs:bytes) -> str:
    r"""将 RAM 中的 little-endian 数据转换为 str 形式的 16 进制数。"""
    s = '0x'
    for b in bs[::-1]:
        s += '%02X' % b

    return s


def str2ram_le(s:str) -> bytes:
    r"""将 str 形式的 16 进制数转换为 little-endian 的 RAM 数据。"""
    return bytes.fromhex(s[2:])[::-1]


def crc_init_ram_to_math(crc_init:bytes) -> str:
    s = '0x'
    for b in crc_init[::-1]:
        s += '%02X' % b

    return s


def extract_crc_init(pseudo_crc_init:bytes) -> str:
    s = '0x'

    crc_init = struct.unpack("<I", pseudo_crc_init)[0]
    crc_init &= 0x01FFFFFE
    crc_init <<= 7
    crc_init = int('{:0>32b}'.format(crc_init)[::-1], 2)
    #print("[Debug] crc_init =", crc_init)
    crc_init = struct.pack(">I", crc_init)
    #print("[Debug] crc_init =", crc_init)

    for b in crc_init[1:]:
        s += '%02X' % b
    
    return s


def hopseq2bytes(hop_seq:list):
    """将 int list 形式的 hop seq 转换为 bytes"""
    print("[Debug] hop_seq:", hop_seq)
    result = bytearray()
    for ch in hop_seq:
        #result.append(ch.to_bytes(1, 'little'))
        # bytearray 的 append 填写 int 而非 bytes
        result.append(ch)
    return bytes(result)


def test():
    # 0x7E5FF67C
    #     5FF67C
    # 0000 000 0 0101 1111 1111 0110 0111 110 0
    # 2FFB 3E00
    # 0010 1111 1111 1011 0011 1110 0000 0000
    #101111111110110011111000000000

    # 0000 0000 0111 1100 1101 1111 1111 0100

    pseudo_crc_init = b'\x7C\xF6\x5F\x7E'
    print("[Test] CRCInit =", extract_crc_init(pseudo_crc_init))

if __name__ == "__main__":
    test()
