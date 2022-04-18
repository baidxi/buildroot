#!/usr/bin/env python3

from serial import Serial
from serial import SerialException
from serial.tools.list_ports import comports

serial_dev = None
EVT_LEN = 100
UPPER_CMD_LEN = 100
OP_CRACK_CHM = 4

def get_microbit_serial_dev_path():
    for port in comports():
        if "mbed" in port.description:
            return port.device
    
    return ""

def serial_crack_chm(aa:bytes, crc_init:bytes):
    r"""Send OP_CRACK_CHM to lower computer

    +-----------------------------+
    | Op   | Len  | AA  | CRCInit |
    |------|------|-----|---------|
    | 0x04 | 0x07 | 4 B | 3 B     |
    +-----------------------------+

    CRCInit is little-endian.
    """
    upper_cmd = bytearray(UPPER_CMD_LEN)
    upper_cmd[0] = OP_CRACK_CHM
    upper_cmd[1] = 7
    upper_cmd = upper_cmd.replace(b'\x00\x00\x00\x00', aa, 1)
    upper_cmd = upper_cmd.replace(b'\x00\x00\x00', crc_init, 1)
    #print("[Debug] upper_cmd", upper_cmd)
    serial_dev.write(upper_cmd)

def main():
    global serial_dev

    dev_path = get_microbit_serial_dev_path()
    serial_dev = Serial(dev_path, 115200, timeout=1)
    
    serial_dev.reset_input_buffer()
    serial_dev.reset_output_buffer()
    serial_crack_chm(b'\x29\x5c\x65\x50', b'\x1b\x23\x63')

    while True:
        lower_cmd = serial_dev.read(EVT_LEN)
        print("[Test]")
        print(lower_cmd)
        print()


if __name__ == "__main__":
    try:
        #test()
        main()
    except KeyboardInterrupt:
        if serial_dev:
            serial_dev.reset_input_buffer()
            serial_dev.reset_output_buffer()
            serial_dev.close()
    except SerialException as e:
        print(e)