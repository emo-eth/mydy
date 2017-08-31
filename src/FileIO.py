'''
Classes for reading and writing MIDI files
'''
from warnings import warn
from struct import unpack, pack
from util import read_varlen, write_varlen
from Constants import DEFAULT_MIDI_HEADER_SIZE
from Containers import Track, Pattern
from Events import MetaEvent, SysexEvent, EventRegistry, UnknownMetaEvent


class FileReader(object):

    CHUNK_SIZE = 4  # size of midi file or track header in bytes
    HEADER_SIZE = 10  # size of midi header contents in bytes

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
            buffer.read(header_size - DEFAULT_MIDI_HEADER_SIZE)
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
        '''Parse a MIDI track into a tuple of events'''
        self.running_status = None
        track_size = self.parse_track_header(buffer)
        track_data = iter(buffer.read(track_size))
        events = []
        while track_data:
            try:
                event = self.parse_event(track_data)
                events.append(event)
            except StopIteration:
                break
        return tuple(events)


    def parse_track_header(self, buffer):
        '''Parse track information from header
        Return track size in bytes'''
        header = buffer.read(self.CHUNK_SIZE)
        if header != b'MTrk':
            raise TypeError("Bad track header in midi file: " + str(header))
        track_size = unpack('>L', buffer.read(4))[0]
        return track_size

    def parse_event(self, track_iter):
        '''Parses an event from a byte iterator.
        Returns a MidiEvent, SysexEvent, or MetaEvent, or subclass thereof'''
        tick = read_varlen(track_iter)
        header_byte = next(track_iter)
        if SysexEvent.is_event(header_byte):
            return self.parse_sysex_event(tick, track_iter)
        elif MetaEvent.is_event(header_byte):
            return self.parse_meta_event(tick, track_iter)
        return self.parse_midi_event(tick, header_byte, track_iter)
        

    def parse_sysex_event(tick, track_iter):
        '''
        Return a SysexEvent object given a tick and track_iter byte iterator
        '''
        payload = []
        byte = next(track_iter)
        # 0xF7 signals end of Sysex data stream
        while byte != 0xF7:
            payload.append(byte)
            byte = next(track_iter)
        return SysexEvent(tick=tick, data=payload)


    def parse_meta_event(self, tick, track_iter):
        '''
        Parse and return a MetaEvent subclass from a byte iterator
        '''
        metacommand = next(track_iter)
        if metacommand not in EventRegistry.MetaEvents:
            warn('Unknown Meta MIDI Event: ' + str(metacommand), Warning)
            cls = UnknownMetaEvent
        else:
            cls = EventRegistry.MetaEvents[metacommand]
        length = read_varlen(track_iter)
        data = [next(track_iter) for x in range(length)]
        return cls(tick=tick, data=data, metacommand=metacommand)
        


    def parse_midi_event(self, tick, header_byte, track_iter):
        '''
        Parse and return a standard MIDI event
        '''
        key = header_byte & 0xF0
        # if this key isn't an event, it's data for an event of
        # the same time we just parsed
        if key not in EventRegistry.Events:
            assert self.running_status, 'Bad byte value'
            data = []
            key = self.running_status & 0xF0
            cls = EventRegistry.Events[key]
            channel = self.running_status & 0xF
            data.append(header_byte)
            data += [next(track_iter) for x in range(cls.length - 1)]
            return cls(tick=tick, channel=channel, data=data)
        else:
            self.running_status = header_byte
            cls = EventRegistry.Events[key]
            channel = self.running_status & 0xF
            data = [next(track_iter) for x in range(cls.length)]
            return cls(tick=tick, channel=channel, data=data)
        raise Warning("Uknown midi event: " + str(header_byte))
