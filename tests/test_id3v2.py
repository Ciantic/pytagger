import unittest
import types

"""
TODO:
- tests for exact extraction for a known mp3
- tests for writing
"""

from tagger.id3v2frame import *
from tagger.id3v2 import *
from tagger.exceptions import *
from tagger.constants import *

class ID3v2LoadTest(unittest.TestCase):

	def testLoadReadOnly(self):
		id3 = ID3v2(self.filename, ID3_FILE_READ)
		self.assert_(id3)

	def testLoadModify(self):
		id3 = ID3v2(self.filename, ID3_FILE_MODIFY)
		self.assert_(id3)

	def _testLoadNew(self):
		id3 = ID3v2(self.filename, ID3_FILE_NEW)
		self.assert_(id3)
	
	def testLoadInvalidModify(self):
		self.assertRaises(ID3HeaderInvalidException, ID3v2, "data/empty_file.mp3", ID3_FILE_MODIFY)

	def testLoadNotFound(self):
		self.assertRaises(ID3ParameterException, ID3v2, "data/missing.mp3", ID3_FILE_MODIFY)

class ID3v2_2_FrameTest(unittest.TestCase):

	tag_tt2 = 'TT2\x00\x00\x13\x01\xfe\xffN\x00_\x00Y\xcb\\1l\xa1\x90\x00\x8d\xef\x00\x00'
	tag_tp1 = 'TP1\x00\x00\x0b\x01\xfe\xff_ \x97\x07\\\xb3\x00\x00'
	tag_tal = 'TAL\x00\x00\x0b\x01\xfe\xffg\t\x95\xee\x98\x98\x00\x00'
	tag_tye = 'TYE\x00\x00\x06\x002000\x00'
	tag_tco = 'TCO\x00\x00\n\x00Pop (TW)\x00'
	tag_tt3 = 'TT2\x00\x00\x12\x00Give Me A Reason\x00'

	tags = {'TT2':tag_tt2, 'TP1':tag_tp1, 'TAL':tag_tal, 'TYE':tag_tye, 'TCO':tag_tco, 'TT3':tag_tt3}

	def testParseValidTags(self):
		for data in self.tags.values():
			f = ID3v2_2_Frame(frame=data)
			self.assert_(f)

	def testCreateNewTags(self):
		for tag in ID3v2_2_Frame.supported.keys():
			f = ID3v2_2_Frame(fid=tag)
			self.assert_(f)

	def testWriteTags(self):
		for data in self.tags.values():
			f = ID3v2_2_Frame(frame=data)
			self.assert_(f.output() == data)

class ID3v2_2Crash(unittest.TestCase):
    filename = "data/pytagger-crash.mp3"

class ID3v2_2File1(unittest.TestCase):
	filename = "data/chinese_id3v2.2_only.mp3"
	
class ID3v2_2File2(unittest.TestCase):
	filename = "data/english_id3v2.2_only.mp3"	

class ID3v1v2Test(unittest.TestCase):
	filename = "data/chinese_id3v1_v2.mp3"

class ID3v2LoadTest1(ID3v2_2File1, ID3v2LoadTest):
	pass

class ID3v2LoadTest2(ID3v2_2File2, ID3v2LoadTest):
	pass
	
class ID3v2LoadTest3(ID3v2_2Crash, ID3v2LoadTest):
    pass

if __name__ == "__main__":
	suite = unittest.TestSuite()
	suite.addTest(unittest.makeSuite(ID3v2LoadTest1))
	suite.addTest(unittest.makeSuite(ID3v2LoadTest2))	
	suite.addTest(unittest.makeSuite(ID3v2LoadTest3))		
	suite.addTest(unittest.makeSuite(ID3v2_2_FrameTest))
	unittest.TextTestRunner(verbosity=2).run(suite)


	
	
