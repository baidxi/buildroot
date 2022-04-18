#!/usr/bin/env python3


import copy


MIN_HOPINCRE = 5
MAX_HOPINCRE = 16


class LLConn:
    CRCINIT_MATCH_LIMIT = 2

    def __init__(self, aa:bytes, is_user_defined=False):
        self.aa = aa # Little-endian, 4 bytes
        self.crc_init = b'' # Little-endian, 3 bytes
        self.chm = b'' # Little-endian, 5 bytes
        self.hop_inter = b'' # Little-endian, 2 bytes 
        self.hop_inc = None # int

        self.candidate_crcinit = b'' # Little-endian, 3 bytes
        self.crcinit_match_count = 0

        # Discovered used channels during sniffing AAs.
        self.aa_chs = [] # int list

        self.remapping_tab = []

        # All possible hop sequences before cracking hop increment
        # Key: hop increment
        # Value: int list, hop sequence，长度为 37 (一个周期)
        self.hop_seqs = {}

        # All valid channel for cracking hop interval
        self.unique_chs = []

        # Unique channel and exploitable channel pairs for cracking hop
        # interval and hop increment. 虽然破解 hop interval 只要 unique channel
        # 就够了，但若 unique channel 没有配套使用的 exploitable channel。那么
        # 后续的 hop increment 便无法破解。于是仅存储 unique channel and
        # exploitable channel pairs，而舍弃没有 exploitable channel 配套使用的
        # unique channel。

        # All valid troikas for cracking hop increment
        # 
        # Element: dict
        #     {
        #         'unique_ch': int,
        #         'exp_ch': int,
        #         'dh_tab': { distance int: hop_inc int,}
        #     }
        self.troikas = []

        # Key: distance between Unique channel and exploitable channel
        # Value: hop increment for specific hop sequence
        self.dh_tab = {}

        self.is_target = False
        self.is_user_defined = is_user_defined


    def set_channel_map(self, chm:bytes):
        self.chm = chm
        self._gen_remapping_tab()
        self._gen_hopseqs()
        self._find_unique_chs()
        self._find_troikas()


    def _gen_remapping_tab(self):
        chm = int.from_bytes(self.chm, 'little')

        for c in range(0, 37):
            if chm & 1 << c:
                self.remapping_tab.append(c)

        # print("[Debug]", len(self.remapping_tab), "used channels") 
        # print("        Remapping table:", self.remapping_tab)
        # print()


    def gen_hopseq(self, hop_inc:int, seq_len=37) -> tuple:
        r"""生成指定长度的 BLE Hop Sequence

        hop_inc
            Hop increment 的取值范围为 5 到 16 之间的整数。

        seq_len
            由于 BLE hop sequence 是无限长的，所以使用该参数指定期望的
            hop sequence 长度。将该参数默认值设为 37 的原因是 BLE hop sequence
            总以 37 为周期重复循环出现。
        """
        seq = []
        last_unmapped_ch = 0
        num_used_chs = len(self.remapping_tab)

        while seq_len:
            unmapped_ch = (last_unmapped_ch + hop_inc) % 37
            last_unmapped_ch = unmapped_ch

            if unmapped_ch in self.remapping_tab:
                ch = unmapped_ch
            else:
                remapping_idx = unmapped_ch % num_used_chs
                ch = self.remapping_tab[remapping_idx]

            #print("[Debug] Current channel:", ch)
            seq.append(ch)
            seq_len -= 1

        return seq


    def _gen_hopseqs(self):
        r"""Generate all possible hop sequences before cracking hop increment."""
        for hop_inc in range(MIN_HOPINCRE, MAX_HOPINCRE + 1):
            self.hop_seqs[hop_inc] = self.gen_hopseq(hop_inc)

        for hop_inc, seq in self.hop_seqs.items():
            print("[Debug] Hop increment:", hop_inc)
            print("        Sequence: ", seq)
            print()


    def _find_unique_chs(self):
        r"""从 channel map 中找到可以用于破解 hop interval 的 channel。"""
        for ch in self.remapping_tab:
            is_unique_ch = True
            for seq in self.hop_seqs.values():
                if seq.count(ch) > 1:
                    is_unique_ch = False
                    break
            if is_unique_ch:
                self.unique_chs.append(ch)

        print("[Debug] Unique channels:", self.unique_chs)


    @classmethod
    def get_hopseq_idx(cls, hop_seq:list, ch:int, start:int) -> int:
        r"""得到 channel 在 hop sequence 的 start 位置之后第一次出现的位置。

        从 0 开始依次将 hop sequence 周期中出现 channel 编号，该编号就表示
        channel 的位置。

        Example:
            ... ...
        """
        for i in range(37):
            if hop_seq[(start + i) % 37] == ch:
                return (start + i) % 37

        return -1


    def _compute_distance(self, hop_seq:list, fst_ch:int, sec_ch:int) -> int:
        r"""计算两个 channel 在指定 hop sequence 中的距离。"""
        fst_idx = self.get_hopseq_idx(hop_seq, fst_ch, 0)
        if fst_idx == -1:
            return -1

        sec_idx = self.get_hopseq_idx(hop_seq, sec_ch, fst_idx)
        if sec_idx == -1:
            return -1

        distance = sec_idx - fst_idx

        if fst_idx > sec_idx:
            distance += 37

        return distance


    def _find_troikas(self):
        r"""找出所有可以用于破解 hop increment 的 troikas。"""
        dh_tab = {}

        for unique_ch in self.unique_chs:
            for ch in self.remapping_tab:
                for hop_inc in range(MIN_HOPINCRE, MAX_HOPINCRE + 1):
                    distance = self._compute_distance(self.hop_seqs[hop_inc], unique_ch, ch)
                    if distance == -1:
                        dh_tab.clear()
                        print("[Error] distance == -1")
                        break
                    elif distance in dh_tab:
                        dh_tab.clear()
                        break
                    else:
                        dh_tab[distance] = hop_inc

                if len(dh_tab) == MAX_HOPINCRE - MIN_HOPINCRE + 1:
                    self.troikas.append(
                        { 'unique_ch': unique_ch,
                          'exp_ch': ch,
                          'dh_tab': copy.deepcopy(dh_tab) }
                    )

                    dh_tab.clear()

        print("[Debug] troikas:", self.troikas)


def test():
    test_aa = b'\xD6\x8D\x9A\xAF'  # 0xAF9A8DD6
    test_chm = b'\x00\x8C\xFC\xFE\x1F' # 0x1ffefc8c00
    test_conn = LLConn(test_aa, True)
    test_conn.set_channel_map(test_chm)


if __name__ == "__main__":
    test()
