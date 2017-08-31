from warnings import warn
from struct import unpack, pack
from util import read_varlen, write_varlen
from Constants import DEFAULT_MIDI_HEADER_SIZE
from Containers import Track, Pattern, MidiEvent, SysexEvent, MetaEvent
from itertools import cycle
import numpy as np



class FileReader(object):

    CHUNK_SIZE = 4  # size of midi file or track header in bytes
    HEADER_SIZE = 10  # size of midi header contents in bytes
    HAS_TWO_DATA_BYTES = {
        0b1000: "Note Off",
        0b1001: "Note On",
        0b1010: "Polyphonic Key Pressure (Aftertouch)",
        0b1011: "CC",
        0b1110: "Pitch Wheel Change",
        0b1011: "Channel Mode Messages",
        0b11110010: "Song Position Pointer",

    }

    HAS_ONE_DATA_BYTE = {
        0b1100: "Program Change",
        0b1101: "Channel Pressure (Aftertouch)",
        0b11110011: "Song Select"
    }


    def read(self, buffer):
        '''Read a midi file from a buffer'''
        print(type(buffer))
        pattern = self.parse_file_header(buffer)
        for track in pattern.tracks:
            self.parse_track(buffer)
        return pattern


    def parse_file_header(self, buffer):
        '''Parse header information from a buffer and return a Pattern based on
        that information.'''
        header = buffer.read(self.CHUNK_SIZE)
        if header != b'MThd':
            raise TypeError("Bad header in MIDI file")
        # a long followed by three shorts
        data = unpack(">LHHH", buffer.read(self.HEADER_SIZE))
        print(data)
        header_size = data[0]
        fmt = data[1]
        num_tracks = data[2]
        division = self.parse_division(data[3])
        # assume any remaining bytes in header are padding
        if header_size > DEFAULT_MIDI_HEADER_SIZE:
            print('>>' + str(buffer.read(header_size - DEFAULT_MIDI_HEADER_SIZE)))
        return Pattern(fmt, num_tracks, division)


    def parse_division(self, division):
        '''Parse division information in MIDI header, either ticks per quarter note
        or SMPTE information'''
        if division & 0x80000:
            smpte = (division >> 7) | 0x7f
            ticks_per_frame = division | 0x7f
            return (smpte, ticks_per_frame)
        return (division,)


    def parse_track(self, buffer):
        '''Parse a MIDI track into a tuple'''
        track_size = self.parse_track_header(buffer)
        track_data = iter(buffer.read(track_size))
        events = []
        while track_data:
            try:
                event = self.parse_event(track_data)
                events.append(event)
            except StopIteration:
                break
        # print length in bytes
        s = 0
        for ev in events:
            s += 2 + len(ev.data)
        print(s)
        print(events)
        return tuple(events)


    def parse_track_header(self, buffer):
        '''Parse track information from header
        Return track size in bytes'''
        header = buffer.read(self.CHUNK_SIZE)
        if header != b'MTrk':
            raise TypeError("Bad track header in midi file: " + str(header))
        track_size = unpack('>L', buffer.read(4))[0]
        print(track_size)
        return track_size

    def parse_event(self, track_iter):
        '''Parses an event from a byte iterator.
        Returns a MidiEvent, SysexEvent, or MetaEvent'''
        delta_time = read_varlen(track_iter)
        header_byte = next(track_iter)
        if header_byte == 0xF0 or header_byte == 0xF7:
            return SysexEvent(delta_time,
                              *self.parse_sysex_event(header_byte, track_iter))
        elif header_byte == 0xFF:
            return MetaEvent(delta_time, *self.parse_meta_event(header_byte, track_iter))
        return MidiEvent(delta_time, *self.parse_midi_event(header_byte, track_iter))
        

    def parse_sysex_event(header_byte, track_data):
        length = read_varlen(track_data)
        payload = [next(track_data) for _ in range(length)]
        payload = []
        byte = next(track_data)
        while byte != 0xF7:
            # TODO: remember to write this out ^
            # TODO: write comments that make sense in the future
            payload.append(byte)
            byte = next(track_data)
        return [header_byte, length] + payload
        # return [bytes([header_byte]) + write_varlen(length) + payload, None, None]


    def parse_meta_event(self, header_byte, track_data):
        type_ = next(track_data)
        length = read_varlen(track_data)
        payload = [next(track_data) for _ in range(length)]
        return [header_byte, type_, length] + payload
        # return [bytes([header_byte, type_]) + write_varlen(length) + payload, None, None]


    def parse_midi_event(self, status, track_data):
        num_bytes = self.num_payload_bytes(status)
        payload = []
        for _ in range(num_bytes):
            payload.append(next(track_data))
        return [status] + payload


    def num_payload_bytes(self, status):
        # print(f'{status:08b}')
        half_byte = status >> 4
        # check if system message, need full byte
        if half_byte == 0b1001:
            print('on!!!')
        if half_byte == 0b1111:
            code = status
        else:
            code = half_byte
        if code in self.HAS_TWO_DATA_BYTES:
            return 2
        elif code in self.HAS_ONE_DATA_BYTE:
            return 1
        return 0