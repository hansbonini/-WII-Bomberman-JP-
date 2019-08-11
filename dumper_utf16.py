#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import textwrap
import codecs
import os
import sys
import json

class Dumper(object):

    offsets = []
    strings = []

    control_bytes = {
        b'\x00\x00'     :   '[ENDSTRING]',
    }

    control_codes = {
        '\u000b'        :   '[READ_MORE]',
        '\u0000'        :   '[WAIT_A_SECOND]',
        '\u0006\u0001'  :   '[つよし]',
        '\u0301'        :   '[FONTE]',
        '\u0601'        :   '[DIMINUI FONTE]'
    }

    def __init__(self, data, filename):
        self.binary = BinaryFile(data)
        self.scripts_file = open('./scripts/'+os.path.splitext(os.path.basename(filename))[0]+'.json', 'w+')
        self.start()

    def start(self):

        self.binary.skip(4)

        while True:
            data = self.binary.read(4)
            if data.value[0:2] != b'\x00\x00':
                break
            self.offsets.append(data.as_integer)

        for offset in self.offsets:
            print(hex(offset))
            self.binary.seek(offset)
            output_text = ""
            while True:
                data = self.binary.read(1)
                n_data = self.binary.read_next(1)

                test = data.value
                test+=(n_data.value)

                if test in self.control_bytes:
                    if self.control_bytes[test] == '[ENDSTRING]':
                        self.binary.skip(1)
                        for target, control_code in self.control_codes.items():
                            output_text = output_text.replace(target, control_code)
                        self.strings.append(output_text)
                        break
                else:
                    if int.from_bytes(test, 'big') in range(0x8140,0xEAA2):
                        self.binary.skip(1)
                        shiftjis = str(test, "utf-16") # Converte de UTF-16 para UTF-8
                        output_text += codecs.encode(shiftjis, "utf-8").decode('utf-8')
                    else:
                        output_text += data.as_string

        json.dump(self.strings, self.scripts_file, indent=4, ensure_ascii=False)

class BinaryFile(object):

    def __init__(self, data):
        self.start_offset = 0
        self.current_offset = 0
        self.content = data
        self.end_offset = len(data)

    def read(self, nbytes):
        value = self.content[self.current_offset:(self.current_offset+nbytes)]
        self.current_offset += nbytes
        return BinaryBytes(value)

    def read_next(self, nbytes):
        value = self.content[self.current_offset:(self.current_offset+nbytes)]
        return BinaryBytes(value)

    def skip(self, nbytes):
        self.current_offset += nbytes

    def seek(self, nbytes):
        self.current_offset = nbytes


class BinaryBytes(object):
    def __init__(self, byte_value):
        self.value = byte_value
        self.as_integer = int.from_bytes(byte_value, 'big')
        try:
            self.as_string = str(byte_value.decode("ascii"))
        except Exception:
            self.as_string = ""

if __name__ == '__main__':
    """ Program Command Line """
    cmd = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
            [BOMBERMAN] TEXT DUMPER
            --------------------------------------------------
            python dumper.py input
            --------------------------------------------------
            Tool to extract bomberman texts from decompressed
            binary files
        ''')
    )

    cmd.add_argument(
        'infile',
        nargs='?',
        type=argparse.FileType('rb'),
        default=sys.stdin,
        help='Input file.'
    )

    """ Program Main Routine """
    args = cmd.parse_args()

    if(args.infile.name != '<stdin>'):
        with args.infile as input_file:
            file_content = input_file.read()
        Dumper(file_content, args.infile.name)
    else:
        cmd.print_help()