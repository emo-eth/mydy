'''
Container classes for MIDI Patterns and Tracks
'''
from abc import ABC, abstractmethod
import numpy as np


class Track(object):
    pass


class Pattern(object):
    def __init__(self, fmt, num_tracks, division, tracks=None):
        assert (tracks is None or len(tracks) == num_tracks,
                "num_tracks and tracks do not match")
        assert ((fmt == 0 and num_tracks <= 1) or (num_tracks >= 1))
        self.division = division
        self._format = fmt
        self.num_tracks = num_tracks
        if not tracks and num_tracks:
            self._tracks = np.array([np.array([]) for _ in range(num_tracks)])
        else:
            self._tracks = np.array([t.copy() for t in tracks])

    @property
    def tracks(self):
        return self._tracks

    @tracks.setter
    def tracks(self, tracks):
        return Pattern(self.format, self.num_tracks, self.division, tracks=[t.copy() for t in tracks])

    def add_track(self, track, fmt=1):
        if self.format != 0:
            fmt = self.format
        return Pattern(fmt, self.num_tracks + 1, self.division, tracks=[t.copy() for t in self.tracks] + [track.copy()])

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, fmt):
        assert 0 <= fmt <= 2, "Format must be between 0 and 2, inclusive"
        return Pattern(fmt, self.num_tracks, self.division, tracks=[t.copy() for t in self.tracks])
