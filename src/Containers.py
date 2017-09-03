'''
Container classes for MIDI Patterns and Tracks

TODO: integer multiplication should extend a track/pattern, as with lists
TODO: respect pattern format, ignore header track when performing vectorized operations
    TODO: see if getitem makes weirdness happen with slicing
TODO: setter for relative ticks
TODO: pow operator
'''
from pprint import pformat, pprint
from .Constants import MAX_TICK_RESOLUTION


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
        super(Track, self).__init__(events)

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
        return "midi.Track(\\\n  %s)" % (pformat(list(self)).replace('\n', '\n  '), )

    def __eq__(self, o):
        return (super(Track, self).__eq__(o) and self.relative == o.relative)

    def __add__(self, o):
        if isinstance(o, int):
            return Track(map(lambda x: x + o, self), self.relative)
        elif isinstance(o, Track):
            return self.copy() + o.copy()
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


class Pattern(list):
    '''
    Pattern class to hold midi tracks
    '''

    def __init__(self, tracks=[], resolution=220, fmt=1, relative=True):
        self.format = fmt
        self._resolution = resolution
        self.relative = relative
        super(Pattern, self).__init__(tracks)
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
        return "midi.Pattern(format=%r, resolution=%r, tracks=\\\n%s)" % \
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
            return self.copy() + o.copy()
        elif isinstance(o, Track):
            # TODO: test this
            return self.copy().append(o.copy())
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
