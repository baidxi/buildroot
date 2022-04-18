#!/usr/bin/env python3

r'''bluerepli

Usage:
    bluerepli.py (-h | --help)
    bluerepli.py (-v | --version)
    bluerepli.py [-i <hcix>] [-a <addr>] [-n <name>] [-c <cod>] --dump-pb [--rname=<str>] [--rclass=<class>] [--link-key=<plain_hex>] [-d <dir>] TARGET
    bluerepli.py [-i <hcix>] [-a <addr>] [-n <name>] [-c <cod>] --dump-msg [--rname=<str>] [--rclass=<class>] [--link-key=<plain_hex>] [-d <dir>] TARGET
    bluerepli.py [-i <hcix>] [-a <addr>] [-n <name>] [-c <cod>] --send-msg [--rname=<str>] [--rclass=<class>] [--link-key=<plain_hex>] MESSAGE PHONE TARGET

Arguments:
    MESSAGE        Text message               
    PHONE          Phone number to receive message
    TARGET         BD_ADDR of target device 

Options:
    -h, --help              Display this help
    -v, --version           Show the version
    -i <hcix>               Specify HCI device [default: hci0]
    -a <addr>               Camouflage BD_ADDR for local device
    -n <name>               Camouflage name for local device
    -c <cod>                Camouflage class for local device
    --dump-pb               Dump whole phonebook stored in TARGET
    --dump-msg              Dump all messages stored in TARGET
    --send-msg              Send a short message to PHONE via TARGET Bluetooth device
    --raddr=<addr>          BD_ADDR of remote device
    --rname=<name>          Name of remote device
    --rclass=<class>        Class of remote device
    --link-key=<key>        Shared link key between local device and remote device
    -d <dir>                The output directory for storing phonebook or message [default: ./output]
'''

INFO = '[\x1B[1;34mINFO\x1B[0m]' # blue
WARNING = '[\x1B[1;33mWARNING\x1B[0m]' # yellow
ERROR = '[\x1B[1;31mERROR\x1B[0m]' # red

from docopt import docopt


def parse_cmdline() -> dict:
    args = docopt(__doc__, version='0.0.1', options_first=True)
    #print("[Debug] args =", args)

    return args


if __name__ == "__main__":
    main()
