#!/usr/bin/env python3

import os
import threading
import getopt
import struct
import time
#import signal

from ui import list_discovered_conns

from helper import le_ram2str
from helper import str2ram_le
from helper import extract_crc_init
from helper import hopseq2bytes

from serial import Serial
from serial import SerialException
from serial.tools.list_ports import comports

import ble

t_crack_hopinc_start = None
t_crack_hopinc_end = None

t_sniff_aa_start = None
t_sniff_aa_end = None

get_t_sniff_aa_start = False


HELP_DOC = r"""
Description

Interactive Options
    -h, --help
        Display this help.

    -s, --sniff-aas
        Sniff surrounding access addresses.

    -l
        List information of discovered connection(s).

    --crack-crc-init -A <AA> [-C <num>]
        破解目标连接的 CRCInit

    --crack-channel-map -A <AA> [--crc-init=<CRCInit>]
        破解目标连接的 channel map

    --crack-hop-interval -A <AA> [-crc-init=<CRCInit>] [-M <CHM>]
        破解目标连接的 hop interval

    --crack-hop-increment -A <AA>
        破解目标连接的 hop increment。

    --jam -A <AA>
        干扰目标连接。

    -A, --access-address=<ACCESS_ADDR>
        指定目标 BLE 连接。

    -C, --channel=<CH>
    
    --crc-init=<CRCInit>
        指定目标 AA 的 CRCInit。

    -M, --channel-map=<CHM>
        指定目标 AA 的 channel map。

    --exit
"""

lower_cmd_handler_thread = None

# key: aa, little-endian, 4 bytes
# Value: ble.LLConn instance
ll_conns = {}


def get_microbit_serial_dev_path():
    for port in comports():
        if "mbed" in port.description:
            return port.device
    
    return ""


# UPPER_CMD_LEN = 254
# EVT_LEN = 254

UPPER_CMD_LEN = 100
EVT_LEN = 100

AA_LEN = 4
CRCINIT_LEN = 3
CHM_LEN = 5
HOPINTER_LEN = 2
HOPINCRE_LEN = 1
HOP_PERIOD_LEN = 37

# Upper Command Opcode
CMD_READY = 0x00
OP_IDLE = 2
OP_SNIFF_AAS = 3
OP_CRACK_CRCINIT = 4
OP_CRACK_CHM = 6
OP_CRACK_HOPINTER = 7
OP_CRACK_HOPINC = 8
OP_JAM = 9
OP_BF_JAM = 10
OP_SNIFF_ADV = 11

# Lower Command Opcode
OP_LOWER_READY = 0
OP_ERROR = 1
OP_ACK = 2
OP_DISCOVERED_AA = 3
OP_CRACKED_CRCINIT = 4
OP_FOUND_USED_CH = 5
OP_CRACKED_CHM = 6
OP_CRACKED_HOPINTER = 7
OP_CRACKED_HOPINC = 8
OP_VERBOSE = 0xFE
EVT_DEBUG = 0xFF

serial_dev = None

help_opt = False
sniff_aas_opt = False
list_conns_opt = False
crack_crcinit_opt = False
crack_chm_opt = False
crack_hopinter_opt = False
crack_hopinc_opt = False
jam_opt = False
bf_jam_opt = False
aa_opt = b'' # Little-endian
channel_opt = None # int
crc_init_opt = b''
exit_opt = False
sniff_adv = False


def clear_inter_opts():
    global help_opt
    global sniff_aas_opt
    global list_conns_opt
    global crack_crcinit_opt
    global crack_chm_opt
    global crack_hopinter_opt
    global crack_hopinc_opt
    global jam_opt
    global bf_jam_opt
    global aa_opt # little-endian bytes
    global crc_init_opt # little-endian bytes
    global channel_opt # 1 element bytes
    global exit_opt
    global sniff_adv

    help_opt = False
    sniff_aas_opt = False
    list_conns_opt = False
    crack_crcinit_opt = False
    crack_chm_opt = False
    crack_hopinter_opt = False
    crack_hopinc_opt = False
    jam_opt = False
    bf_jam_opt = False
    aa_opt = b''
    crc_init_opt = b''
    channel_opt = None # int
    exit_opt = False
    sniff_adv = False


def parse_inter_cmd(inter_cmd:str):
    global help_opt
    global sniff_aas_opt
    global list_conns_opt
    global crack_crcinit_opt
    global crack_chm_opt
    global crack_hopinter_opt
    global crack_hopinc_opt
    global jam_opt
    global bf_jam_opt
    global aa_opt # little-endian bytes
    global crc_init_opt # little-endian bytes
    global channel_opt # 1 element bytes
    global exit_opt
    global sniff_adv

    inter_argvs = inter_cmd.split()
    ov_pairs, nonopt_args = getopt.getopt(
        inter_argvs, 
        "hslA:C:", 
        [ "help", "sniff-aas", 
        "crack-crc-init", "crack-channel-map",
        "crack-hop-interval", "crack-hop-increment", "jam",
        "bf-jam", "sniff-adv",
        "access-address=", "channel=", "crc-init=", 
        "exit" ]
    )

    for opt, val in ov_pairs:
        if opt in ("-h", "--help"):
            help_opt = True
            break
        elif opt in ("-s", "sniff-aas"):
            sniff_aas_opt = True
            break
        elif opt in ("-l"):
            list_conns_opt = True
            break
        elif opt in ("--crack-crc-init"):
            crack_crcinit_opt = True
        elif opt in ("--crack-channel-map"):
            crack_chm_opt = True
        elif opt in ("--crack-hop-interval"):
            crack_hopinter_opt = True
        elif opt in ("--crack-hop-increment"):
            crack_hopinc_opt = True
        elif opt in ("--jam"):
            jam_opt = True
        elif opt in ("--bf-jam"):
            bf_jam_opt = True
        elif opt in ("-A", "--access-address"):
            if len(val) != 10 or val[0] != '0' or val[1] != 'x':
                raise ValueError
            aa_opt = bytes.fromhex(val[2:])[::-1] # little-endian
        elif opt in ("-C", "--channel"):
            if not (1 <= len(val) <= 2):
                raise ValueError
            channel_opt = int(val)
        elif opt in ("--crc-init"):
            if len(val) != 8 or val[0] != '0' or val[1] != 'x':
                raise ValueError
            crc_init_opt = bytes.fromhex(val[2:])[::-1] # little-endian
        elif opt in ("--exit"):
            exit_opt = True
        elif opt in ("--sniff-adv"):
            sniff_adv = True
            break

    for nonopt_arg in nonopt_args:
        print("[Debug] nonopt_arg:", nonopt_arg)


class InterCmdHandlerThread(threading.Thread):
    def run(self):
        InterCmdHandlerThread.inter_cmd_handler()

    @staticmethod
    def inter_cmd_handler():
        global help_opt
        global sniff_aas_opt
        global list_conns_opt
        global crack_crcinit_opt
        global crack_chm_opt
        global crack_hopinter_opt
        global crack_hopinc_opt
        global jam_opt
        global bf_jam_opt
        global aa_opt
        global crc_init_opt
        global channel_opt
        global exit_opt
        global sniff_adv

        while True:
            try:
                serial_idle()
                clear_inter_opts()
                inter_cmd = input('> ') # Waiting interactive command
                if len(inter_cmd) == 0:
                    continue
                parse_inter_cmd(inter_cmd)
            except (getopt.GetoptError, ValueError) as e:
                print("[Error] Invalid interactive command,", e)
                continue

            if help_opt:
                print(HELP_DOC)
            elif sniff_aas_opt:
                ll_conns.clear()
                serial_sniff_aas()

                print("[Info] Input q + Enter to stop sniffing aas.")
                while input() != 'q':
                    continue
            elif list_conns_opt:
                list_discovered_conns(ll_conns)
            elif crack_crcinit_opt: # Need an AA and an aa_ch
                if aa_opt in ll_conns and channel_opt == None:
                    ll_conns[aa_opt].is_target = True
                    channel_opt = ll_conns[aa_opt].aa_chs[0] 

                elif aa_opt in ll_conns and channel_opt != None:
                    print("[info] Using user defined channel.")
                    ll_conns[aa_opt].is_target = True

                elif aa_opt not in ll_conns and channel_opt == None:
                    print("[info] The provided AA is not in the list.")
                    print("[Error] No channel for AA.")
                    continue

                elif aa_opt not in ll_conns and channel_opt != None:
                    print("[info] The provided AA is not in the list.")
                    print("[info] Using user defined connections.")
                    ll_conns[aa_opt] = ble.LLConn(aa_opt, True)
                    ll_conns[aa_opt].aa_chs.append(channel_opt)
                    ll_conns[aa_opt].is_target = True

                serial_crack_crcinit(aa_opt, channel_opt)

                print("[Info] Input q + Enter to stop cracking CRCInit.")
                while input() != 'q':
                    continue

                ll_conns[aa_opt].is_target = False
            
            elif crack_chm_opt:
                if aa_opt not in ll_conns and crc_init_opt == b'':
                    print("[info] The provided AA is not in the list.")
                    print("[Error] Need CRCInit.")
                    continue

                elif aa_opt not in ll_conns and crc_init_opt != b'':
                    print("[info] The provided AA is not in the list.")
                    print("[info] Using user defined connections.")
                    ll_conns[aa_opt] = ble.LLConn(aa_opt, True)
                    ll_conns[aa_opt].crc_init = crc_init_opt
                    ll_conns[aa_opt].is_target = True

                elif aa_opt in ll_conns and crc_init_opt == b'':
                    ll_conns[aa_opt].is_target = True
                    crc_init_opt = ll_conns[aa_opt].crc_init

                elif aa_opt in ll_conns and crc_init_opt != b'':
                    print("[Info] Using user defined CRCInit.")
                    ll_conns[aa_opt].is_target = True
                
                serial_crack_chm(aa_opt, crc_init_opt)

                print("[Info] Input q + Enter to stop cracking channel map.")
                while input() != 'q':
                    continue

                ll_conns[aa_opt].is_target = False

            elif crack_hopinter_opt:
                if aa_opt not in ll_conns:
                    print("[Error] The provided AA is not in the list.")
                    continue

                ll_conns[aa_opt].is_target = True
                crc_init_opt = ll_conns[aa_opt].crc_init

                try:
                    unique_ch = ll_conns[aa_opt].troikas[0]['unique_ch']
                except IndexError:
                    print("[T-T] The current channel map can not be used to crack hop interval.")
                    continue

                serial_crack_hopinter(aa_opt, crc_init_opt, unique_ch)
                
                print("[Info] Input q + Enter to stop cracking hop interval.")
                while input() != 'q':
                    continue

                ll_conns[aa_opt].is_target = False

            elif crack_hopinc_opt:
                if aa_opt not in ll_conns:
                    print("[Error] The provided AA is not in the list.")
                    continue
                
                ll_conns[aa_opt].is_target = True
                ll_conns[aa_opt].candidate_crcinit = b''
                ll_conns[aa_opt].crcinit_match_count = 0

                serial_crack_hopinc(
                    aa_opt,
                    ll_conns[aa_opt].crc_init,
                    ll_conns[aa_opt].hop_inter, 
                    ll_conns[aa_opt].troikas[0]['unique_ch'],
                    ll_conns[aa_opt].troikas[0]['exp_ch']
                )

                print("[Info] Input q + Enter to stop cracking hop increment.")
                while input() != 'q':
                    continue

                ll_conns[aa_opt].is_target = False

            elif jam_opt:
                # ll_conns 是一个 dict。其中 key 为 aa，value 为 LLConn
                # instance。同时 LLConn instance 本身也存储了 aa。
                if aa_opt not in ll_conns:
                    print("[Error] The provided AA is not in the list.")
                    continue
                
                if ll_conns[aa_opt].crc_init != b'' \
                   and ll_conns[aa_opt].chm != b'' \
                   and ll_conns[aa_opt].hop_inter != b'' \
                   and ll_conns[aa_opt].hop_inc != b'' \
                   and len(ll_conns[aa_opt].troikas) != 0:
                    hop_inc = ll_conns[aa_opt].hop_inc
                   
                    serial_jam(
                        aa_opt, ll_conns[aa_opt].crc_init, 
                        ll_conns[aa_opt].chm, ll_conns[aa_opt].hop_inter,
                        hop_inc,
                        ll_conns[aa_opt].troikas[0]['unique_ch'],
                        hopseq2bytes(ll_conns[aa_opt].hop_seqs[hop_inc])
                    )

                    ll_conns[aa_opt].is_target = True

                    while input() != 'q':
                        continue
                    ll_conns[aa_opt].is_target = False
                    print("[Debug] Jamming stopped.")
                else:
                    print("[Error] Can't jam this connection.")

            elif bf_jam_opt:
                if aa_opt not in ll_conns:
                    print("[Error] The provided AA is not in the list.")
                    continue

                if ll_conns[aa_opt].crc_init != b'':
                    serial_brute_force_jam(
                        aa_opt, ll_conns[aa_opt].crc_init, 
                        12
                    )
                    while input() != 'q':
                        continue
                    ll_conns[aa_opt].is_target = False
                    print("[Debug] Brute force jamming stopped.")
                else:         
                    print("[Error] Can't brute force jam this connection.")

            elif exit_opt:
                #print("[Debug] exit_opt")
                # 这里调用 serial_idle() 的主要目的并不是让 lower computer 进入
                # MODE_IDLE，而是借 lower computer 返回的 ack，让 lower command
                # handler 进入下一次循环，从而判断 not exit_opt 为假，最终退出
                # 线程。
                serial_idle()
                return
            elif sniff_adv:
                serial_sniff_adv(37)
            else:
                print("[Error] Invalid interactive cmd")


class LowerCmdHandlerThread(threading.Thread):
    def run(self):
        LowerCmdHandlerThread.lower_cmd_handler()

    @staticmethod
    def lower_cmd_handler():
        inter_cmd_handler_thread = InterCmdHandlerThread()
        serial_ready()

        while not exit_opt:
            lower_cmd = serial_dev.read(EVT_LEN)
            #print("[Debug] lower_cmd =", lower_cmd)

            if len(lower_cmd) != EVT_LEN:
                print("[Error] Invalid lower command length")
                continue

            op = lower_cmd[0]

            if op == OP_LOWER_READY:
                #print("[Debug] OP_LOWER_READY, lower_cmd =", lower_cmd)
                print("[^-^] Lower computer is ready!")
                if not inter_cmd_handler_thread.is_alive():
                    # inter_cmd_handler_thread 将继承 lower_cmd_handler_thread
                    # 的 daemon 属性。
                    inter_cmd_handler_thread.start()
                else:
                    print("[Error] The Interactive command handler is already alive.")
            
            elif op == EVT_DEBUG:
                try:
                    msg_len = lower_cmd[1]
                    print("[Debug]", lower_cmd[2:msg_len + 2].decode())
                except UnicodeDecodeError as e:
                    print("[Error]", e)
                    continue
            
            elif op == OP_ERROR:
                msg_len = lower_cmd[1]
                print("[Error]", lower_cmd[2:msg_len + 2].decode())
            
            elif op == OP_DISCOVERED_AA:
                aa = lower_cmd[2:6] # Little-endian
                ch = lower_cmd[6] # int
                
                try:
                    if ch not in ll_conns[aa].aa_chs:
                        ll_conns[aa].aa_chs.append(ch)
                except KeyError:
                    ll_conns[aa] = ble.LLConn(aa)
                    ll_conns[aa].aa_chs.append(ch)
                
                print("[^-^] AA:", le_ram2str(aa), "   ", "channel:", ch)
                
                # if ch == 0 or ch == 1 or ch == 2:
                #     global t_sniff_aa_start
                #     if get_t_sniff_aa_start == False:
                #         t_sniff_aa_start = time.time()
                #         get_t_sniff_aa_start = True
                
                if ch == 36:
                    global t_sniff_aa_end
                    t_sniff_aa_end = time.time()
                    print(t_sniff_aa_end - t_sniff_aa_start)
                    get_t_sniff_aa_start = False


            elif op == OP_CRACKED_CRCINIT:
                #print("[Debug] OP_CRACKED_CRCINIT")
                pseudo_crc_init = lower_cmd[2:6]
                crc_init = extract_crc_init(pseudo_crc_init)
                print("[Info] Candidate CRCInit:", crc_init)
                crc_init = str2ram_le(crc_init)

                for conn in ll_conns.values():
                    if conn.is_target:
                        if crc_init == conn.candidate_crcinit:
                            conn.crcinit_match_count += 1
                            if conn.crcinit_match_count >= ble.LLConn.CRCINIT_MATCH_LIMIT:
                                conn.is_target = False
                                conn.crc_init = crc_init
                                print("[^-^] CRCInit:", le_ram2str(crc_init))
                        else:
                            conn.candidate_crcinit = crc_init
                            conn.crcinit_match_count = 0
                        
                        #serial_idle()
                        #serial_crack_chm(conn.aa, conn.crc_init)
                        #conn.is_target = True
                        break
                    
            elif op == OP_CRACKED_CHM:
                serial_idle()
                #print("[Debug] OP_CRACKED_CHM")
                chm = lower_cmd[2:7] # Little-endian, 5 bytes
                for conn in ll_conns.values():
                    if conn.is_target:
                        conn.is_target = False
                        conn.set_channel_map(chm)

                        #serial_idle()
                        #serial_crack_hopinter(conn.aa, conn.crc_init, conn.troikas[0]['unique_ch'])
                        #conn.is_target = True
                        break

                print("[^-^] Channel map:", le_ram2str(chm))
                
            elif op == OP_CRACKED_HOPINTER:
                #print("[Debug] OP_CRACKED_HOPINTER")
                hop_inter = lower_cmd[2:4] # Little-endian, 2 bytes
                for conn in ll_conns.values():
                    if conn.is_target:
                        conn.is_target = False
                        conn.hop_inter = hop_inter
                        break

                print(
                    "[^-^] Hop interval:", 
                    int.from_bytes(hop_inter, byteorder='little')
                )

            elif op == OP_CRACKED_HOPINC:
                global t_crack_hopinc_end
                print("[Debug] OP_CRACKED_HOPINC")
                distance = lower_cmd[2] # int
                print("[Debug] distance =", distance)
                try:
                    for conn in ll_conns.values():
                        if conn.is_target:
                            conn.is_target = False
                            hop_inc = conn.troikas[0]['dh_tab'][distance] # int
                            conn.hop_inc = hop_inc
                            print("[^-^] Hop increment:", hop_inc)
                            t_crack_hopinc_end = time.time()
                            print(t_crack_hopinc_end-t_crack_hopinc_start)
                            break
                except KeyError as e:
                    print("[Error] The distance is not existed. Try again")
                
            elif op == OP_ACK:
                #print("[Debug] OP_ACK")
                pass

        inter_cmd_handler_thread.join()


def serial_idle():
    r"""Send OP_IDLE to lower computer.
    
    +------------+
    | Op  | Len  |
    |-----|------|
    | 1 B | 0x00 |
    +------------+
    """
    #print("[Debug] serial_idle()")
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_IDLE
    serial_dev.write(upper_cmd)


def serial_ready():
    r"""Send CMD_READY to lower computer."""
    #print("[Debug] serial_upper_ready()")
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = CMD_READY
    serial_dev.write(upper_cmd)


def serial_sniff_aas():
    r"""Send OP_SNIFF_AAS to lower computer.

    +------------+
    | Op  | Len  |
    |-----|------|
    | 1 B | 0x00 |
    +------------+
    """
    #print("[Debug] serial_sniff_aas()")
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_SNIFF_AAS
    global t_sniff_aa_start
    t_sniff_aa_start = time.time()
    serial_dev.write(upper_cmd)


def serial_sniff_adv(channel:int):
    cmd = struct.pack('>BBB', OP_SNIFF_ADV, 1, channel)
    serial_dev.write(cmd)


def serial_crack_crcinit(aa:bytes, ch:int):
    r"""Send OP_CRACK_CRCINIT to lower computer.

    Parameters
        The aa should be little-endian. 

    +--------------------------------+
    | Op  | Len  | AA (LE) | Channel |
    |-----|------|---------|---------|
    | 1 B | 0x05 | 4 B     |  1 B    |
    +--------------------------------+
    """
    #print("[Debug] serial_crack_crcinit()")
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_CRACK_CRCINIT
    upper_cmd[1] = 5
    upper_cmd = upper_cmd.replace(bytes(AA_LEN), aa, 1)
    upper_cmd[6] = ch
    serial_dev.write(upper_cmd)


def serial_crack_chm(aa:bytes, crc_init:bytes):
    r"""Send OP_CRACK_CHM to lower computer.

    Parameters
        The aa and crc_init should be little-endian.

    +-------------------------------------|...............+
    | Op  | Len  | AA (LE) | CRCInit (LE) | Start Channel |
    |-----|------|---------|--------------|...............+
    | 1 B | 0x07 | 4 B     | 3 B          | 1 B           |
    +-------------------------------------|...............+
    """
    #print("[Debug] serial_crack_chm()")
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_CRACK_CHM
    upper_cmd[1] = 7
    upper_cmd = upper_cmd.replace(bytes(AA_LEN), aa, 1)
    upper_cmd = upper_cmd.replace(bytes(CRCINIT_LEN), crc_init, 1)
    #print("[Debug] upper_cmd", upper_cmd)
    serial_dev.write(upper_cmd)


def serial_crack_hopinter(aa:bytes, crc_init:bytes, unique_ch:int):
    r"""Send OP_CRACK_HOPINTER to lower computer.

    Parameters
        The aa and crc_init should be little-endian.

    +------------------------------------------------------+
    | Op  | Len  | AA (LE) | CRCInit (LE) | Unique Channel |
    |-----|------|---------|--------------|----------------|
    | 1 B | 0x08 | 4 B     | 3 B          | 1 B            |
    +------------------------------------------------------+
    """
    #print("[Debug] serial_crack_hopinter()")
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_CRACK_HOPINTER
    upper_cmd[1] = 8
    upper_cmd = upper_cmd.replace(bytes(AA_LEN), aa, 1)
    upper_cmd = upper_cmd.replace(bytes(CRCINIT_LEN), crc_init, 1)
    upper_cmd[2 + AA_LEN + CRCINIT_LEN] = unique_ch
    #print("[Debug] upper_cmd =", upper_cmd)
    serial_dev.write(upper_cmd)


def serial_crack_hopinc(
    aa:bytes, crc_init:bytes, hop_inter:bytes,
    unique_ch:int, exp_ch:int):
    r"""Send OP_CRACK_HOPINC to lower computer

    Parameters
        The aa, crc_init and hop_inter should be little-endian.

    +------------------------------------------------------------------------------------------------+
    | Op  | Len  | AA (LE) | CRCInit (LE) | Hop Interval (LE) | Unique Channel | Exploitable Channel |
    |-----|------|---------|--------------|-------------------|----------------|---------------------|
    | 1 B | 0x0B | 4 B     | 3 B          | 2 B               |  1 B           | 1 B                 |
    +------------------------------------------------------------------------------------------------+
    """
    #print("[Debug] serial_crack_hopinc()")
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_CRACK_HOPINC
    upper_cmd[1] = 0x0B
    upper_cmd = upper_cmd.replace(bytes(AA_LEN), aa, 1)
    upper_cmd = upper_cmd.replace(bytes(CRCINIT_LEN), crc_init, 1)
    upper_cmd = upper_cmd.replace(bytes(HOPINTER_LEN), hop_inter, 1)
    upper_cmd[2 + AA_LEN + CRCINIT_LEN + HOPINTER_LEN] = unique_ch
    upper_cmd[3 + AA_LEN + CRCINIT_LEN + HOPINTER_LEN] = exp_ch
    #print("[Debug] upper_cmd =", upper_cmd)
    global t_crack_hopinc_start
    t_crack_hopinc_start = time.time()
    serial_dev.write(upper_cmd)


def serial_jam(
    aa:bytes, crc_init:bytes, chm:bytes,
    hop_inter:bytes, hop_inc:int, unique_ch:int,
    hop_seq:bytes):
    r"""SEND OP_JAM to lower computer

    +----------------------------------------------------------------------------------------------------------------+
    | Op  | Len  | AA       | CRCInit  | ChM      | Hop Interval | Hop Increment          | Unique channel | Hop seq |
    |-----|------|----------|----------|----------|--------------|------------------------|----------------|---------|
    | 1 B | 0x10 | 4 B (LE) | 3 B (LE) | 5 B (LE) | 2 B (LE)     | 1 B (only use 5 LSBit) | 1 B            | 37 B    | 
    +----------------------------------------------------------------------------------------------------------------+
    """
    print("[Debug] serial_jam()")
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_JAM
    upper_cmd[1] = 0x10
    upper_cmd = upper_cmd.replace(bytes(AA_LEN), aa, 1)
    upper_cmd = upper_cmd.replace(bytes(CRCINIT_LEN), crc_init, 1)
    upper_cmd = upper_cmd.replace(bytes(CHM_LEN), chm, 1)
    upper_cmd[2 + AA_LEN + CRCINIT_LEN + CHM_LEN] = hop_inter[0]
    upper_cmd[3 + AA_LEN + CRCINIT_LEN + CHM_LEN] = hop_inter[1]
    upper_cmd[4 + AA_LEN + CRCINIT_LEN + CHM_LEN] = hop_inc
    upper_cmd[5 + AA_LEN + CRCINIT_LEN + CHM_LEN] = unique_ch
    print("[Debug] Unique channel:", unique_ch)
    if unique_ch == 0x00:
        upper_cmd[5 + AA_LEN + CRCINIT_LEN + CHM_LEN] = 0x01
        upper_cmd = upper_cmd.replace(bytes(HOP_PERIOD_LEN), hop_seq, 1)
        upper_cmd[5 + AA_LEN + CRCINIT_LEN + CHM_LEN] = 0x00
    else:
        upper_cmd = upper_cmd.replace(bytes(HOP_PERIOD_LEN), hop_seq, 1)
    print("[Debug] upper_cmd =", upper_cmd)
    serial_dev.write(upper_cmd)


def serial_brute_force_jam(
    aa:bytes, crc_init:bytes, ch:int):
    """
    +-------------------------------------------------+
    | Op  | Len  | AA       | CRCInit  | Used channel |
    |-----|------|----------|----------|--------------|
    | 1 B | 0x08 | 4 B (LE) | 3 B (LE) | 1 B          |
    +-------------------------------------------------+
    """
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_BF_JAM
    upper_cmd[1] = 0x08
    upper_cmd = upper_cmd.replace(bytes(AA_LEN), aa, 1)
    upper_cmd = upper_cmd.replace(bytes(CRCINIT_LEN), crc_init, 1)
    upper_cmd[2 + AA_LEN + CRCINIT_LEN] = ch
    print("[Debug] upper_cmd =", upper_cmd)
    serial_dev.write(upper_cmd)



def main():
    global serial_dev
    global lower_cmd_handler_thread

    dev_path = get_microbit_serial_dev_path()
    serial_dev = Serial(dev_path, 115200)
    
    serial_dev.reset_input_buffer()
    serial_dev.reset_output_buffer()
    
    # 由于 threading module 会确保在所有 non-daemon threads 退出前，保证整个进程
    # 的存活，所以若想让整个 python 程序（主线程）的退出不用等待子线程，
    # 就需要将 lower_cmd_handler_thread，设置为 daemon thread。
    lower_cmd_handler_thread = LowerCmdHandlerThread()
    lower_cmd_handler_thread.daemon = True
    lower_cmd_handler_thread.start() 
    lower_cmd_handler_thread.join()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        # Python 进程在接收到 Ctrl-C 发出的 SIGINT 后，会默认将其被转换为
        # KeyboardInterrupt，且只有 main thread 能捕获到这个 KeyboardInterrupt。
        #print("[Debug] KeyboardInterrupt from main(),", e)
        print()
    except SerialException as e:
        print("[SerialException]", e)
    finally:
        if serial_dev:
            serial_idle()
            serial_dev.reset_input_buffer()
            serial_dev.reset_output_buffer()
            serial_dev.close()
