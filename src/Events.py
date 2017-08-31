'''
A collection of MIDI events
'''
import math
from six import with_metaclass


class EventRegistry(object):
    '''
    Class that registers the different Events and MetaEvents defined here.
    '''
    Events = {}
    MetaEvents = {}

    @classmethod
    def register_event(cls, event, bases):
        '''
        Add a class to the static Events or MetaEvents dictionaries
        '''
        print(Event in bases, MetaEvent in bases)

        if (Event in bases) or (NoteEvent in bases):
            assert event.status not in cls.Events, \
                "Event %s already registered" % event.name
            cls.Events[event.status] = event
        elif (MetaEvent in bases) or (MetaEventWithText in bases):
            if event.metacommand is not None:
                assert event.metacommand not in cls.MetaEvents, \
                    "Event %s already registered" % event.name
                cls.MetaEvents[event.metacommand] = event
        else:
            raise ValueError("Unknown bases class in event type: ", event.name)


class EventMetaclass(type):
    '''
    Metaclass for MIDI events, which registers classes with EventRegistry as
    they are declared.
    '''

    def __init__(cls, name, superclasses, attributedict):
        if name not in ['AbstractEvent', 'Event', 'MetaEvent', 'NoteEvent',
                        'MetaEventWithText']:
            EventRegistry.register_event(cls, superclasses)


class AbstractEvent(metaclass=EventMetaclass):
    '''
    Abstract MIDI event, from which Event and MetaEvent inherit.
    '''

    __slots__ = ['tick', 'data']
    name = "Generic MIDI Event"
    length = 0
    status = 0x0

    def __init__(self, **kw):
        if isinstance(self.length, int):
            data = [0] * self.length
        else:
            data = []
        self.tick = 0
        self.data = data
        for key in kw:
            setattr(self, key, kw[key])

    def __lt__(self, other):
        if self.tick < other.tick:
            return True
        return self.data < other.data

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.tick == other.tick and
                self.data == other.data)

    def __ne__(self, other):
        return not self.__eq__(other)

    def _baserepr(self, keys=[]):
        keys = ['tick'] + keys + ['data']
        body = []
        for key in keys:
            val = getattr(self, key)
            keyval = "%s=%r" % (key, val)
            body.append(keyval)
        body = str.join(', ', body)
        return "midi.%s(%s)" % (self.__class__.__name__, body)

    def __repr__(self):
        return self._baserepr()


class Event(AbstractEvent):
    __slots__ = ['channel']
    name = 'Event'

    def __init__(self, **kw):
        if 'channel' not in kw:
            kw = kw.copy()
            kw['channel'] = 0
        super(Event, self).__init__(**kw)

    def copy(self, **kw):
        _kw = {'channel': self.channel, 'tick': self.tick, 'data': self.data}
        _kw.update(kw)
        return self.__class__(**_kw)

    def __lt__(self, other):
        return (super(Event, self).__lt__(other) or
                (super(Event, self).__eq__(other) and
                 self.channel < other.channel))

    def __eq__(self, other):
        return super(Event, self).__eq__(other) and \
            self.channel == other.channel

    def __repr__(self):
        return self._baserepr(['channel'])

    @classmethod
    def is_event(cls, status):
        return (cls.status == (status & 0xF0))


class MetaEvent(AbstractEvent):
    '''
    MetaEvent is a special subclass of Event that is not meant to
    be used as a concrete class.  It defines a subset of Events known
    as the Meta events.
    '''

    status = 0xFF
    metacommand = 0x0
    name = 'Meta Event'

    @classmethod
    def is_event(cls, status):
        return (status == cls.status)


class NoteEvent(Event):
    '''
    NoteEvent is a special subclass of Event that is not meant to
    be used as a concrete class.  It defines the generalities of NoteOn
    and NoteOff events.
    '''
    length = 2

    @property
    def pitch(self):
        return self.data[0]

    @pitch.setter
    def set_pitch(self, val):
        self.data[0] = val

    @property
    def velocity(self):
        return self.data[1]

    @velocity.setter
    def set_velocity(self, val):
        self.data[1] = val


class NoteOnEvent(NoteEvent):
    status = 0x90
    name = 'Note On'


class NoteOffEvent(NoteEvent):
    status = 0x80
    name = 'Note Off'


class AfterTouchEvent(Event):
    status = 0xA0
    length = 2
    name = 'After Touch'

    @property
    def pitch(self):
        return self.data[0]

    @pitch.setter
    def set_pitch(self, val):
        self.data[0] = val

    @property
    def value(self):
        return self.data[1]

    @value.setter
    def set_value(self, val):
        self.data[1] = val


class ControlChangeEvent(Event):
    status = 0xB0
    length = 2
    name = 'Control Change'

    @property
    def control(self):
        return self.data[0]

    @control.setter
    def set_control(self, val):
        self.data[0] = val

    @property
    def value(self):
        return self.data[1]

    @value.setter
    def set_value(self, val):
        self.data[1] = val


class ProgramChangeEvent(Event):
    status = 0xC0
    length = 1
    name = 'Program Change'

    @property
    def value(self):
        return self.data[0]

    @value.setter
    def set_value(self, val):
        self.data[0] = val


class ChannelAfterTouchEvent(Event):
    status = 0xD0
    length = 1
    name = 'Channel After Touch'

    @property
    def value(self):
        return self.data[1]
    
    @value.setter
    def set_value(self, val):
        self.data[1] = val


class PitchWheelEvent(Event):
    status = 0xE0
    length = 2
    name = 'Pitch Wheel'

    @property
    def pitch(self):
        return ((self.data[1] << 7) | self.data[0]) - 0x2000

    @pitch.setter
    def set_pitch(self, pitch):
        value = pitch + 0x2000
        self.data[0] = value & 0x7F
        self.data[1] = (value >> 7) & 0x7F


class SysexEvent(Event):
    status = 0xF0
    name = 'SysEx'
    length = 'varlen'

    @classmethod
    def is_event(cls, status):
        return (cls.status == status)


class SequenceNumberMetaEvent(MetaEvent):
    name = 'Sequence Number'
    metacommand = 0x00
    length = 2


class MetaEventWithText(MetaEvent):
    '''
    Subclass of MetaEvent for events with text
    '''
    def __init__(self, **kw):
        super(MetaEventWithText, self).__init__(**kw)
        if 'text' not in kw:
            self.text = ''.join(chr(datum) for datum in self.data)

    def __repr__(self):
        return self._baserepr(['text'])


class TextMetaEvent(MetaEventWithText):
    name = 'Text'
    metacommand = 0x01
    length = 'varlen'


class CopyrightMetaEvent(MetaEventWithText):
    name = 'Copyright Notice'
    metacommand = 0x02
    length = 'varlen'


class TrackNameEvent(MetaEventWithText):
    name = 'Track Name'
    metacommand = 0x03
    length = 'varlen'


class InstrumentNameEvent(MetaEventWithText):
    name = 'Instrument Name'
    metacommand = 0x04
    length = 'varlen'


class LyricsEvent(MetaEventWithText):
    name = 'Lyrics'
    metacommand = 0x05
    length = 'varlen'


class MarkerEvent(MetaEventWithText):
    name = 'Marker'
    metacommand = 0x06
    length = 'varlen'


class CuePointEvent(MetaEventWithText):
    name = 'Cue Point'
    metacommand = 0x07
    length = 'varlen'


class ProgramNameEvent(MetaEventWithText):
    name = 'Program Name'
    metacommand = 0x08
    length = 'varlen'


class UnknownMetaEvent(MetaEvent):
    name = 'Unknown'
    # This class variable must be overriden by code calling the constructor,
    # which sets a local variable of the same name to shadow the class variable.
    metacommand = None

    def __init__(self, **kw):
        super(MetaEvent, self).__init__(**kw)
        self.metacommand = kw['metacommand']

    def copy(self, **kw):
        kw['metacommand'] = self.metacommand
        return super(UnknownMetaEvent, self).copy(kw)


class ChannelPrefixEvent(MetaEvent):
    name = 'Channel Prefix'
    metacommand = 0x20
    length = 1


class PortEvent(MetaEvent):
    name = 'MIDI Port/Cable'
    metacommand = 0x21


class TrackLoopEvent(MetaEvent):
    name = 'Track Loop'
    metacommand = 0x2E


class EndOfTrackEvent(MetaEvent):
    name = 'End of Track'
    metacommand = 0x2F


class SetTempoEvent(MetaEvent):
    name = 'Set Tempo'
    metacommand = 0x51
    length = 3

    @property
    def bpm(self):
        return float(6e7) / self.mpqn

    @bpm.setter
    def set_bpm(self, bpm):
        self.mpqn = int(float(6e7) / bpm)

    @property
    def mpqn(self):
        assert(len(self.data) == 3)
        vals = [self.data[x] << (16 - (8 * x)) for x in range(3)]
        return sum(vals)

    @mpqn.setter
    def set_mpqn(self, val):
        self.data = [(val >> (16 - (8 * x)) & 0xFF) for x in range(3)]


class SmpteOffsetEvent(MetaEvent):
    name = 'SMPTE Offset'
    metacommand = 0x54


class TimeSignatureEvent(MetaEvent):
    name = 'Time Signature'
    metacommand = 0x58
    length = 4

    @property
    def numerator(self):
        return self.data[0]

    @numerator.setter
    def set_numerator(self, val):
        self.data[0] = val

    @property
    def denominator(self):
        return 2 ** self.data[1]
    @denominator.setter
    def set_denominator(self, val):
        self.data[1] = int(math.log(val, 2))

    @property
    def metronome(self):
        return self.data[2]

    @metronome.setter
    def set_metronome(self, val):
        self.data[2] = val

    @property
    def thirty_seconds(self):
        return self.data[3]
    
    @thirty_seconds.setter
    def set_thirty_seconds(self, val):
        self.data[3] = val


class KeySignatureEvent(MetaEvent):
    name = 'Key Signature'
    metacommand = 0x59
    length = 2

    @property
    def alternatives(self):
        d = self.data[0]
        return d - 256 if d > 127 else d

    @alternatives.setter
    def set_alternatives(self, val):
        self.data[0] = 256 + val if val < 0 else val

    @property
    def minor(self):
        return self.data[1]

    @minor.setter
    def set_minor(self, val):
        self.data[1] = val


class SequencerSpecificEvent(MetaEvent):
    name = 'Sequencer Specific'
    metacommand = 0x7F
