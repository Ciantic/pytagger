"""
Copyright (c) 2004. Alastair Tse <acnt2@cam.ac.uk>
http://www-lce.eng.cam.ac.uk/~acnt2/code/pytagger/

ID3v2 Class
"""

__revision__ = "$Id: id3v2.py,v 1.3 2004/05/09 23:25:40 acnt2 Exp $"

from tagger.exceptions import *
from tagger.constants import *
from tagger.id3v2frame import *
from tagger.utility import *
from tagger.debug import *


import os, struct, sys, types, tempfile, math

class ID3v2:
	"""
	ID3v2 Tag Parser/Writer for MP3 files


	@cvar supported: list of version that this parser supports
	@ivar tag: dictionary of parameters that the tag has
	@type tag: dictionary

	@note: tag has the following options

	size = size of the whole header, excluding header and footer
	ext = has extension header (2.3, 2.4 only)
	exp = is experimental (2.4, 2.3 only)
	footer = has footer (2.3, 2.4 only)
	compression = has compression enabled (2.2 only)
	unsync = uses unsynchronise method of encoding data

	@ivar frames: list of frames that is in the tag
	@type frames: dictionary of ID3v2*Frame(s)

	@ivar version: version this tag supports
	@type version: float (2.2, 2.3, 2.4)

	@todo: parse/write footers
	@todo: parse/write appended tags
	@todo: parse/write ext header

	"""

	supported = [2.2, 2.3, 2.4]
	
	def __init__(self, filename, mode=ID3_FILE_READ, \
				 version=ID3V2_DEFAULT_VERSION):
		"""
		@param filename: the file to open or write to.
		@type filename: string

		@param mode: either ID3_FILE_NEW, ID3_FILE_READ, ID3_FILE_MODIFY. The default is ID3_FILE_READ.
		@type mode: int

		@param version: if ID3_FILE_NEW, then what version to create the header in. Default is 2.4
		@type version: float

		@raise ID3Exception: if file does not have an ID3v2 but is specified
		to be in read or modify mode.
		"""

		if version not in self.supported:
			raise ID3ParameterException("version %s not valid" % str(version))

		if not os.path.exists(filename):
			raise ID3ParameterException("filename %s not valid" % filename)
		
		if mode == ID3_FILE_READ:
			self.f = open(filename, 'rb')
		elif mode in [ID3_FILE_MODIFY, ID3_FILE_NEW]:
			self.f = open(filename, 'rb+')
			
		self.mode = mode
		self.filename = filename

		if mode in [ID3_FILE_READ, ID3_FILE_MODIFY]:
			self.parse_header()
			self.parse_frames()
		elif mode == ID3_FILE_NEW:
			self.new_header(version)

	def dump_header(self):
		"""
		Debugging purposes, dump the whole header of the file.

		@todo: dump footer and extension header as well
		"""
		old_pos = self.f.tell()
		output = ''
		if self.tag["size"]:
			self.f.seek(0)
			output = self.f.read(ID3V2_FILE_HEADER_LENGTH + self.tag["size"])
			self.f.seek(old_pos)
			
		return output

	def new_frame(self, fid=None, frame=None):
		"""
		Return a new frame of the correct type for this tag

		@param fid: frame id
		@param frame: bytes in the frame
		"""
		if self.version == 2.2:
			return ID3v2_2_Frame(frame=frame, fid=fid)
		elif self.version == 2.3:
			return ID3v2_3_Frame(frame=frame, fid=fid)
		elif self.version == 2.4:
			return ID3v2_4_Frame(frame=frame, fid=fid)
		else:
			raise ID3NotImplemented("version %f not supported." % self.version)

	def set_version(self, version):
		self.version = version

	def _read_null_bytes(self):
		"""
		Count the number of null bytes at the specified file pointer
		"""
		nullbuffer = 0
		while 1:
			if self.f.read(1) == '\x00':
				nullbuffer += 1
			else:
				break
		return nullbuffer

	def __seek_to_sync(self):
		"""
		Reads the file object until it reaches a sync frame of an MP3 file
		(FIXME - inefficient, and possibly useless)
		"""
		buf = ''
		hit = -1
		read = 0
		while hit == -1:
			# keep on reading until we have 3 chars in the buffer
			while len(buf) < 3:
				buf += self.f.read(1)
				read += 1
			# do pattern matching for a 11 bit on pattern in the first 2 bytes
			# (note: that it may extend to the third byte)
			b0,b1,b2 = struct.unpack('!3B',buf)
			if (b0 & 0xff) and (b1 & 0xe0):
				hit = 0
			elif (b0 & 0x7f) and (b1 & 0xf0):
				hit = 1
			elif (b0 & 0x3f) and (b1 & 0xf8):
				hit = 2
			elif (b0 & 0x1f) and (b1 & 0xfc):
				hit = 3
			elif (b0 & 0x0f) and (b1 & 0xfe):
				hit = 4
			elif (b0 & 0x07) and (b1 & 0xff):
				hit = 5
			elif (b0 & 0x03) and (b1 & 0xff) and (b2 & 0x80):
				hit = 6
			elif (b0 & 0x01) and (b1 & 0xff) and (b2 & 0xc0):
				hit = 7
			else:
				buf = buf[1:]
				
		return read + 0.1 * hit - 3

	def new_header(self, version=ID3V2_DEFAULT_VERSION):
		"""
		Create a new default ID3v2 tag data structure

		@param version: version of the tag to use. default is 2.4.
		@type version: float
		"""

		if version not in self.supported:
			raise ID3ParameterException("version %s not supported" % str(version))
		
		self.tag = {}
		if version in self.supported:
			self.version = version
		else:
			raise ID3NotImplementedException("Version %s not supported", \
											 str(version))

		if version in [2.4, 2.3]:
			self.tag["ext"] = 0
			self.tag["exp"] = 0
			self.tag["footer"] = 0
		elif version == 2.2:
			self.tag["compression"] = 0
			
		self.tag["unsync"] = 0
		self.tag["size"] = 0
		self.frames = []
	
	def parse_header(self):
		"""
		Parse Header of the file

		"""
		
		data = self.f.read(ID3V2_FILE_HEADER_LENGTH)
		if len(data) != ID3V2_FILE_HEADER_LENGTH:
			raise ID3HeaderInvalidException("ID3 tag header is incomplete")
		
		self.tag = {}
		self.frames = []
		id3, ver, flags, rawsize = struct.unpack("!3sHB4s", data)
		
		if id3 != "ID3":
			raise ID3HeaderInvalidException("ID3v2 header not found")

		self.tag["size"] = unsyncsafe(rawsize)
		# size  = excluding header + footer
		version = 2 + (ver / 0x100) * 0.1
		if version not in self.supported:
			raise ID3NotImplementedException("version %s not supported" % \
											 str(version))
		else:
			self.version = version
			
		if self.version in [2.4, 2.3]:
			for flagname, bit in ID3V2_3_TAG_HEADER_FLAGS:
				self.tag[flagname] = (flags >> bit) & 0x01
		elif self.version in [2.2]:
			for flagname, bit in ID3V2_2_TAG_HEADER_FLAGS:
				self.tag[flagname] = (flags >> bit) & 0x01

		if self.tag.has_key("ext") and self.tag["ext"]:
			self.parse_ext_header()
	
		debug(self.tag)
    
	def parse_ext_header(self):
		""" Parse Extension Header """

		# seek to the extension header position
		self.f.seek(ID3V2_FILE_HEADER_LENGTH)
		data = self.f.read(ID3V2_FILE_EXTHEADER_LENGTH)
		extsize, flagbytes = struct.unpack("!4sB", data)
		extsize = unsyncsafe(extsize)
		readdata = 0
		if flagbytes == 1:
			flags = struct.unpack("!B",self.f.read(flagbytes))[0]
			self.tag["update"] = ( flags & 0x40 ) >> 6
			if ((flags & 0x20) >> 5):
				self.tag["crc"] = unsyncsafe(self.f.read(5))
				readdata += 5
			if ((flags & 0x10) >> 4):
				self.tag["restrictions"] = struct.unpack("!B", self.f.read(1))[0]
				# FIXME: store these restrictions properly
				readdata += 1
				
			# work around dodgy ext headers created by libid3tag
			if readdata < extsize - ID3V2_FILE_EXTHEADER_LENGTH - flagbytes:
				self.f.read(extsize - ID3V2_FILE_EXTHEADER_LENGTH - flagbytes - readdata)
		else:
			# ignoring unrecognised extension header
			self.f.read(extsize - ID3V2_FILE_EXTHEADER_LENGTH)
		return 1
    
	def parse_footer(self):
		"""
		Parse Footer

		@todo: implement me
		"""
		return 0 # FIXME
    
	def parse_frames(self):
		""" Recursively Parse Frames """
		read = 0
		readframes = 0
		
		while read < self.tag["size"]:
			framedata = self.get_next_frame(self.tag["size"] - read)
			if framedata:
				try:
					read += len(framedata)
					if self.version == 2.2:
						frame = ID3v2_2_Frame(frame=framedata)
					elif self.version == 2.3:
						frame = ID3v2_3_Frame(frame=framedata)
					elif self.version == 2.4:
						frame = ID3v2_4_Frame(frame=framedata)
					readframes += 1
					self.frames.append(frame)
				except ID3Exception:
					pass # ignore unrecognised frames
			else:
				self.tag["padding"] = self._read_null_bytes()
				debug("NULL Padding: %d" % self.tag["padding"])
				break

		# do a sanity check on the size/padding
		if not self.tag.has_key("padding"):
			self.tag["padding"] = 0
			
		if self.tag["size"] != read + self.tag["padding"]:
			self.tag["size"] = read + self.tag["padding"]
			
		return len(self.frames)

	def get_next_frame(self, search_length):

		# skip null frames
		c = self.f.read(1)
		self.f.seek(-1, 1)
		if c == '\x00':
			return '' # check for NULL frames
		
		hdr = self.f.read(id3v2_header_len[self.version])
		size = id3v2_data_len[self.version](hdr)
		data = self.f.read(size)
		return hdr + data
		
	def construct_header(self, size):
		"""
		Construct Header Bytestring to for tag

		@param size: size to encode into the bytestring. Note the size is the whole size of the tag minus the header and footer
		@type size: int
		"""
		if self.version in [2.3, 2.4]:
			flags = ID3V2_3_TAG_HEADER_FLAGS
		elif self.version in [2.2]:
			flags = ID3V2_2_TAG_HEADER_FLAGS

		bytestring = 'ID3'
		flagbyte = 0
		for flagname, bit in flags:
			flagbyte = flagbyte | ((self.tag[flagname] & 0x01) << bit)
			
		bytestring += struct.pack('<H', int(math.ceil((self.version-2.0) * 10)))
		bytestring += struct.pack('!B', flagbyte)
		bytestring += syncsafe(size, 4)
		return bytestring

	def construct_ext_header(self):
		"""
		Construct an Extension Header (FIXME)
		"""
		self.tag['ext'] = 0
		return '' # FIXME!

	def construct_footer(self):
		"""
		Construct a Footer (FIXME)
		"""
		return '' # FIXME!
	
	def commit(self, pretend=False):
		framesstring = ''
		for f in self.frames:
			framesstring += f.output()

		footerstring = ''
		extstring = ''
		
		if self.tag.has_key("ext") and self.tag["ext"]:
			extstring = self.construct_ext_header()
		if self.tag.has_key("footer") and self.tag["footer"]:
			footerstring = self.construct_footer()

		# make sure there is enough space from start of file to
		# end of tag, otherwise realign tag
		if self.tag["size"] < len(extstring) + len(framesstring):
			headerstring = self.construct_header(len(framesstring+extstring) \
												 + ID3V2_FILE_DEFAULT_PADDING)
			
			# need to realign - find start of MP3
			if self.version > 2.2 and self.tag["footer"]:
				self.f.seek(20 + self.tag["size"])
			else:
				self.f.seek(10 + self.tag["size"])
				
			# copy everything to a temporary file
			t = tempfile.TemporaryFile()
			buf = self.f.read(1024)
			while buf:
				t.write(buf)
				buf = self.f.read(1024)
				
			# write to a new file
			if not pretend:
				self.f.close()
				self.f = open(self.filename, 'wb+')
				self.f.write(headerstring)
				self.f.write(extstring)
				self.f.write(framesstring)
				self.f.write('\x00' * ID3V2_FILE_DEFAULT_PADDING)
				self.f.write(footerstring)
				#print t.tell()
				t.seek(0)
			
				buf = t.read(1024)
				while buf:
					self.f.write(buf)
					buf = t.read(1024)
				t.close()
				self.f.close()
				self.f = open(self.filename, 'rb+')
				self.tag["size"] = len(headerstring) + len(extstring) + \
								   ID3V2_FILE_DEFAULT_PADDING
			
		else:
			headerstring = self.construct_header(self.tag["size"])
			if not pretend:
				self.f.seek(0)
				self.f.write(headerstring)
				self.f.write(extstring)
				self.f.write(framesstring)
				written = len(extstring) + len(framesstring)
				warn("Written Bytes: %d" % written)
				# add padding
				self.f.write('\x00' * (self.tag["size"] - written))
				# add footerstring
				self.f.write(footerstring)
				self.f.flush()

	
