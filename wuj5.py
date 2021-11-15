#!/usr/bin/env python3


from argparse import ArgumentParser
from dataclasses import dataclass
import json5
import os
import struct


def unpack_u16(in_data, offset):
    return struct.unpack_from('>H', in_data, offset)[0]

def unpack_u32(in_data, offset):
    return struct.unpack_from('>I', in_data, offset)[0]

def unpack_bool(in_data, offset):
    return unpack_u16(in_data, offset) != 0

def unpack_f32(in_data, offset):
    return round(struct.unpack_from('>f', in_data, offset)[0], 6)

def unpack_string(in_data, offset, strings_offset):
    offset = strings_offset + unpack_u16(in_data, offset)
    return in_data[offset:].split(b'\0')[0].decode('ascii')

def unpack_struct(fields, in_data, struct_offset, strings_offset):
    val = {}
    offset = struct_offset
    for field in fields:
        field_val = field.unpack(in_data, struct_offset, offset, strings_offset)
        if field_val is not None:
            val[field.name] = field_val
        offset += field.size()
    return val

def unpack_array(fields, in_data, struct_offset, array_offset, strings_offset):
    offset = struct_offset + unpack_u16(in_data, array_offset + 0x0)
    count = unpack_u16(in_data, array_offset + 0x2)
    size = sum(field.size() for field in fields)
    return [unpack_struct(fields, in_data, offset + i * size, strings_offset) for i in range(count)]

def pack_u16(val):
    return struct.pack('>H', val)

def pack_u32(val):
    return struct.pack('>I', val)

def pack_bool(val):
    return pack_u16(val)

def pack_f32(val):
    return struct.pack('>f', val)

def pack_string(val, strings):
    offset = strings.insert(val)
    return pack_u16(offset)

def pack_struct(fields, val, strings):
    size = sum(field.size() for field in fields)
    buffer = Buffer(size)
    out_data = b''.join([field.pack(val.get(field.name), buffer, strings) for field in fields])
    return out_data + buffer.buffer

def pack_array(fields, vals, buffer, strings):
    offset = buffer.size()
    for val in vals:
        buffer.push(pack_struct(fields, val, strings))
    return struct.pack('>HH', offset, len(vals))

@dataclass
class Field:
    kind: str
    name: str
    array_fields: list = None

    def size(self):
        return {
            'pad16': 0x2,
            'u16': 0x2,
            'u32': 0x4,
            'bool': 0x2,
            'f32': 0x4,
            'string': 0x2,
            'array': 0x4,
        }[self.kind]

    def unpack(self, in_data, struct_offset, offset, strings_offset):
        if self.kind == 'pad16':
            return None
        elif self.kind == 'u16':
            return unpack_u16(in_data, offset)
        elif self.kind == 'u32':
            return unpack_u32(in_data, offset)
        elif self.kind == 'bool':
            return unpack_bool(in_data, offset)
        elif self.kind == 'f32':
            return unpack_f32(in_data, offset)
        elif self.kind == 'string':
            return unpack_string(in_data, offset, strings_offset)
        elif self.kind == 'array':
            return unpack_array(self.array_fields, in_data, struct_offset, offset, strings_offset)
        else:
            exit(f'Invalid field kind {self.kind}.')

    def pack(self, val, buffer, strings):
        if self.kind == 'pad16':
            return b'\x00\x00'
        elif self.kind == 'u16':
            return pack_u16(val)
        elif self.kind == 'u32':
            return pack_u32(val)
        elif self.kind == 'bool':
            return pack_bool(val)
        elif self.kind == 'f32':
            return pack_f32(val)
        elif self.kind == 'string':
            return pack_string(val, strings)
        elif self.kind == 'array':
            return pack_array(self.array_fields, val, buffer, strings)
        else:
            exit(f'Invalid field kind {self.kind}.')

class Buffer:
    def __init__(self, offset):
        self.buffer = b''
        self.offset = offset

    def size(self):
        return self.offset + len(self.buffer)

    def push(self, data):
        self.buffer += data

class Strings:
    def __init__(self):
        self.buffer = b'\0'
        self.offsets = { '': 0 }

    def insert(self, string):
        if string in self.offsets:
            return self.offsets[string]

        offset = len(self.buffer)
        self.offsets[string] = offset
        self.buffer += string.encode('ascii') + b'\0'
        return offset


animation_header_fields = [
    Field('array', 'groups', [
        Field('string', 'name'),
        Field('string', 'pane'),
        Field('u16', 'first animation'),
        Field('u16', 'animation count'),
    ]),
    Field('array', 'animations', [
        Field('string', 'name'),
        Field('string', 'brlan'),
        Field('string', 'next'),
        Field('bool', 'reversed'),
        Field('f32', 'speed'),
    ]),
]

layout_header_fields = [
    Field('array', 'variants', [
        Field('string', 'name'),
        Field('u16', 'opacity'),
        Field('bool', 'animated'),
        Field('pad16', ''),
        Field('f32', 'animation delay'),
        Field('f32', 'translation x 4:3'),
        Field('f32', 'translation y 4:3'),
        Field('f32', 'translation z 4:3'),
        Field('f32', 'scale x 4:3'),
        Field('f32', 'scale y 4:3'),
        Field('f32', 'translation x 16:9'),
        Field('f32', 'translation y 16:9'),
        Field('f32', 'translation z 16:9'),
        Field('f32', 'scale x 16:9'),
        Field('f32', 'scale y 16:9'),
        Field('u16', 'first message'),
        Field('u16', 'message count'),
        Field('u16', 'first picture'),
        Field('u16', 'picture count'),
    ]),
    Field('array', 'messages', [
        Field('string', 'pane'),
        Field('string', 'name'),
        Field('u32', 'message id'),
    ]),
    Field('array', 'pictures', [
        Field('string', 'destination pane'),
        Field('string', 'source pane'),
    ]),
]

def unpack_brctr(in_data):
    strings_offset = unpack_u16(in_data, 0x10)
    animation_header_offset = unpack_u16(in_data, 0x0c)
    layout_header_offset = unpack_u16(in_data, 0x0e)

    return {
        'main brlyt': unpack_string(in_data, 0x06, strings_offset),
        'bmg': unpack_string(in_data, 0x08, strings_offset),
        'picture source brlyt': unpack_string(in_data, 0x0a, strings_offset),
        **unpack_struct(animation_header_fields, in_data, animation_header_offset, strings_offset),
        **unpack_struct(layout_header_fields, in_data, layout_header_offset, strings_offset),
    }

def pack_brctr(val):
    strings = Strings()

    header_data = b''.join([
        b'bctr\x00\x02',
        pack_string(val['main brlyt'], strings),
        pack_string(val['bmg'], strings),
        pack_string(val['picture source brlyt'], strings),
    ])

    animation_val = { field.name: val[field.name] for field in animation_header_fields }
    animation_data = pack_struct(animation_header_fields, animation_val, strings)
    layout_val = { field.name: val[field.name] for field in layout_header_fields }
    layout_data = pack_struct(layout_header_fields, layout_val, strings)

    offset = 0x14
    header_data += pack_u16(offset)
    offset += len(animation_data)
    header_data += pack_u16(offset)
    offset += len(layout_data)
    header_data += pack_u16(offset)
    header_data += b'\x00\x00'

    return header_data + animation_data + layout_data + strings.buffer


def decode(in_path):
    in_file = open(in_path, 'rb')
    in_data = in_file.read()
    magic = in_data[0:4]
    if magic != b'bctr':
        exit('Unknown file format.')
    val = unpack_brctr(in_data)
    out_data = json5.dumps(val, indent = 4, quote_keys = True)
    out_path = os.path.splitext(in_path)[0] + '.json5'
    out_file = open(out_path, 'w')
    out_file.write(out_data)

def encode(in_path):
    in_file = open(in_path, 'r')
    in_data = in_file.read()
    val = json5.loads(in_data)
    out_data = pack_brctr(val)
    out_path = os.path.splitext(in_path)[0] + '.brctr'
    out_file = open(out_path, 'wb')
    out_file.write(out_data)


parser = ArgumentParser()
parser.add_argument('operation', choices = ['decode', 'encode'])
parser.add_argument('in_path')
args = parser.parse_args()

operations = {
    'decode': decode,
    'encode': encode,
}
operations[args.operation](args.in_path)
