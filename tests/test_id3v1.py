import unittest
import types

"""
TODO:
- tests for exact extraction for a known mp3
- tests for writing
"""

from tagger.id3v1 import *
from tagger.exceptions import *
from tagger.constants import *

class ID3v1LoadTest(unittest.TestCase):

	def testLoadReadOnly(self):
		id3 = ID3v1(self.filename, ID3_FILE_READ)
		print id3._tag
		self.assert_(id3)

	def _testLoadModify(self):
		id3 = ID3v1(self.filename, ID3_FILE_MODIFY)
		self.assert_(id3)

	def _testLoadNew(self):
		id3 = ID3v1(self.filename, ID3_FILE_NEW)
		self.assert_(id3)

	def _testLoadInvalidModify(self):
		self.assertRaises(ID3HeaderInvalidException, ID3v1, "data/empty_file.mp3", ID3_FILE_MODIFY)

	def testLoadNotFound(self):
		self.assertRaises(ID3ParameterException, ID3v1, "data/missing.mp3", ID3_FILE_MODIFY)
class ID3v1TagAccessTest(unittest.TestCase):

	def setUp(self):
		self.id3 = ID3v1(self.filename, ID3_FILE_READ)

	def tearDown(self):
		del self.id3
		self.id3 = None


	def isString(self, x):
		self.assert_(type(x) == types.StringType)

	def testGetSongName(self):
		self.isString(self.id3.songname)
		
	def testGetArtist(self):
		self.isString(self.id3.artist)

	def testGetAlbum(self):
		self.isString(self.id3.album)		

	def testGetYear(self):
		self.isString(self.id3.year)
		
	def testGetComment(self):
		comment = self.id3.comment
		self.isString(comment)
		self.assert_(len(comment) < 29)
		
	def testGetGenre(self):
		x = self.id3.genre
		self.assert_(type(x) == types.IntType)
		
	def testGetTrack(self):
		x = self.id3.track
		self.assert_(type(x) == types.IntType)
		

class ID3v1OnlyFile1(unittest.TestCase):
	filename = "data/chinese_id3v1_only.mp3"

class ID3v1OnlyFile2(unittest.TestCase):
	filename = "data/english_id3v1_only.mp3"	

class ID3v1v2Test(unittest.TestCase):
	filename = "data/chinese_id3v1_v2.mp3"

class ID3v1LoadTest1(ID3v1OnlyFile1, ID3v1LoadTest):
	pass

class ID3v1LoadTest2(ID3v1OnlyFile2, ID3v1LoadTest):
	pass

class ID3v1TagTest1(ID3v1OnlyFile1, ID3v1TagAccessTest):
	pass

class ID3v1TagTest2(ID3v1OnlyFile2, ID3v1TagAccessTest):
	pass

if __name__ == "__main__":
	suite = unittest.TestSuite()
	suite.addTest(unittest.makeSuite(ID3v1LoadTest1))
	suite.addTest(unittest.makeSuite(ID3v1LoadTest2))	
	suite.addTest(unittest.makeSuite(ID3v1TagTest1))
	suite.addTest(unittest.makeSuite(ID3v1TagTest2))		
	unittest.TextTestRunner(verbosity=2).run(suite)


	
	
