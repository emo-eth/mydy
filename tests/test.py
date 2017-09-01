import unittest
import numpy as np
import sys
import random
sys.path.append('../src')
import util
import FileIO
random.randint(1, 128)

class TestUtil(unittest.TestCase):
    def test_symmetry(self):
        for _ in range(1000):
            test = random.randint(0, 2 ** (7 * 4)-1)
            self.assertEqual(test, util.read_varlen(iter(util.write_varlen(test))))

class TestFileIO(unittest.TestCase):
    def test_splode(self):
        with open('mary.mid', 'rb') as f:
            io = FileIO.FileReader()
            io.read(f)
    
    def test_write_read(self):
        read = FileIO.read_midifile('mary.mid')
        self.assertTrue(len(read[0]) > 0)
        FileIO.write_midifile('test.mid', read)
        self.assertEqual(read, FileIO.read_midifile('test.mid'))