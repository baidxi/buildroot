#!/usr/bin/env python3

"""
reponses.py - Classes encapsulating OBEX responses.

Copyright (C) 2007 David Boddie <david@boddie.org.uk>

This file is part of the nOBEX Python package.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import socket
import time
import threading


import struct
from bluerepli.nOBEX.common import OBEX_Version, Message, MessageHandler

class Response(Message):
    # Define the additional format information required by responses.
    # Subclasses should redefine this when required to ensure that their
    # minimum lengths are calculated correctly.
    format = ""

    def __init__(self, data = (), header_data = ()):
        Message.__init__(self, data, header_data)
        self.minimum_length = self.length(Message.format + self.format)

class FailureResponse(Response):
    pass

class Continue(Response):
    code = OBEX_Continue = 0x90

class Success(Response):
    code = OBEX_OK = OBEX_Success = 0xA0

class ConnectSuccess(Success):
    format = "BBH"

class Bad_Request(FailureResponse):
    code = OBEX_Bad_Request = 0xC0

class Unauthorized(FailureResponse):
    code = OBEX_Unauthorized = 0xC1

class Forbidden(FailureResponse):
    code = OBEX_Forbidden = 0xC3

class Not_Found(FailureResponse):
    code = OBEX_Not_Found = 0xC4

class Precondition_Failed(FailureResponse):
    code = OBEX_Precondition_Failed = 0xCC

class UnknownResponse(Response):
    def __init__(self, code, data):
        self.code = code
        self.data = data[3:]

    def __repr__(self):
        return "%s(code=0x%02X, data=%s)" % (
            type(self).__name__, self.code, repr(self.data)
        )


class ResponseHandler(MessageHandler):
    send_garbage_flag = True

    message_dict = {
            Continue.code: Continue,
            Success.code: Success,
            Bad_Request.code: Bad_Request,
            Unauthorized.code: Unauthorized,
            Forbidden.code: Forbidden,
            Not_Found.code: Not_Found,
            Precondition_Failed.code: Precondition_Failed
    }

    UnknownMessageClass = UnknownResponse


    def decode_connection(self, socket):
        # print('[INFO] Waiting victim confirm...')
        code, data = self.read_conn_rsp_pkt(socket)

        if code == ConnectSuccess.code:
            message = ConnectSuccess(data)
        elif code in self.message_dict:
            message = self.message_dict[code](data)
        else:
            return self.UnknownMessageClass(code, data)

        obex_version, flags, max_packet_length = struct.unpack(">BBH", data[3:7])

        message.obex_version = OBEX_Version()
        message.obex_version.from_byte(obex_version)
        message.flags = flags
        message.max_packet_length = max_packet_length
        message.read_data(data)
        return message


    def read_conn_rsp_pkt(self, socket_):
        '''by sourcell xu, original no
        模仿 MessageHandler._read_packet() 为 ResponseHandler.decode_connection() 
        提供处理 OBEX connection response 的方法，从而解决因 victim 不及时授权导致的 recv() 阻塞。'''
        ResponseHandler.send_garbage_flag = True
        send_garbage_thread = self.SendGarbageThread(socket_)
        send_garbage_thread.start()

        # Receive OBEX connection response code (1 B) and packet length (2 B).
        # Because OBEX (based on RFCOMM) is connection-oriented and the 
        # connection request is sent before garbage, so the reponse for 
        # connection request will be received before the response for garbage.
        data = socket_.recv(3, socket.MSG_WAITALL)
            
        ResponseHandler.send_garbage_flag = False

        code, length = struct.unpack(">BH", data)
        #print('[Debug] code =', code)
        #print('[Debug] length =', length)
        body_len = length - 3
        while body_len > 0:
            read_len = 32767 if body_len > 32767 else body_len
            data += socket_.recv(read_len, socket.MSG_WAITALL)
            body_len -= read_len
        #print(code, data)

        send_garbage_thread.join()
        send_garbage_thread.clean()

        #code = 0xa0
        #data = b'\xa0\x00\x1f\x10\x00\xff\xfe\xcb\x00\x00\x00\x01J\x00\x13ya5\xf0\xf0\xc5\x11\xd8\tf\x08\x00 \x0c\x9af'
        return code, data


    class SendGarbageThread(threading.Thread):
        '''Constantly send malformed OBEX packet to target for keeping connection alive.'''
        def __init__(self, sock):
            super().__init__()
            self.count = 0
            self.sock = sock

        def run(self):
            while True:
                time.sleep(2)
                if ResponseHandler.send_garbage_flag:
                    # request opcode = 0x00, length = 0x0000
                    self.sock.send(b'\x00\x00\x00')
                    self.count += 1
                else:
                    break

        def clean(self):
            for i in range(self.count):
                print('[CLEAN GARBAGE]', self.sock.recv(3, socket.MSG_WAITALL))
            self.count = 0
