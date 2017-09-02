import unittest
import random
import util
import math
import FileIO
import Events
from itertools import chain

class TestUtil(unittest.TestCase):
    def test_symmetry(self):
        for _ in range(1000):
            test = random.randint(0, 2 ** (7 * 4)-1)
            self.assertEqual(test, util.read_varlen(iter(util.write_varlen(test))))

class TestFileIO(unittest.TestCase):

    def test_write_read(self):
        read = FileIO.read_midifile('mary.mid')
        self.assertTrue(len(read[0]) > 0)
        FileIO.write_midifile('test.mid', read)
        self.assertEqual(read, FileIO.read_midifile('test.mid'))

class TestEvents(unittest.TestCase):
    
    def test_construction(self):
        for _, cls in chain(Events.EventRegistry.Events.items(),
                            Events.EventRegistry.MetaEvents.items()):
            cls(metacommand=1, tick=1, data=[1])
    
    def test_add_event(self):
        pattern = FileIO.read_midifile('mary.mid')
        event = pattern[1][5]
        event2 = event + 1
        self.assertNotEqual(event, event2)
        self.assertEqual(event.pitch + 1, event2.pitch)
        event3 = event2 - 1
        self.assertEqual(event, event3)

    def test_shift_event(self):
        pattern = FileIO.read_midifile('mary.mid')
        event = pattern[1][5]
        event2 = event >> 1
        self.assertNotEqual(event, event2)
        self.assertEqual(event.velocity + 1, event2.velocity)
        event3 = event2 << 1
        self.assertEqual(event, event3)

    def test_mul_event(self):
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
        pattern = FileIO.read_midifile('mary.mid')
        track1 = pattern[1]
        track2 = track1 + 1
        self.assertNotEqual(track1, track2)
        track3 = track2 - 1
        self.assertEqual(track1, track3)

    def test_shift_track(self):
        pattern = FileIO.read_midifile('mary.mid')
        track1 = pattern[1]
        track2 = track1 >> 1
        self.assertNotEqual(track1, track2)
        track3 = track2 << 1
        self.assertEqual(track1, track3)
    
    def test_mul_track(self):
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

class TestPattern(unittest.TestCase):

    def test_deep_eq(self):
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

