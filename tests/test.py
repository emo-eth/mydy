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
    
    def test_add_tracks(self):
        pattern = FileIO.read_midifile('mary.mid')
        track1 = pattern[1]
        copy = track1.copy()
        self.assertTrue(len(track1) * 2 - 1 == len(track1 + track1[:-1]))
        self.assertNotEqual(track1, track1 + copy)


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
