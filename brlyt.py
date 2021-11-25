from common import *


def unpack_string64(in_data, offset, **kwargs):
    return in_data[offset:offset + 0x8].decode('ascii').rstrip('\x00')

def unpack_string128(in_data, offset, **kwargs):
    return in_data[offset:offset + 0x10].decode('ascii').rstrip('\x00')

def unpack_array(in_data, offset, **kwargs):
    size = kwargs['size']
    start_offset = kwargs['start_offset']
    fields = kwargs['fields']
    start_offset += offset
    count = unpack_u16(in_data, offset)
    size = sum(size[field.kind] for field in fields)
    return [unpack_struct(in_data, start_offset + i * size, **kwargs) for i in range(count)]

brlyt_size = {
    **size,
    'string64': 0x8,
    'string128': 0x10,
    'array': 0x2,
}

brlyt_unpack = {
    **unpack,
    'string64': unpack_string64,
    'string128': unpack_string128,
    'array': unpack_array,
}


base_fields = [
    Field('magic', 'magic'),
    Field('u32', 'size'),
]

lyt1_fields = [
    *base_fields,
    Field('bool8', 'centered'),
    Field('pad24', None),
    Field('f32', 'size x'),
    Field('f32', 'size y'),
]

txl1_fields = [
    *base_fields,
    Field('array', 'tpls', start_offset = 0x4, fields = [
        Field('u32', 'name'),
        Field('pad32', None),
    ])
]

fnl1_fields = [
    *base_fields,
]

mat1_fields = [
    *base_fields,
]

pan1_fields = [
    *base_fields,
    Field('pad32', None), # FIXME
    Field('string128', 'name'),
    Field('string64', 'user data'),
    Field('f32', 'translation x'),
    Field('f32', 'translation y'),
    Field('f32', 'translation z'),
    Field('f32', 'rotation x'),
    Field('f32', 'rotation y'),
    Field('f32', 'rotation z'),
    Field('f32', 'scale x'),
    Field('f32', 'scale y'),
    Field('f32', 'size x'),
    Field('f32', 'size y'),
]

pas1_fields = [
    *base_fields,
]

pae1_fields = [
    *base_fields,
]

pic1_fields = [
    *pan1_fields,
]

bnd1_fields = [
    *pan1_fields,
]

txt1_fields = [
    *pan1_fields,
]

wnd1_fields = [
    *pan1_fields,
]

grp1_fields = [
    *base_fields,
    Field('string128', 'name'),
    Field('array', 'panes', start_offset = 0x4, fields = [
        Field('string128', 'name'),
    ]),
    Field('pad16', None),
]

grs1_fields = [
    *base_fields,
]

gre1_fields = [
    *base_fields,
]

def unpack_sections(in_data, offset, parent_magic):
    sections = []
    last_section = None
    while offset < len(in_data):
        magic = unpack_magic(in_data, offset + 0x00)
        section_size = unpack_u32(in_data, offset + 0x04)
        fields = {
            'lyt1': lyt1_fields,
            'txl1': txl1_fields,
            'fnl1': fnl1_fields,
            'mat1': mat1_fields,
            'pan1': pan1_fields,
            'pas1': pas1_fields,
            'pae1': pae1_fields,
            'pic1': pic1_fields,
            'bnd1': bnd1_fields,
            'txt1': txt1_fields,
            'wnd1': wnd1_fields,
            'grp1': grp1_fields,
            'grs1': grs1_fields,
            'gre1': gre1_fields,
        }[magic]
        kwargs = {
            'size': brlyt_size,
            'unpack': brlyt_unpack,
            'fields': fields,
        }
        section = unpack_struct(in_data, offset, **kwargs)
        del section['size']
        offset += section_size
        if magic == 'pas1' or magic == 'grs1':
            expected_last_magic = {
                'pas1': 'pan1',
                'grs1': 'grp1',
            }[magic]
            last_magic = last_section.get('magic')
            if last_magic != expected_last_magic:
                exit(f'Unexpected {magic} after {last_magic}.')
            offset, child_sections = unpack_sections(in_data, offset, last_magic)
            last_section['children'] = child_sections
        elif magic == 'pae1' or magic == 'gre1':
            expected_parent_magic = {
                'pae1': 'pan1',
                'gre1': 'grp1',
            }[magic]
            if parent_magic != expected_parent_magic:
                exit(f'Unexpected {magic} after {parent_magic}.')
            break
        else:
            sections += [section]
        last_section = section
    return offset, sections

def unpack_brlyt(in_data):
    return {
        'version': unpack_u16(in_data, 0x06),
        'sections': unpack_sections(in_data, 0x10, None)[1]
    }
