import struct

from helper import le_ram2str

import docopt


def list_discovered_conns(ll_conns:dict):
    #print("[Debug]", ll_conns)
    if len(ll_conns) == 0:
        print("[T-T] ", end='')
    print(len(ll_conns), "discovered connection(s)")

    for conn in ll_conns.values():
        print()
        print("Access Address:", le_ram2str(conn.aa))
        print("    CRCInit:", le_ram2str(conn.crc_init))
        print("    Channel map:", le_ram2str(conn.chm))
        print("    Hop interval:", le_ram2str(conn.hop_inter))
        print("    Hop increment:", conn.hop_inc)
        print("    AA on channels:", conn.aa_chs)
        print("    Remapping table:", conn.remapping_tab)
        print("    All possible hop sequences:", conn.hop_seqs)
        print("    Channels for cracking hop interval:", conn.unique_chs)
        print("    Troikas for cracking hop increment:", conn.troikas)
        print("    Is target?", conn.is_target)
        print("    Is user defined connection?", conn.is_user_defined)
        print()
