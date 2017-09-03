'''
Tests for MIDI modules
'''
import unittest
import random
import math
from itertools import chain
# in the dev environment, mydy is known as src
import src as mydy
from mydy import Util, FileIO, Events
from mydy.Constants import MAX_TICK_RESOLUTION


class TestUtil(unittest.TestCase):
    def test_symmetry(self):
        for _ in range(1000):
            test = random.randint(2 ** 16, 2 ** (64) - 1)
            self.assertEqual(test, Util.read_varlen(
                iter(Util.write_varlen(test))))


class TestFileIO(unittest.TestCase):

    def test_write_read(self):
        '''Test that write and read are inverses of each other'''
        read = FileIO.read_midifile('mary.mid')
        self.assertTrue(len(read[0]) > 0)
        FileIO.write_midifile('test.mid', read)
        self.assertEqual(read, FileIO.read_midifile('test.mid'))
        read2 = read * (2 / 3)
        FileIO.write_midifile('test.mid', read2)


class TestEvents(unittest.TestCase):

    def test_constructors(self):
        '''Test all constructors behave as expected'''
        for _, cls in chain(Events.EventRegistry.Events.items(),
                            Events.EventRegistry.MetaEvents.items()):
            cls(metacommand=1, tick=1, data=[1])

    def test_add_event(self):
        '''Test that events support integer addition'''
        pattern = FileIO.read_midifile('mary.mid')
        event = pattern[1][5]
        event2 = event + 1
        self.assertNotEqual(event, event2)
        self.assertEqual(event.pitch + 1, event2.pitch)
        event3 = event2 - 1
        self.assertEqual(event, event3)

    def test_shift_event(self):
        '''Test that events support integer shift operations'''
        pattern = FileIO.read_midifile('mary.mid')
        event = pattern[1][5]
        event2 = event >> 1
        self.assertNotEqual(event, event2)
        self.assertEqual(event.velocity + 1, event2.velocity)
        event3 = event2 << 1
        self.assertEqual(event, event3)

    def test_mul_event(self):
        '''Test that events support integer and float multiplication'''
        pattern = FileIO.read_midifile('mary.mid')
        event = pattern[1][20]
        event * 1  # test ints are valid too
        event2 = event * 2.2
        self.assertNotEqual(event, event2)
        self.assertEqual(event.tick * 2.2, event2.tick)
        event3 = event2 / 2.2
        self.assertAlmostEqual(event.tick, event3.tick)


class TestTracks(unittest.TestCase):

    def test_add_track(self):
        '''Test that tracks support integer addition'''
        pattern = FileIO.read_midifile('mary.mid')
        track1 = pattern[1]
        track2 = track1 + 1
        self.assertNotEqual(track1, track2)
        track3 = track2 - 1
        self.assertEqual(track1, track3)

    def test_shift_track(self):
        '''Test that tracks support integer shift operations'''
        pattern = FileIO.read_midifile('mary.mid')
        track1 = pattern[1]
        track2 = track1 >> 1
        self.assertNotEqual(track1, track2)
        track3 = track2 << 1
        self.assertEqual(track1, track3)

    def test_mul_track(self):
        '''Test that tracks support integer and float multiplication'''
        pattern = FileIO.read_midifile('mary.mid')
        track1 = pattern[1]
        track1 * 1  # test ints are valid too
        track2 = track1 * 2.2
        self.assertNotEqual(track1, track2)
        track3 = track2 / 2.2
        # avoid failures due to float imprecision
        for event in track3:
            event.tick = int(event.tick)
        self.assertAlmostEqual(track1, track3)
    
    def test_pow_tracks(self):
        '''Tracks support integer and float power operations'''
        pattern = FileIO.read_midifile('sotw.mid')
        track = pattern[0]
        self.assertTrue(track.length * 2 == (track ** 2).length)
        track42 = track ** 4.2
        self.assertTrue(track.length * 4.2 == (track ** 4.2).length)
        self.assertTrue(int(track.length * 4.2) == int((track ** 4.2).length))
    
    def test_add_tracks(self):
        '''Tracks can be added together to create a new object'''
        pattern = FileIO.read_midifile('mary.mid')
        track1 = pattern[1]
        copy = track1.copy()
        self.assertTrue(len(track1) * 2 - 1 == len(track1 + track1[:-1]))
        combined = track1 + copy
        self.assertTrue(track1[1] == combined[1] and track1[1] is not combined[1])
    
    def test_length_and_relative(self):
        '''Length property works with both relative and absolute ticks.'''
        pattern = FileIO.read_midifile('mary.mid')
        self.assertEqual(pattern[0].length, 1)
        running_tick = 0
        for event in pattern[1]:
            running_tick += event.tick
        self.assertEqual(running_tick, pattern[1].length)
        abscopy = pattern[1].copy()
        abscopy.relative = False
        # print(abscopy)
        self.assertEqual(running_tick, abscopy.length)

    def test_relative(self):
        '''Test that relative setter and make_ticks_xxx methods work as expected,
        ie methods return copies and setter modifies in place '''
        pattern = FileIO.read_midifile('mary.mid')
        track = pattern[1]
        abscopy = track.copy()
        abscopy2 = abscopy.make_ticks_abs()
        self.assertTrue(abscopy is not abscopy2)
        self.assertNotEqual(abscopy, abscopy2)
        abscopy.relative = False
        self.assertEqual(abscopy, abscopy2)
        relcopy = abscopy.make_ticks_rel()
        self.assertEqual(track, relcopy)


class TestPattern(unittest.TestCase):

    def test_deep_eq(self):
        '''Test that two pattern objects equal each other'''
        read1 = FileIO.read_midifile('mary.mid')
        read2 = FileIO.read_midifile('mary.mid')
        self.assertEqual(read1, read2)

    def test_add_pattern(self):
        pattern1 = FileIO.read_midifile('mary.mid')
        pattern2 = pattern1 + 1
        self.assertNotEqual(pattern1, pattern2)
        pattern3 = pattern2 - 1
        self.assertEqual(pattern1, pattern3)

    def test_shift_pattern(self):
        pattern1 = FileIO.read_midifile('mary.mid')
        pattern2 = pattern1 >> 1
        self.assertNotEqual(pattern1, pattern2)
        pattern3 = pattern2 << 1
        self.assertEqual(pattern1, pattern3)
        pattern1 >> 200
        math.ceil

    def test_mul_pattern(self):
        pattern1 = FileIO.read_midifile('mary.mid')
        pattern1 * 1  # test ints are valid too
        pattern2 = pattern1 * 2.2
        self.assertNotEqual(pattern1, pattern2)
        pattern3 = pattern2 / 2.2
        # avoid failures due to float imprecision
        for track in pattern3:
            for event in track:
                event.tick = int(event.tick)
        self.assertEqual(pattern1, pattern3)

    def test_mul_symmetry(self):
        orig = FileIO.read_midifile('mary.mid')
        orig *= 1.1
        FileIO.write_midifile('test.mid', orig)
        orig.resolution = MAX_TICK_RESOLUTION
        for track in orig:
            for event in track:
                event.tick = int(event.tick + .5)
        read = FileIO.read_midifile('test.mid')
        self.assertEqual(orig, read)
    
    def test_add_patterns(self):
        pattern = FileIO.read_midifile('mary.mid')
        copy = pattern.copy()
        self.assertTrue(len(pattern) * 2 == len(pattern + copy))
        self.assertTrue(pattern == copy and pattern is not copy)
        for track, trackcopy in zip(pattern, copy):
            self.assertEqual(track, trackcopy)
            self.assertFalse(track is trackcopy)
            for event, eventcopy in zip(track, trackcopy):
                self.assertEqual(event, eventcopy)
                self.assertFalse(event is eventcopy)
