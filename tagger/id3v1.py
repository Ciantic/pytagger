"""
Copyright (c) 2004. Alastair Tse <acnt2@cam.ac.uk>
http://www-lce.eng.cam.ac.uk/~acnt2/code/pytagger/

ID3v1 Class
"""

__revision__ = "$Id: "

from tagger.exceptions import *
from tagger.constants import *

import struct, os

class ID3v1:
	"""
	ID3v1 Class
	
	This class parses and writes ID3v1 tags using a very simplified
	interface.
	
	You can access the ID3v1 tag variables by directly accessing the
	object attributes. For example:
	
	id3v1 = ID3v1('some.mp3')
	id3v1.track = 1
	print id3v1.title
	del id3v1
	
	@ivar songname: the songname in iso8859-1
	@type songname: string
	@ivar artist: the artist name in iso8859-1
	@type artist: string
	@ivar album: the album name in iso8859-1
	@type album: string
	@ivar year: the year of the track
	@type year: string
	@ivar comment: comment string. limited to 28 characters
	@type comment: string
	@ivar genre: genre number
	@type genre: int
	@ivar track: track number
	@type track: int

	"""

	_f = None

	def __init__(self, filename, mode=ID3_FILE_READ):
		"""
		constructor

		tries to load the id3v1 data from the filename given. if it succeeds it
		will set the tag_exists parameter.

		@param filename: filename
		@type filename: string
		@param mode: ID3_FILE_{NEW,READ,MODIFY}
		@type mode: constant
		"""

		if not os.path.exists(filename):
			raise ID3ParameterException("File not found: %s" % filename)

		
		if mode == ID3_FILE_READ:
			self._f = open(filename, 'rb')
		elif mode in [ID3_FILE_MODIFY, ID3_FILE_NEW]:
			self._f = open(filename, 'r+b')
		else:
			raise ID3ParameterException("invalid mode")

		
		self._filename = filename
		self._tag = {'songname':'', 'artist:'', album:'', year':'',
					'comment':'', 'genre':0, 'track':0}

		if mode != ID3_FILE_NEW:
			self.parse()

	def __getattr__(self, name):
		if self._tag and self._tag.has_key(name):
			return self._tag[name]
		else:
			raise AttributeError, "%s not found" % name

	"""
	def __setattr__(self, name, value):
		if self._tag and self._tag.has_key(name):
			if name == 'genre' and type(value) != types.IntValue:
				raise TypeError, "genre should be an integer"
			if name == 'track' and type(value) != types.IntValue:
				raise TypeError, "track should be an integer"
			self.__dict__["_tag"][name] = value
		else:
			object.__setattr__(self, name, value)
	"""

	def __del__(self):
		if self._f:
			self._f.close()

	def seek_to_id3v1(self):
		"""
		Seek to the ID3v1 tag
		"""
		read = 0
		while 1:
			buf = self._f.read(1024)
			if len(buf) == 0:
				break
			else:
				read += len(buf)
		self._f.seek(read - 128)
		
	def parse(self):
		try:
			self._f.seek(-128, 2)
		except IOError:
			raise ID3HeaderInvalidException("not enough bytes")
			
		id3v1 = self._f.read(128)
		
		tag, songname, artist, album, year, comment, genre = \
			 struct.unpack("!3s30s30s30s4s30sb", id3v1)
		
		if tag != "TAG":
			raise ID3HeaderInvalidException("ID3v1 TAG not found")
		else:
			if comment[28] == '\x00':
				track = ord(comment[29])
				comment = comment[0:27]
			else:
				track = -1

				
			self._tag["songname"] = self.unpad(songname).strip()
			self._tag["artist"] = self.unpad(artist).strip()
			self._tag["album"] = self.unpad(album).strip()
			self._tag["year"] = self.unpad(year).strip()
			self._tag["comment"] = self.unpad(comment).strip()
			self._tag["genre"] = genre
			self._tag["track"] = track
	
	def unpad(self, field):
		length = 0
		for x in field:
			if x == '\x00':
				break
			else:
				length += 1
		return field[:length]
