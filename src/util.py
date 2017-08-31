from collections import deque

def read_varlen(byte_iter):
    '''Reads a variable length quantity from an iterator'''
    byte = next(byte_iter)
    if not _has_next_byte(byte):
        return byte
    value = _remove_flag(byte)
    while _has_next_byte(byte):
        byte = next(byte_iter)
        value <<= 7
        value += (byte & 0x7f)
    return value

def write_varlen(value):
    '''Translates a value to a max-4-byte variable length quantity'''
    chrs = deque()
    chrs.appendleft(bytes([_7_bit_mask(value)]))
    value >>= 7
    while value:
        chrs.appendleft(bytes([_flag_next_byte(_7_bit_mask(value))]))
        value >>= 7
    return b''.join(chrs)

def _has_next_byte(byte):
    '''Determine if stream has a next byte by checking the MSB'''
    return byte & 0x80

def _flag_next_byte(byte):
    '''Flag the MSB to indicate more bytes incoming'''
    return byte | 0x80

def _remove_flag(byte):
    '''Extract value from byte by masking last 7 bits'''
    return byte & 0x7f

# alias
_7_bit_mask = _remove_flag