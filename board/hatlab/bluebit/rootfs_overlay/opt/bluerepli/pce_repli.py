#!/usr/bin/env python3

import time
import sys
import os

from xml.etree import ElementTree
from xml.dom import minidom

from bluerepli.nOBEX.xml_helper import parse_xml
from bluerepli.nOBEX.client import Client
from bluerepli.nOBEX.bluez_helper import find_service
from bluerepli.nOBEX import bluez_helper
from bluerepli.nOBEX import headers
from bluerepli.nOBEX.common import OBEXError


class PBAPClient(Client):
    # 该 UUID 在 SDP 中无效，仅在 OBEX 中使用，用于标识 PSE
    PBAP_UUID = b'\x79\x61\x35\xf0\xf0\xc5\x11\xd8\x09\x66\x08\x00\x20\x0c\x9a\x66'

    def __init__(self, addr, port=None):
        '''The port is RFCOMM channel.'''
        #self.address = addr
        if port is None:
            # 执行 `sdptool search --xml --bdaddr=<addr> pbap`，
            # 并解析返回的 xml 从而找到动态分配的 port
            port = find_service("pbap", addr)
        super().__init__(addr, port)


    def connect(self):
        '''构造 OBEX 协议的 headers，并发起连接'''
        super().connect(header_list=[headers.Target(self.PBAP_UUID)])


    def pull_vcard_listing(self, name='/telecom/pb', parse=True):
        '''PBAP does't have `x-obex/folder-listing` object like MAP, but have 
        `x-bt/vcard-listing` object.
        name     Name header, name of the folder
        parse    Whether Parse xml
        '''
        hdrs, data = self.get(name, header_list=[headers.Type(
            b"x-bt/vcard-listing")])

        if not parse:
            return data

        # tree = parse_xml(data)
        # folders = []
        # files = []
        # for e in tree:
        #     if e.tag == "folder":
        #         folders.append(e.attrib["name"])
        #     elif e.tag == "file":
        #         files.append(e.attrib["name"])
        #     elif e.tag == "parent-folder":
        #         pass # ignore it
        #     else:
        #         sys.stderr.write("Unknown listing element %s\n" % e.tag)

        # return folders, files



    # def listen(self):
    #     port = bluez_helper.get_available_port(self.address)

    #     socket = bluez_helper.BluetoothSocket()
    #     print('[Debug] self.address =', self.address)
    #     print('[Debug] port =', port)
    #     socket.bind((self.address, port))
    #     socket.listen(1)

    #     print("Starting server for %s on port %i" % socket.getsockname())
    #     bluez_helper.advertise_service(name, port)

    #     return socket


class PCERepli(PBAPClient):
    '''Phonebook Client Equipment Replicant'''
    def __init__(self, raddr, iface='hci0'):
        super().__init__(raddr)
        self.raddr = raddr
        self.iface = iface

        self.connect()
        # self.setpath('telecom/cch')
        # self.setpath('cch')
        #self.setpath('nondir')


    def dump_pb(self, store_dir='./pbap_root', sim=''):
        '''
        store_dir    最后一个字符不能为 "/"
        sim           SIM1/ SIM2/ ... SIMN/ 
        '''
        if store_dir is None:
            store_dir = './pbap_root'

        if self.raddr is None:
            print('[ERROR] Remote address is None.')
            sys.exit(1)

        prefix = sim

        if sim:
            prefix = "SIM1/"
        else:
            prefix = ""

        # if self.link_key is not None:
        #     hci_write_stored_link_key(
        #         [self.raddr], [self.link_key], self.iface
        #     )
        # 在调用上面三个 HIC command 后可能需要延时足够时间再执行
        # `pbapclient.py`，否则会遭遇如下错误：
        #     ConnectionAbortedError: [Errno 103] Software caused connection abort
        #time.sleep(2)
        store_dir = os.path.abspath(store_dir) + "/"

        # dump the phone book and other folders
        self.__dump_dir("telecom/pb", store_dir+"telecom/pb")
        self.__dump_dir("telecom/ich", store_dir+"telecom/ich")
        self.__dump_dir("telecom/och", store_dir+"telecom/och")
        self.__dump_dir("telecom/mch", store_dir+"telecom/mch")
        self.__dump_dir("telecom/cch", store_dir+"telecom/cch")

        self.__dump_dir("SIM1/telecom/pb", store_dir+"SIM1/telecom/pb")
        self.__dump_dir("SIM1/telecom/ich", store_dir+"SIM1/telecom/ich")
        self.__dump_dir("SIM1/telecom/och", store_dir+"SIM1/telecom/och")
        self.__dump_dir("SIM1/telecom/mch", store_dir+"SIM1/telecom/mch")
        self.__dump_dir("SIM1/telecom/cch", store_dir+"SIM1/telecom/cch")

        # dump the combined vcards
        self.setpath("telecom")
        self.__get_file("pb.vcf", store_dir+"telecom/pb.vcf",
                folder_name=prefix+"telecom", book=True)
        self.__get_file("ich.vcf", store_dir+"telecom/ich.vcf",
                folder_name=prefix+"telecom", book=True)
        self.__get_file("och.vcf", store_dir+"telecom/och.vcf",
                folder_name=prefix+"telecom", book=True)
        self.__get_file("mch.vcf", store_dir+"telecom/mch.vcf",
                folder_name=prefix+"telecom", book=True)
        self.__get_file("cch.vcf", store_dir+"telecom/cch.vcf",
                folder_name=prefix+"telecom", book=True)

        self.setpath("SIM1/telecom")
        self.__get_file("pb.vcf", store_dir+"SIM1/telecom/pb.vcf",
                folder_name=prefix+"telecom", book=True)
        self.__get_file("ich.vcf", store_dir+"SIM1/telecom/ich.vcf",
                folder_name=prefix+"telecom", book=True)
        self.__get_file("och.vcf", store_dir+"SIM1/telecom/och.vcf",
                folder_name=prefix+"telecom", book=True)
        self.__get_file("mch.vcf", store_dir+"SIM1/telecom/mch.vcf",
                folder_name=prefix+"telecom", book=True)
        self.__get_file("cch.vcf", store_dir+"SIM1/telecom/cch.vcf",
                folder_name=prefix+"telecom", book=True)

        self.disconnect()


    def __dump_xml(self, element, file_name):
        rough_string = ElementTree.tostring(element, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_string = reparsed.toprettyxml()
        with open(file_name, 'w') as fd:
            fd.write('<?xml version="1.0"?>\n<!DOCTYPE vcard-listing SYSTEM "vcard-listing.dtd">\n')
            fd.write(pretty_string[23:]) # skip xml declaration


    def __get_file(self, src_path, dest_path, verbose=True, folder_name=None, book=False):
        if verbose:
            if folder_name is not None:
                print("Fetching %s/%s" % (folder_name, src_path))
            else:
                print("Fetching %s" % src_path)

        if book:
            mimetype = b'x-bt/phonebook'
        else:
            mimetype = b'x-bt/vcard'

        hdrs, card = self.get(src_path, header_list=[headers.Type(mimetype)])
        with open(dest_path, 'wb') as f:
            f.write(card)


    def __dump_dir(self, src_path, dest_path):
        src_path = src_path.strip("/")

        # since some people may still be holding back progress with Python 2, I'll support
        # them for now and not use the Python 3 exist_ok option :(
        try:
            os.makedirs(dest_path)
        except OSError as e:
            pass

        # Access the list of vcards in the directory
        hdrs, cards = self.get(src_path, header_list=[headers.Type(b'x-bt/vcard-listing')])

        if len(cards) == 0:
            print("[INFO] %s is empty, skipping" % src_path)
            return

        # Parse the XML response to the previous request.
        # Extract a list of file names in the directory
        names = []
        root = parse_xml(cards)
        self.__dump_xml(root, "/".join([dest_path, "listing.xml"]))
        for card in root.findall("card"):
            names.append(card.attrib["handle"])

        self.setpath(src_path)

        # get all the files
        for name in names:
            fname = "/".join([dest_path, name])
            try:
                self.__get_file(name, fname, folder_name=src_path)
            except OBEXError as e:
                print("Failed to fetch", fname, e)

        # return to the root directory
        depth = len([f for f in src_path.split("/") if len(f)])
        for i in range(depth):
            self.setpath(to_parent=True)


if __name__ == "__main__":
    pass
