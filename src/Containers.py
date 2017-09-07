'''
Container classes for MIDI Patterns and Tracks

TODO: integer multiplication should extend a track/pattern, as with lists
TODO: respect pattern format, ignore header track when performing vectorized
    operations
    TODO: see if getitem makes weirdness happen with slicing
TODO: should tracks care if they have relative ticks or not?
TODO: implement pow and map methods for pattern
'''
from functools import reduce
from pprint import pformat, pprint
from .Constants import MAX_TICK_RESOLUTION
from .Events import NoteOnEvent, NoteOffEvent, MetaEvent, AbstractEvent, EndOfTrackEvent

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
        self._relative = relative
        self._length = None
        super(Track, self).__init__(self.__assert_event(event.copy())
                                    for event in events)
    
    def __assert_event(self, event):
        assert isinstance(event, AbstractEvent), "Non-event passed to Track constructor"
        return event

    @property
    def length(self):
        '''Compute the length of a track in ticks'''
        if self._length is None:
            if self.relative:
                self._length = reduce(lambda curr, event: curr + event.tick, self, 0)
            else:
                self._length = 0 if not len(self) else self[-1].tick
        return self._length

    @property
    def relative(self):
        return self._relative

    @relative.setter
    def relative(self, val):
        '''Set the relative flag and mutate events to have relative ticks'''
        if val != self._relative:
            self._relative = val
            running_tick = 0
            if self._relative:
                for event in self:
                    event.tick -= running_tick
                    running_tick += event.tick
            else:
                for event in self:
                    event.tick += running_tick
                    running_tick = event.tick

    def make_ticks_abs(self):
        '''Return a copy of the track with absolute ticks'''
        copy = self.copy()
        copy.relative = False
        return copy

    def make_ticks_rel(self):
        '''Returns a copy of the track with relative ticks'''
        copy = self.copy()
        copy.relative = True
        return copy
    
    def truncate_ticks(self):
        '''
        Returns a copy of the track whose events have whole-number ticks.
        Note that ticks are automatically truncated with the max resolution
        when written to disk
        '''
        copy = self.copy()
        for event in copy:
            event.tick = int(event.tick + .5)
        return copy

    def merge(self, o):
        '''Merge two MIDI tracks, interleaving their events.'''
        assert isinstance(o, Track), "Can only merge with other tracks"
        abself = self.make_ticks_abs()
        abso = o.make_ticks_abs()
        combined = abself + abso
        combined = Track(events=sorted(combined, key=lambda x: x.tick),
                         relative=False)
        combined.relative = self.relative
        return combined
    
    def map(self, f, attr=None, event_type=None):
        '''
        Map a function that operates on events over the track, optionally apply
        to event attributes
        If attr is not passed, f must return an Event. Otherwise, it is assumed
        f returns a value to assign to the specified attribute
        Params:
            f: function(x: event) - function that takes a single event as its
                    only argument, and either returns an Event or a value to
                    assign to the specified attr
            Optional:
            attr: string - attribute/property of an Event that f assigns to. If
                not supplied, f is assumed to return an Event object
            
        Returns:
            A new Track object with f applied to all Events
        '''
        if attr is not None:
            copy = self.copy()
            for event in copy:
                if ((event_type is None or isinstance(event, event_type))
                     and hasattr(event, attr)):
                    setattr(event, attr, f(event))
            return copy
        return Track(events=(f(event.copy())
                             if (event_type is None
                                 or isinstance(event, event_type))
                             else event.copy() for event in self),
                     relative=self.relative)
    
    def filter(self, test):
        '''Filter events from a track according to a test predicate.
        Returns a new Track with only events that satisfy the test.'''
        return Track((event for event in self if test(event)),
                     relative=self.relative)

    def copy(self):
        return Track((event.copy() for event in self), self.relative)

    def __getitem__(self, item):
        # TODO: test and fix this.
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return Track((super(Track, self).__getitem__(i).copy() for i in range(*indices)))
        else:
            return super(Track, self).__getitem__(item)

    def __repr__(self):
        return "mydy.Track(relative: %s\\\n  %s)" % (self.relative, pformat(list(self)).replace('\n', '\n  '), )

    def __eq__(self, o):
        return (super(Track, self).__eq__(o) and self.relative == o.relative)

    def __add__(self, o):
        # TODO: figure out trackend events
        if isinstance(o, int):
            return Track(map(lambda x: x + o, self), self.relative)
        elif isinstance(o, Track):
            # if self has an EndOfTrackEvent, grab it, and slice it out
            eot = None
            if len(self) and isinstance(self[-1], EndOfTrackEvent):
                eot = self[-1]
            if eot is None:
                copy = self.copy()
            else:
                copy = self[:-1]
            ocopy = o.copy()
            ocopy.relative = self.relative
            # nudge ocopy by the tick value of the EOTEvent
            if eot is not None and len(ocopy):
                ocopy[0].tick += eot.tick
            elif eot is not None and not len(ocopy):  # otherwise just append it
                ocopy.append(eot)
            copy.extend(ocopy)
            return copy
        raise TypeError(
            f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __sub__(self, o):
        if isinstance(o, int):
            return self + (-o)
        raise TypeError(
            f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")

    def __rshift__(self, o):
        # TODO: allow function mapping?
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
        assert 0 < o, "Extension power must be greater than zero"
        if not (isinstance(o, int) or isinstance(o, float)):
            raise TypeError(
                f"unsupported operand type(s) for +: '{self.__class__}' and '{type(o)}'")
        # compute the length of the track in ticks
        length = self.length 
        copy = self.make_ticks_rel()
        # grab the end-of-track-event
        if isinstance(copy[-1], EndOfTrackEvent):
            end_of_track = copy[-1]
            # grab everything but the end-of-track-event
            new = copy[:-1]
        else:
            end_of_track = None
            new = copy
        # this is the track we will be adding onto our returned track
        body = new.filter(lambda x: not MetaEvent.is_event(x.status))
        # create whole copies of the body
        for _ in range(1, int(o)):
            new += body
        # decide if we're extending by a partial factor, add fraction to the end
        cutoff = length * (o % 1)
        if cutoff:
            # keep track of absolute tick position and which notes are on
            pos = 0
            on = set()
            for i, event in enumerate(body):
                pos += event.tick
                if pos > cutoff:
                    tick = cutoff - (pos - event.tick)
                    new += body[:i]
                    for note in on:
                        new.append(NoteOffEvent(
                            tick=tick, pitch=note, velocity=0))
                        # since these are relative ticks, set to 0
                        tick = 0
                    break
                if isinstance(event, NoteOnEvent):
                    on.add(event.pitch)
                elif isinstance(event, NoteOffEvent):
                    try:
                        on.remove(event.pitch)
                    except KeyError:
                        pass
        if end_of_track is not None:
            new.append(end_of_track)
        new.relative = self.relative
        return new


class Pattern(list):
    '''
    Pattern class to hold midi tracks
    '''

    def __init__(self, tracks=[], resolution=220, fmt=1, relative=True):
        self.format = fmt
        self._resolution = resolution
        self._relative = relative
        super(Pattern, self).__init__(self.__assert_track(track.copy())
                                      for track in tracks)
        assert ((fmt == 0 and len(self) <= 1) or (len(self) >= 1))
    
    def __assert_track(self, track):
        assert isinstance(track, Track), ("Non-Track passed to Pattern " +
                                          "constructor")
        return track

    @property
    def relative(self):
        return self._relative

    @relative.setter
    def relative(self, val):
        # TODO: tests
        if (val != self.relative):
            self._relative = val
            for track in self:
                track.relative = val

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
        # TODO: consider formats when adding tracks
        if isinstance(o, int):
            return Pattern(map(lambda x: x + o, self), self.resolution,
                           self.format, self.relative)
        elif isinstance(o, Pattern):
            copy = self.copy()
            copy.extend(o.copy())
            return copy

            # # TODO: more tests
            # if self.format == 0:
            #     '''TODO: The first track of a Format 1 file is special, and is also known as the 'Tempo Map'. It should contain all meta-events of the types Time Signature, and Set Tempo. The meta-events Sequence/Track Name, Sequence Number, Marker, and SMTPE Offset. should also be on the first track of a Format 1 file.'''
            #     copy = self.copy()
            #     if o.format == 0:
            #         copy.extend(o.copy())
            #         # default to format 1
            #         copy.format = 1
            #         return copy
            #     elif o.format == 1 or o.format == 2:
            #         copy.format = o.format
            #         ocopy = o.copy()
            #         ocopy.extend(copy)
            #         return ocopy
            # if self.format == 0 and o.format == 1:
            #     copy = self.copy()
            #     copy.format = 1
            #     return o.copy().extend(copy)
        elif isinstance(o, Track):
            copy = self.copy()
            ocopy = o.copy()
            ocopy.relative = self.relative
            copy.append(ocopy)
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
