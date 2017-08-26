from warnings import warn
from struct import unpack, pack
from util import read_varlen, write_varlen
from Constants import DEFAULT_MIDI_HEADER_SIZE
from Containers import Track, Pattern
import numpy as np


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


def read(buffer):
    '''Read a midi file from a buffer'''
    pattern = parse_file_header(buffer)
    for track in pattern.tracks:
        parse_track(buffer)
    return pattern


def parse_file_header(buffer):
    '''Parse header information from a buffer'''
    header = buffer.read(CHUNK_SIZE)
    if header != b'MThd':
        raise TypeError("Bad header in MIDI file")
    # a long followed by three shorts
    data = unpack(">LHHH", buffer.read(HEADER_SIZE))
    header_size = data[0]
    fmt = data[1]
    num_tracks = data[2]
    division = parse_division(data[3])
    # assume any remaining bytes in header are padding
    if header_size > DEFAULT_MIDI_HEADER_SIZE:
        buffer.read(header_size - DEFAULT_MIDI_HEADER_SIZE)
    return Pattern(fmt, num_tracks, division)


def parse_division(division):
    '''Parse division information in MIDI header, either ticks per quarter note
    or SMPTE information'''
    if division & 0x80000:
        smpte = (division >> 7) | 0x7f
        ticks_per_frame = division | 0x7f
        return (smpte, ticks_per_frame)
    return (division,)


def parse_track(buffer):
    '''Parse a MIDI track into an ndarray'''
    track_size = parse_track_header(buffer)
    track_data = iter(bytearray(buffer.read(track_size)))
    events = np.empty((0,))
    while track_data:
        try:
            event = parse_track_event(track_data)
            events = np.concatenate((events, event))
        except StopIteration:
            break
    events = np.reshape(events, (int(len(events) / 4), 4))
    return events


def parse_track_header(buffer):
    '''Parse track information from header
    Return track size in bytes'''
    header = buffer.read(CHUNK_SIZE)
    if header != b'MTrk':
        raise TypeError("Bad track header in midi file: " + str(header))
    track_size = unpack(">L", buffer.read(4))[0]
    return track_size


def parse_track_event(track_iter):
    delta_time = read_varlen(track_iter)
    event = parse_event(track_iter)
    return np.array([delta_time] + event)


def parse_event(track_iter):
    '''Parse an event as a length-4 array'''
    header_byte = next(track_iter)
    if header_byte == 0xF0 or header_byte == 0xF7:
        event = parse_sysex_event(header_byte, track_iter)
    elif header_byte == 0xFF:
        event = parse_meta_event(header_byte, track_iter)
    else:
        event = parse_midi_event(header_byte, track_iter)
    return event


def parse_sysex_event(header_byte, track_data):
    length = read_varlen(track_data)
    payload = bytes([next(track_data) for _ in range(length)])
    return [bytes([header_byte]) + write_varlen(length) + payload, None, None]


def parse_meta_event(header_byte, track_data):
    type_ = next(track_data)
    length = read_varlen(track_data)
    payload = bytes([next(track_data) for _ in range(length)])
    return [bytes([header_byte, type_]) + write_varlen(length) + payload, None, None]


def parse_midi_event(status, track_data):
    num_bytes = num_payload_bytes(status)
    payload = [None, None]
    if num_bytes == 2:
        payload[0] = next(track_data)
        payload[1] = next(track_data)
    elif num_bytes == 1:
        payload[0] = next(track_data)
    return [status] + payload


def num_payload_bytes(status):
    half_byte = status >> 4
    # check if system message, need full byte
    if half_byte == 0b1111:
        code = status
    else:
        code = half_byte
    if code in HAS_TWO_DATA_BYTES:
        return 2
    elif code in HAS_ONE_DATA_BYTE:
        return 1
    return 0


class FileReader(object):

    #     def parse_track_header(self, midifile):
    #         # First four bytes are Track header
    #         magic = midifile.read(4)
    #         if magic != b'MTrk':
    #             raise TypeError("Bad track header in MIDI file: " + magic)
    #         # next four bytes are track size
    #         trksz = unpack(">L", midifile.read(4))[0]
    #         return trksz

    #     def parse_track(self, midifile, track):
    #         self.RunningStatus = None
    #         trksz = self.parse_track_header(midifile)
    #         trackdata = iter(bytearray(midifile.read(trksz)))
    #         while True:
    #             try:
    #                 event = self.parse_midi_event(trackdata)
    #                 track.append(event)
    #             except StopIteration:
    #                 break

    #     def parse_midi_event(self, trackdata):
    #         # first datum is varlen representing delta-time
    #         tick = read_varlen(trackdata)
    #         # next byte is status message
    #         stsmsg = ord(trackdata.next())
    #         # is the event a MetaEvent?
    #         if MetaEvent.is_event(stsmsg):
    #             cmd = ord(trackdata.next())
    #             if cmd not in EventRegistry.MetaEvents:
    #                 warn("Unknown Meta MIDI Event: " + repr(cmd), Warning)
    #                 cls = UnknownMetaEvent
    #             else:
    #                 cls = EventRegistry.MetaEvents[cmd]
    #             datalen = read_varlen(trackdata)
    #             data = [ord(trackdata.next()) for x in range(datalen)]
    #             return cls(tick=tick, data=data, metacommand=cmd)
    #         # is this event a Sysex Event?
    #         elif SysexEvent.is_event(stsmsg):
    #             data = []
    #             while True:
    #                 datum = ord(trackdata.next())
    #                 if datum == 0xF7:
    #                     break
    #                 data.append(datum)
    #             return SysexEvent(tick=tick, data=data)
    #         # not a Meta MIDI event or a Sysex event, must be a general message
    #         else:
    #             key = stsmsg & 0xF0
    #             if key not in EventRegistry.Events:
    #                 assert self.RunningStatus, "Bad byte value"
    #                 data = []
    #                 key = self.RunningStatus & 0xF0
    #                 cls = EventRegistry.Events[key]
    #                 channel = self.RunningStatus & 0x0F
    #                 data.append(stsmsg)
    #                 data += [ord(trackdata.next()) for x in range(cls.length - 1)]
    #                 return cls(tick=tick, channel=channel, data=data)
    #             else:
    #                 self.RunningStatus = stsmsg
    #                 cls = EventRegistry.Events[key]
    #                 channel = self.RunningStatus & 0x0F
    #                 data = [ord(trackdata.next()) for x in range(cls.length)]
    #                 return cls(tick=tick, channel=channel, data=data)
    #         raise Warning("Unknown MIDI Event: " + repr(stsmsg))

    def read(self, midifile):
        pattern = self.parse_file_header(midifile)
        for track in pattern:
            self.parse_track(midifile, track)
        return pattern

    def parse_file_header(self, midifile):
        # First four bytes are MIDI header
        header = midifile.read(4)
        if header != b'MThd':
            raise TypeError("Bad header in MIDI file.")
        # next four bytes are header size
        # next two bytes specify the format version
        # next two bytes specify the number of tracks
        # next two bytes specify the resolution/PPQ/Parts Per Quarter
        # (in other words, how many ticks per quater note)
        data = unpack(">LHHH", midifile.read(10))
        header_size = data[0]
        fmt = data[1]
        tracks = [Track() for x in range(data[2])]
        resolution = data[3]
        # the assumption is that any remaining bytes
        # in the header are padding
        if header_size > DEFAULT_MIDI_HEADER_SIZE:
            midifile.read(header_size - DEFAULT_MIDI_HEADER_SIZE)
        return Pattern(tracks=tracks, resolution=resolution, format=fmt)

# class FileWriter(object):
#     def write(self, midifile, pattern):
#         self.write_file_header(midifile, pattern)
#         for track in pattern:
#             self.write_track(midifile, track)

#     def write_file_header(self, midifile, pattern):
#         # First four bytes are MIDI header
#         packdata = pack(">LHHH", 6,
#                             pattern.format,
#                             len(pattern),
#                             pattern.resolution)
#         midifile.write(b'MThd' + packdata)

#     def write_track(self, midifile, track):
#         buf = b''
#         self.RunningStatus = None
#         for event in track:
#             buf += self.encode_midi_event(event)
#         buf = self.encode_track_header(len(buf)) + buf
#         midifile.write(buf)

#     def encode_track_header(self, trklen):
#         return b'MTrk' + pack(">L", trklen)

#     def encode_midi_event(self, event):
#         ret = bytearray()
#         ret += write_varlen(event.tick)
#         # is the event a MetaEvent?
#         if isinstance(event, MetaEvent):
#             ret += bytearray(event.statusmsg + event.metacommand)
#             ret += write_varlen(len(event.data))
#             ret += bytearray(event.data)
#         # is this event a Sysex Event?
#         elif isinstance(event, SysexEvent):
#             ret.append(0xF0)
#             ret += bytearray(event.data)
#             ret.append(0xF7)
#         # not a Meta MIDI event or a Sysex event, must be a general message
#         elif isinstance(event, Event):
#             if not self.RunningStatus or \
#                 self.RunningStatus.statusmsg != event.statusmsg or \
#                 self.RunningStatus.channel != event.channel:
#                     self.RunningStatus = event
#                     ret.append(event.statusmsg | event.channel)
#             ret += bytearray(event.data)
#         else:
#             raise ValueError("Unknown MIDI Event: " + str(event))
#         return ret

# def write_midifile(midifile, pattern):
#     if not hasattr(midifile, "write"):
#         midifile = open(midifile, 'wb')
#     writer = FileWriter()
#     return writer.write(midifile, pattern)

# def read_midifile(midifile):
#     if not hasattr(midifile, "read"):
#         midifile = open(midifile, 'rb')
#     reader = FileReader()
#     return reader.read(midifile)
