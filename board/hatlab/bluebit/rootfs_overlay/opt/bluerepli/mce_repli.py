#!/usr/bin/env python3

# Released as open source by NCC Group Plc - http://www.nccgroup.com/
#
# Developed by Sultan Qasim Khan, Sultan.QasimKhan@nccgroup.trust
#
# http://www.github.com/nccgroup/nOBEX
#
# Released under GPLv3, a full copy of which can be found in COPYING.

import os, sys
from xml.etree import ElementTree
from bluerepli.nOBEX import headers
from bluerepli.nOBEX.common import OBEXError
from bluerepli.nOBEX.xml_helper import parse_xml

from bluerepli.nOBEX.client import Client
from bluerepli.nOBEX.bluez_helper import find_service
from bluerepli.nOBEX.bluez_helper import SDPException
from bluerepli.nOBEX import headers


class MAPClient(Client):
    '''MAS (Message Access Server) is a Service Class of MAP (Message Access Profile)'''
    # 该 UUID 在 SDP 中无效，仅在 OBEX 中使用。
    MAS_UUID = b'\xbb\x58\x2b\x40\x42\x0c\x11\xdb\xb0\xde\x08\x00\x20\x0c\x9a\x66'

    def __init__(self, address, port=None):
        if port is None:
            try:
                port = find_service("map", address)
            except SDPException as e:
                if str(e) == "sdptool search returned 255":
                    print("[\x1B[1;31mFailed\x1B[0m] Maybe target host is down.")
                sys.exit(1)
        super().__init__(address, port)


    def connect(self):
        '''Send OBEX connect request'''
        # OBEX connect request 会携带 target header，从而指定连接的 service。
        # 其中 header 的概念和 HTTP 中 header 的概念很类似。
        super().connect(header_list=[headers.Target(self.MAS_UUID)])

        #print(self.listdir())


    def push_message(self, folder:str, bmsg:bytes):
        # Charset tag in Application Parameters header is required
        charset_tagid = b'\x14'
        charset_len = b'\x01'
        charset = b'\x01' # UTF-8

        self.put(name=folder, file_data=bmsg, header_list=[headers.Type(
            b'x-bt/message'), headers.App_Parameters(charset_tagid \
            + charset_len + charset)])


    def get_ver(self):
        pass

    # def list_folder(self, ):
    #     pass


class MCERepli(MAPClient):
    '''Message Client Equipment Replicant'''
    def __init__(self, raddr:str, iface='hci0'):
        super().__init__(raddr)
        self.raddr = raddr
        self.iface = iface

        self.connect()


    def send_msg(self, msg:str, rphone:str):
        '''Send a short message through MSE.'''
        self.setpath('')
        self.setpath('telecom')
        self.setpath('msg')
        length = 11 + len(msg)*2 + 2 + 9
        #print(length)
        bmsg = b'BEGIN:BMSG\r\n' \
        + b'VERSION:1.0\r\n' \
        + b'STATUS:READ\r\n' \
        + b'TYPE:SMS_GSM\r\n' \
        + b'FOLDER:telecom/msg/sent\r\n' \
        + b'BEGIN:BENV\r\n' \
        + b'BEGIN:VCARD\r\n' \
        + b'VERSION:2.1\r\n' \
        + b'N:test\r\n' \
        + b'TEL:' + rphone.encode() + b'\r\n' \
        + b'END:VCARD\r\n' \
        + b'BEGIN:BBODY\r\n' \
        + b'CHARSET:UTF-8\r\n' \
        + b'LENGTH:'+ str(length).encode() + b'\r\n' \
        + b'BEGIN:MSG\r\n' \
        + msg.encode() + b'\r\n' \
        + b'END:MSG\r\n' \
        + b'END:BBODY\r\n' \
        + b'END:BENV\r\n' \
        + b'END:BMSG'
        #print('[DEBUG]', bmsg)
        #+ ''.join([('%02X'%b) for b in msg.encode()]).encode() + b'\r\n' \
        self.push_message('outbox', bmsg)


    def dump_msg(self, store_dir='.'):
        dst_dir = os.path.abspath(store_dir) + "/"

        self.setpath("telecom")
        self.setpath("msg")

        # dump every folder
        dirs, files = self.listdir()
        print()
        #print('[DEBUG] dirs:', dirs)
        #print('[DEBUG] files:', files)
        for d in dirs:
            # if d == 'inbox':
            #     continue
            self.__dump_dir(d, dst_dir + "telecom/msg/" + d)

        self.disconnect()


    def __dump_dir(self, src_path, dst_path):
        src_path = src_path.strip("/")

        # Access the list of vcards in the directory
        hdrs, cards = self.get(src_path, header_list=[headers.Type(b'x-bt/MAP-msg-listing')])

        # folder doesn't exist, iPhone behaves this way
        if len(cards) == 0:
            return

        os.makedirs(dst_path, exist_ok=True)

        # Parse the XML response to the previous request.
        # Extract a list of file names in the directory
        names = []
        root = parse_xml(cards)
        self.__dump_xml(root, "/".join([dst_path, "mlisting.xml"]))
        for card in root.findall("msg"):
            names.append(card.attrib["handle"])

        self.setpath(src_path)

        # get all the files
        for name in names:
            self.__get_file(name, "/".join([dst_path, name]), folder_name=src_path)

        # return to the root directory
        depth = len([f for f in src_path.split("/") if len(f)])
        for i in range(depth):
            self.setpath(to_parent=True)


    def __get_file(self, src_path, dst_path, verbose=True, folder_name=None):
        if verbose:
            if folder_name is not None:
                print("Fetching %s/%s" % (folder_name, src_path))
            else:
                print("Fetching %s" % src_path)

        # include attachments, use UTF-8 encoding
        req_hdrs = [headers.Type(b'x-bt/message'),
                    headers.App_Parameters(b'\x0A\x01\x01\x14\x01\x01')]
        hdrs, card = self.get(src_path, header_list=req_hdrs)
        with open(dst_path, 'wb') as f:
            f.write(card)


    def __dump_xml(self, element, file_name):
        fd = open(file_name, 'wb')
        fd.write(b'<?xml version="1.0" encoding="utf-8" standalone="yes" ?>\n')
        fd.write(ElementTree.tostring(element, 'utf-8'))
        fd.close()


if __name__ == "__main__":
    pass
