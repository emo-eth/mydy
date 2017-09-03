'''
A collection of MIDI events

'''
import math


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

    name = "Generic MIDI Event"
    length = 0
    status = 0x0

    def __init__(self, tick=0, data=[]):
        if not data and isinstance(self.length, int):
            data = [0] * self.length
        self.tick = tick
        self.data = data

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
        return "mydy.%s(%s)" % (self.__class__.__name__, body)

    def __repr__(self):
        return self._baserepr()

    def copy(self):
        return self.__class__(tick=self.tick, data=self.data.copy())

    def __add__(self, o):
        if isinstance(o, int):
            if hasattr(self, 'pitch'):
                new = self.copy()
                new.pitch += o
                return new
            else:
                return self.copy()
        raise TypeError(
            f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __radd__(self, o):
        return self.__add__(o)

    def __sub__(self, o):
        if isinstance(o, int):
            return self + (-o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __rsub__(self, o):
        return self.__sub__(o)

    def __rshift__(self, o):
        # TODO: remove final else
        if isinstance(o, int):
            if hasattr(self, 'velocity'):
                new = self.copy()
                new.velocity += o
                return new
            else:
                return self.copy()
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __lshift__(self, o):
        if isinstance(o, int):
            return self >> (-o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __mul__(self, o):
        # TODO: handle resolution changes as necessary
        if o <= 0:
            raise TypeError(f"multiplication factor must be greater than zero")
        elif (isinstance(o, int) or isinstance(o, float)) and o > 0:
            new = self.copy()
            new.tick *= o
            return new
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __truediv__(self, o):
        if o <= 0:
            raise TypeError(f"multiplication factor must be greater than zero")
        elif (isinstance(o, int) or isinstance(o, float)) and o > 0:
            return self * (1 / o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")


class Event(AbstractEvent):
    name = 'Event'

    def __init__(self, channel=0, tick=0, data=[], **kw):
        super(Event, self).__init__(tick, data)
        self.channel = channel

    def _truncate(self):
        '''Quantize data bytes to 7-bit values'''
        def quantize(x):
            if 0 <= x <= 127:
                return x
            elif 0 > x:
                return 0
            else:
                return 127
        new = self.copy()
        new.data = list(map(quantize, self.data))
        return new

    def copy(self):
        return self.__class__(channel=self.channel, tick=self.tick, data=self.data.copy())

    def __lt__(self, other):
        return (super(Event, self).__lt__(other) or
                (super(Event, self).__eq__(other) and
                 self.channel < other.channel))

    def __eq__(self, other):
        return (super(Event, self).__eq__(other) and
                self.channel == other.channel)

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

    def __init__(self, tick=0, data=[], metacommand=None):
        super(MetaEvent, self).__init__(tick, data)
        if metacommand:
            self.metacommand = metacommand

    @classmethod
    def is_event(cls, status):
        return (status == cls.status)

    def copy(self):
        return self.__class__(metacommand=self.metacommand, tick=self.tick,
                              data=self.data.copy())


class NoteEvent(Event):
    '''
    NoteEvent is a special subclass of Event that is not meant to
    be used as a concrete class.  It defines the generalities of NoteOn
    and NoteOff events.
    '''
    length = 2

    def __init__(self, pitch=None, velocity=None, channel=0, tick=0, data=[], **kw):
        super(NoteEvent, self).__init__(channel, tick, data)
        if pitch is not None:
            self.pitch = pitch
        if velocity is not None:
            self.velocity = velocity

    @property
    def pitch(self):
        return self.data[0]

    @pitch.setter
    def pitch(self, val):
        self.data[0] = val

    @property
    def velocity(self):
        return self.data[1]

    @velocity.setter
    def velocity(self, val):
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

    def __init__(self, pitch=None, value=None, channel=0, tick=0, data=[], **kw):
        super(AfterTouchEvent, self).__init__(channel, tick, data)
        if pitch is not None:
            self.pitch = pitch
        if value is not None:
            self.value = value

    @property
    def pitch(self):
        return self.data[0]

    @pitch.setter
    def pitch(self, val):
        self.data[0] = val

    @property
    def value(self):
        return self.data[1]

    @value.setter
    def value(self, val):
        self.data[1] = val


class ControlChangeEvent(Event):
    status = 0xB0
    length = 2
    name = 'Control Change'

    def __init__(self, control=None, value=None, channel=0, tick=0, data=[], **kw):
        super(ControlChangeEvent, self).__init__(channel, tick, data)
        if control is not None:
            self.control = control
        if value is not None:
            self.value = value

    @property
    def control(self):
        return self.data[0]

    @control.setter
    def control(self, val):
        self.data[0] = val

    @property
    def value(self):
        return self.data[1]

    @value.setter
    def value(self, val):
        self.data[1] = val


class ProgramChangeEvent(Event):
    status = 0xC0
    length = 1
    name = 'Program Change'

    def __init__(self, value=None, channel=0, tick=0, data=[], **kw):
        super(ProgramChangeEvent, self).__init__(channel, tick, data)
        if value is not None:
            self.value = value

    @property
    def value(self):
        return self.data[0]

    @value.setter
    def value(self, val):
        self.data[0] = val


class ChannelAfterTouchEvent(Event):
    status = 0xD0
    length = 1
    name = 'Channel After Touch'

    def __init__(self, value=None, channel=0, tick=0, data=[], **kw):
        super(ChannelAfterTouchEvent, self).__init__(channel, tick, data)
        if value is not None:
            self.value = value

    @property
    def value(self):
        return self.data[1]

    @value.setter
    def value(self, val):
        self.data[1] = val


class PitchWheelEvent(Event):
    status = 0xE0
    length = 2
    name = 'Pitch Wheel'

    def __init__(self, pitch=None, channel=0, tick=0, data=[], **kw):
        super(PitchWheelEvent, self).__init__(channel, tick, data)
        if pitch is not None:
            self.pitch = pitch

    @property
    def pitch(self):
        return ((self.data[1] << 7) | self.data[0]) - 0x2000

    @pitch.setter
    def pitch(self, pitch):
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

    def __init__(self, text=None, tick=0, data=[], **kw):
        super(MetaEventWithText, self).__init__(**kw)
        if text is not None:
            self.text = text
        self._text = None

    @property
    def text(self):
        if self._text is None:
            self._text = ''.join(chr(datum) for datum in self.data)
        return self._text

    @text.setter
    def text(self, text):
        # TODO: how will actual bytes affect the output?
        self.data = bytearray(ord(c) for c in text)
        self._text = None

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

    def __init__(self, metacommand=None, tick=0, data=[]):
        super(UnknownMetaEvent, self).__init__(tick, data)
        self.metacommand = metacommand


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
    # TODO: look into how bpm and mpqn interact
    name = 'Set Tempo'
    metacommand = 0x51
    length = 3

    def __init__(self, bpm=None, mpqn=None, tick=0, data=[], **kw):
        super(SetTempoEvent, self).__init__(tick, data)
        if bpm is not None:
            self.bpm = bpm
        if mpqn is not None:
            self.mpqn = mpqn

    @property
    def bpm(self):
        return float(6e7) / self.mpqn

    @bpm.setter
    def bpm(self, bpm):
        self.mpqn = int(float(6e7) / bpm)

    @property
    def mpqn(self):
        assert(len(self.data) == 3)
        vals = [self.data[x] << (16 - (8 * x)) for x in range(3)]
        return sum(vals)

    @mpqn.setter
    def mpqn(self, val):
        self.data = [(val >> (16 - (8 * x)) & 0xFF) for x in range(3)]


class SmpteOffsetEvent(MetaEvent):
    name = 'SMPTE Offset'
    metacommand = 0x54


class TimeSignatureEvent(MetaEvent):
    name = 'Time Signature'
    metacommand = 0x58
    length = 4

    def __init__(self, numerator=None, denominator=None, metronome=None, thirty_seconds=None,
                 tick=0, data=[], **kw):
        super(TimeSignatureEvent, self).__init__(tick, data)
        if numerator is not None:
            self.numerator = numerator
        if denominator is not None:
            self.denominator = denominator
        if metronome is not None:
            self.metronome = metronome
        if thirty_seconds is not None:
            self.thirty_seconds = thirty_seconds

    @property
    def numerator(self):
        return self.data[0]

    @numerator.setter
    def numerator(self, val):
        self.data[0] = val

    @property
    def denominator(self):
        return 2 ** self.data[1]

    @denominator.setter
    def denominator(self, val):
        self.data[1] = int(math.log(val, 2))

    @property
    def metronome(self):
        return self.data[2]

    @metronome.setter
    def metronome(self, val):
        self.data[2] = val

    @property
    def thirty_seconds(self):
        return self.data[3]

    @thirty_seconds.setter
    def thirty_seconds(self, val):
        self.data[3] = val


class KeySignatureEvent(MetaEvent):
    name = 'Key Signature'
    metacommand = 0x59
    length = 2

    def __init__(self, alternatives=None, minor=None, channel=0, tick=0, data=[],
                 **kw):
        super(KeySignatureEvent, self).__init__(tick, data)
        if alternatives is not None:
            self.alternatives = alternatives
        if minor is not None:
            self.minor = minor

    @property
    def alternatives(self):
        d = self.data[0]
        return d - 256 if d > 127 else d

    @alternatives.setter
    def alternatives(self, val):
        self.data[0] = 256 + val if val < 0 else val

    @property
    def minor(self):
        return self.data[1]

    @minor.setter
    def minor(self, val):
        self.data[1] = val


class SequencerSpecificEvent(MetaEvent):
    name = 'Sequencer Specific'
    metacommand = 0x7F
