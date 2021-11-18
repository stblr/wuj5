import struct


def unpack_pad16(in_data, offset, **kwargs):
    return None

def unpack_pad32(in_data, offset, **kwargs):
    return None

def unpack_u16(in_data, offset, **kwargs):
    return struct.unpack_from('>H', in_data, offset)[0]

def unpack_u32(in_data, offset, **kwargs):
    return struct.unpack_from('>I', in_data, offset)[0]

def unpack_bool16(in_data, offset, **kwargs):
    return unpack_u16(in_data, offset) != 0

def unpack_bool32(in_data, offset, **kwargs):
    return unpack_u32(in_data, offset) != 0

def unpack_f32(in_data, offset, **kwargs):
    return round(struct.unpack_from('>f', in_data, offset)[0], 6)

def unpack_magic(in_data, offset, **kwargs):
    return in_data[offset:offset + 4].decode('ascii')

def unpack_struct(in_data, offset, **kwargs):
    size = kwargs['size']
    unpack = kwargs['unpack']
    fields = kwargs['fields']
    val = {}
    field_offset = offset
    for field in fields:
        kwargs = {
            **kwargs,
            'struct_offset': offset,
            **field.kwargs,
        }
        field_val = unpack[field.kind](in_data, field_offset, **kwargs)
        if field_val is not None:
            val[field.name] = field_val
        field_offset += size[field.kind]
    return val

def pack_pad16(val, **kwargs):
    return b'\x00\x00'

def pack_pad32(val, **kwargs):
    return b'\x00\x00\x00\x00'

def pack_u16(val, **kwargs):
    return struct.pack('>H', val)

def pack_u32(val, **kwargs):
    return struct.pack('>I', val)

def pack_bool16(val, **kwargs):
    return pack_u16(val)

def pack_f32(val, **kwargs):
    return struct.pack('>f', val)

def pack_magic(val, **kwargs):
    return val

def pack_struct(val, **kwargs):
    size = kwargs['size']
    pack = kwargs['pack']
    fields = kwargs['fields']
    size = sum(size[field.kind] for field in fields)
    out_data = b''
    for field in fields:
        kwargs = {
            **kwargs,
            **field.kwargs,
        }
        out_data += pack[field.kind](val.get(field.name), **kwargs)
    return out_data

size = {
    'pad16': 0x2,
    'pad32': 0x4,
    'u16': 0x2,
    'u32': 0x4,
    'bool16': 0x2,
    'bool32': 0x4,
    'f32': 0x4,
    'magic': 0x4,
}

unpack = {
    'pad16': unpack_pad16,
    'pad32': unpack_pad32,
    'u16': unpack_u16,
    'u32': unpack_u32,
    'bool16': unpack_bool16,
    'bool32': unpack_bool32,
    'f32': unpack_f32,
    'magic': unpack_magic,
}

pack = {
    'pad16': pack_pad16,
    'pad32': pack_pad32,
    'u16': pack_u16,
    'u32': pack_u32,
    'bool16': pack_bool16,
    'f32': pack_f32,
}

class Field:
    def __init__(self, kind, name, **kwargs):
        self.kind = kind
        self.name = name
        self.kwargs = kwargs
