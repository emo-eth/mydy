import unittest
import random
import util
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
    
    def test_construction(self):
        for _, cls in chain(Events.EventRegistry.Events.items(),
                            Events.EventRegistry.MetaEvents.items()):
            cls(metacommand=1, tick=1, data=[1])
    
    def test_add(self):
        pattern = FileIO.read_midifile('mary.mid')
        val = pattern[1][5].pitch
        pattern[1] = pattern[1] + 1
        self.assertEqual(val + 1, pattern[1][5].pitch)

