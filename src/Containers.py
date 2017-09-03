'''
Container classes for MIDI Patterns and Tracks

TODO: integer multiplication should extend a track/pattern, as with lists
TODO: respect pattern format, ignore header track when performing vectorized operations
    TODO: see if getitem makes weirdness happen with slicing
TODO: setter for relative ticks
'''
from functools import reduce
from pprint import pformat, pprint
from .Constants import MAX_TICK_RESOLUTION
from .Events import NoteOnEvent, NoteOffEvent, MetaEvent


class Track(list):
    '''
    Track class to hold midi events within a pattern.
    '''

    def __init__(self, events=[], relative=True):
        '''
        Params:
            Optional:
            events: iterable - collection of events to include in the track
            relative: bool - whether or not ticks are relative or absolute
        '''
        self.relative = relative
        super(Track, self).__init__(event.copy() for event in events)

    def make_ticks_abs(self):
        if (self.relative):
            self.relative = False
            running_tick = 0
            for event in self:
                event.tick += running_tick
                running_tick = event.tick

    def make_ticks_rel(self):
        if (not self.relative):
            self.relative = True
            running_tick = 0
            for event in self:
                event.tick -= running_tick
                running_tick += event.tick

    def copy(self):
        return Track((event.copy() for event in self), self.relative)

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return Track((super(Track, self).__getitem__(i).copy() for i in range(*indices)))
        else:
            return super(Track, self).__getitem__(item)

    def __repr__(self):
        return "mydy.Track(\\\n  %s)" % (pformat(list(self)).replace('\n', '\n  '), )

    def __eq__(self, o):
        return (super(Track, self).__eq__(o) and self.relative == o.relative)

    def __add__(self, o):
        if isinstance(o, int):
            return Track(map(lambda x: x + o, self), self.relative)
        elif isinstance(o, Track):
            copy = self.copy()
            copy.extend(o.copy())
            return copy
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __sub__(self, o):
        if isinstance(o, int):
            return self + (-o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __rshift__(self, o):
        if isinstance(o, int):
            return Track(map(lambda x: x >> o, self), self.relative)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __lshift__(self, o):
        if isinstance(o, int):
            return self >> (-o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __mul__(self, o):
        if o <= 0:
            raise TypeError(f"multiplication factor must be greater than zero")
        elif (isinstance(o, int) or isinstance(o, float)) and o > 0:
            return Track(map(lambda x: x * o, self), self.relative)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __truediv__(self, o):
        if o <= 0:
            raise TypeError(f"multiplication factor must be greater than zero")
        elif (isinstance(o, int) or isinstance(o, float)) and o > 0:
            return self * (1 / o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __pow__(self, o):
        if not (isinstance(o, int) or isinstance(o, float)):
            raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")
        # compute the length of the track in ticks
        length = reduce(lambda curr, event: curr + event.tick, self, 0)
        # grab the end-of-track-event
        end_of_track = self[-1]
        # grab everything but the end-of-track-event
        # this is the track we will be adding onto our returned track
        new = self[:-1]
        body = Track(events=filter(lambda x: not MetaEvent.is_event(x.status), new))
        # this will contain our new track
        # add body of event for whole
        for i in range(int(o)):
            new += body
        # decide if we're extending by a float factor and add fractional bit on the end
        cutoff = length * (o % 1)
        if cutoff:
            # keep track of absolute tick position and which notes are on
            pos = 0
            on = set()
            for i, event in enumerate(body):
                pos += event.tick
                if isinstance(event, NoteOnEvent):
                    on.add(event.pitch)
                elif isinstance(event, NoteOffEvent):
                    try:
                        on.remove(event.pitch)
                    except KeyError:
                        pass
                if pos > cutoff:
                    new += body[:i]
                    for note in on:
                        tick = cutoff - (pos - event.tick)
                        new.append(NoteOffEvent(tick=tick, pitch=note, velocity=0))
                    break
        new.append(end_of_track)
        return new


class Pattern(list):
    '''
    Pattern class to hold midi tracks
    '''

    def __init__(self, tracks=[], resolution=220, fmt=1, relative=True):
        self.format = fmt
        self._resolution = resolution
        self.relative = relative
        super(Pattern, self).__init__(track.copy() for track in tracks)
        assert ((fmt == 0 and len(self) <= 1) or (len(self) >= 1))

    @property
    def resolution(self):
        return self._resolution

    @resolution.setter
    def resolution(self, val):
        assert 0 <= val <= MAX_TICK_RESOLUTION, "Invalid 2-byte value"
        coeff = val / self.resolution
        for track in self:
            for event in track:
                event.tick *= coeff
        self._resolution = val

    def copy(self):
        # TODO: add kwarg support?
        return Pattern((track.copy() for track in self), self.resolution, self.format, self.relative)

    def __repr__(self):
        return "mydy.Pattern(format=%r, resolution=%r, tracks=\\\n%s)" % \
            (self.format, self.resolution, pformat(list(self)))

    def __eq__(self, o):
        return (super(Pattern, self).__eq__(o)
                and self.resolution == o.resolution
                and self.format == o.format
                and self.relative == o.relative)

    def __add__(self, o):
        if isinstance(o, int):
            return Pattern(map(lambda x: x + o, self), self.resolution,
                           self.format, self.relative)
        elif isinstance(o, Pattern):
            copy = self.copy()
            copy.extend(o.copy())
            return copy
        elif isinstance(o, Track):
            # TODO: test this
            copy = self.copy()
            copy.append(o.copy())
            return copy
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __sub__(self, o):
        if isinstance(o, int):
            return self + (-o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __rshift__(self, o):
        if isinstance(o, int):
            return Pattern(map(lambda x: x >> o, self), self.resolution,
                           self.format, self.relative)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __lshift__(self, o):
        if isinstance(o, int):
            return self >> (-o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __mul__(self, o):
        if o <= 0:
            raise TypeError(f"multiplication factor must be greater than zero")
        elif (isinstance(o, int) or isinstance(o, float)):
            return Pattern(map(lambda x: x * o, self), self.resolution,
                           self.format, self.relative)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __truediv__(self, o):
        if o <= 0:
            raise TypeError(f"multiplication factor must be greater than zero")
        elif (isinstance(o, int) or isinstance(o, float)):
            return self * (1 / o)
        raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return Pattern((super(Pattern, self).__getitem__(i).copy() for i in range(*indices)))
        else:
            return super(Pattern, self).__getitem__(item)
