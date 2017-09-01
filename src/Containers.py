'''
Container classes for MIDI Patterns and Tracks
'''
from pprint import pformat, pprint


class Track(list):
    def __init__(self, events=[], relative=True):
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

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = item.indices(len(self))
            return Track((super(Track, self).__getitem__(i) for i in range(*indices)))
        else:
            return super(Track, self).__getitem__(item)

    def __getslice__(self, i, j):
        # The deprecated __getslice__ is still called when subclassing built-in types
        # for calls of the form List[i:j]
        return self.__getitem__(slice(i,j))

    def __repr__(self):
        return "midi.Track(\\\n  %s)" % (pformat(list(self)).replace('\n', '\n  '), )



class Pattern(list):
    def __init__(self, tracks=[], resolution=220, fmt=1, relative=True):
        assert ((fmt == 0 and len(tracks) <= 1) or (len(tracks) >= 1))
        self.format = fmt
        self.resolution = resolution
        self.relative_tick = relative
        super(Pattern, self).__init__(tracks)

    # @property
    # def tracks(self):
    #     return self._tracks

    # @tracks.setter
    # def tracks(self, tracks):
    #     return Pattern(self.format, self.num_tracks, self.resolution, tracks=[t.copy() for t in tracks])

    # def add_track(self, track, fmt=1):
    #     if self.format != 0:
    #         fmt = self.format
    #     return Pattern(fmt, self.num_tracks + 1, self.resolution, tracks=[t.copy() for t in self.tracks] + [track.copy()])

    # @property
    # def format(self):
    #     return self.format

    # @format.setter
    # def format(self, fmt):
    #     assert 0 <= fmt <= 2, "Format must be between 0 and 2, inclusive"
    #     return Pattern(fmt, self.num_tracks, self.resolution, tracks=[t.copy() for t in self.tracks])
