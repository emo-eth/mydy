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


class AbstractEvent(object):

    def __init__(self, time_delta, status, *data):
        self.time_delta = time_delta
        self.status = status
        self.data = data or tuple()
    
    @property
    @abstractmethod
    def is_transposable(self):
        return
    
    @property
    @abstractmethod
    def has_velocity(self):
        return

    def _body_repr(self):
        data_repr = ' '.join(f'{x:08b}' for x in self.data)
        head = f'td: {self.time_delta:08b} id: {self.status:08b}'
        if data_repr:
            return head + ' data: ' + data_repr
        return head


class MidiEvent(AbstractEvent):
    def __repr__(self):
        return f'<MidiEvent: {self._body_repr()}>'

class SysexEvent(AbstractEvent):
    def __repr__(self):
        return f'<SysexEvent: {self._body_repr()}>'
    pass

class MetaEvent(AbstractEvent):
    def __repr__(self):
        return f'<MetaEvent: {self._body_repr()}>'

