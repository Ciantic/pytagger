#!/usr/bin/python2.3
"""
Pure Python ID3v1/v2 Tag Parser/Writer
--------------------------------------

This is an implementation purely in Python. You can use Python bindings
to existing libraries such as id3lib or libid3tag (from libmad.) The
reason for using this is because you can easily modify how fields are
parsed and make your own customisations and hacks around dodgy files.

The sole reason this exists is because I found that different ID3
implementations were incompatible with each other because of the
sketchy standards from id3.org. Specifically, I was trying to massage
MP3s with Chinese tags encoded in either BIG5 or UTF-8 to iTunes format.
iTunes stores its ID3v2 tags using UTF-16 and ID3v1 tags using native
encoding (BIG5) or untouched. On the other hand, libid3tag stores tags
in UTF-8 but forgets to set the encoding bit properly, so other programs
cannot parse the tags properly (or believe they are invalid).

I'll document quirks as I find them for each player I come across, but
for now, I only use Linux and MacOSX, which means I can only play around
with *nix libraries such as id3lib and libid3tag and iTunes.

The parser is based on the specifications for ID3v1.1 and ID3v2.4.
Support for older ID3v2.2/3 tags is planned. Currently, this only works
on tags for MP3 files.

License
-------
This module is licensed under the BSD license. I would appreciate it
if you give me a quick email if you find it useful :) More details in
the COPYING file included with this distribution.

Usage
-----

There are 2 simple classes, ID3v2 and ID3v1. They both take an MP3
file as constructors:

   id3file = ID3v2('goodsong.mp3')

Once the file is parsed, you can access the internal structures as:

   ID3v2.tag    <--- Properties of the ID3v2 tag
   ID3v2.frames <--- A list of frames objects present in the tag
   ID3v2Frame.fid    <-- frame ID, either 3 or 4 character string
   ID3v2Frame.fields <-- a tuple of frames

You can directly remove/edit/replace the frames and tag information
in the class and then commit to disk by executing:

   id3file.commit()

Changes
-------
  v 0.1 : Alastair Tse <acnt2@cam.ac.uk> - Initial Release

"""


import os, sys, struct, types, tempfile

# constants
ID3V2_FILE_HEADER_LENGTH = 10
ID3V2_FILE_EXTHEADER_LENGTH = 5
ID3V2_FRAME_HEADER_LENGTH = 10
ID3V2_2_FRAME_HEADER_LENGTH = 6

ID3V2_FIELD_ENC_ISO8859_1 = 0
ID3V2_FIELD_ENC_UTF16 = 1
ID3V2_FIELD_ENC_UTF16BE = 2
ID3V2_FIELD_ENC_UTF8 = 3

ID3V2_FILE_READ = 0
ID3V2_FILE_MODIFY = 1
ID3V2_FILE_NEW = 2

ID3V2_FILE_DEFAULT_PADDING = 2048

ID3V2_DEBUG = 0

def _debug(args):
	if ID3V2_DEBUG > 1: print args
def _warn(args):
	if ID3V2_DEBUG > 0: print args
def _error(args):
	print args

#
# Data Utility Functions 
#

def syncsafe(num, size):
	"""	Given a number, sync safe it """
	result = ''
	for i in range(0,size):
		x = (num >> (i*7)) & 0x7f
		result = chr(x) + result
	return result

def nosyncsafe(data):
	return struct.unpack('!I', data)[0]

def unsyncsafe(data):
	"""
	Given a byte string, it will assume it is big-endian and un-SyncSafe
	a number
	"""
	bytes = len(data)
	bs = struct.unpack("!%dB" % bytes, data)
	total = 0
	for i in range(0,bytes-1):
		total += bs[bytes-1-i] * pow(128,i)
	return total

class ID3Exception(Exception):
	def __init__(self, err):
		self.err = err
	def __repr__(self):
		return err

class ID3v2Frame:
	""" ID3v2 2.4 Frame Parser/Constructor """

	header_length = ID3V2_FRAME_HEADER_LENGTH

	encodings = {'iso8859-1':0,
				 'utf-16':1,
				 'utf-16be':2,
				 'utf-8':3,
				 0:'iso8859-1',
				 1:'utf-16',
				 2:'utf-16be',
				 3:'utf-8'}

	frames_text_id = ['TIT1','TIT2','TIT3','TALB','TOAL','TRCK','TPOS',\
					  'TSST','TSRC']
	frames_text_person = ['TPE1','TPE2','TPE3','TPE4','TOPE','TEXT',\
						  'TOLY','TCOM','TMCL','TIPL','TENC']
	frames_text_prop = ['TBPM','TLEN','TKEY','TLAN','TCON','TFLT','TMED']
	frames_text_rights = ['TCOP','TPRO','TPUB','TOWN','TRSN','TRSO']
	frames_text_others = ['TOFN','TDLY','TDEN','TDOR','TDRC','TDRL',\
						  'TDTG','TSSE','TSOA','TSOP','TSOT']
	frames_url = ['WCOM','WCOP','WOAF','WOAR','WOAS','WORS','WPAY',\
				  'WPUB']
	
	only_2_4 = ['ASPI','EQU2','RVA2','SEEK','SIGN','TDEN','TDOR','TDRC',\
				'TDRL','TDTG','TIPL','TMCL','TMOO','TPRO','TSOA','TSOP',\
				'TSOT','TSST']

	only_2_3 = ['EQUA','IPLS','RVAD','TDAT','TIME','TORY','TRDA','TSIZ',\
				'TYER']
	
	supported = {
		'AENC':('bin','Audio Encryption'), # FIXME
		'APIC':('apic','Attached Picture'),
		'ASPI':('bin','Seek Point Index'), # FIXME		
		'COMM':('comm','Comments'),
		'COMR':('bin','Commerical Frame'), # FIXME
		'EQU2':('bin','Equalisation'), # FIXME		
		'ENCR':('bin','Encryption method registration'), # FIXME
		'ETCO':('bin','Event timing codes'), # FIXME
		'GEOB':('geob','General Encapsulated Object'),
		'GRID':('bin','Group ID Registration'), # FIXME
		'LINK':('link','Linked Information'), # FIXME
		'MCDI':('bin','Music CD Identifier'),
		'MLLT':('bin','Location lookup table'), # FIXME
		'OWNE':('bin','Ownership frame'), # FIXME
		'PCNT':('pcnt','Play Counter'),
		'PRIV':('bin','Private frame'), # FIXME
		'POPM':('bin','Popularimeter'), # FIXME
		'POSS':('bin','Position Synchronisation frame'), # FIXME
		'RBUF':('bin','Recommended buffer size'), # FIXME
		'RVA2':('bin','Relative volume adjustment'), #FIXME
		'RVRB':('bin','Reverb'), # FIXME
		'SIGN':('bin','Signature'), # FIXME
		'SEEK':('pcnt','Seek'),
		'SYTC':('bin','Synchronised tempo codes'), # FIXME
		'SYLT':('bin','Synchronised lyrics/text'), # FIXME
		'TALB':('text','Album/Movie/Show Title'),
		'TBPM':('text','BPM'),
		'TCOM':('text','Composer'),		
		'TCON':('text','Content type'),		
		'TCOP':('text','Copyright'),
		'TDEN':('text','Encoding time'),
		'TDLY':('text','Playlist delay'),
		'TDOR':('text','Original release time'),
		'TDRC':('text','Recording time'),
		'TDRL':('text','Release time'),
		'TDTG':('text','Tagging time'),
		'TENC':('text','Encoded by'),		
		'TEXT':('text','Lyricist/Text writer'),
		'TFLT':('text','File type'),
		'TIPL':('text','Musicians credits list'),
		'TIT1':('text','Content group description'),
		'TIT2':('text','Title/Songname/Content Description'),
		'TIT3':('text','Subtitle/Description refinement'),
		'TKEY':('text','Initial Key'),
		'TLAN':('text','Language'),
		'TLEN':('text','Length'),
		'TMCL':('text','Musician credits list'),
		'TMED':('text','Media type'),
		'TOAL':('text','Original album/movie/show title'),
		'TOFN':('text','Original Filename'),
		'TOPE':('text','Original artist/performer'),
		'TOLY':('text','Original lyricist/text writer'),
		'TOWN':('text','File owner/licensee'),
		'TPE1':('text','Lead Performer(s)/Soloist(s)'),
		'TPE2':('text','Band/Orchestra Accompaniment'),
		'TPE3':('text','Conductor'),
		'TPE4':('text','Interpreted, remixed by'),
		'TPOS':('text','Part of a set'), # [0-9/]
		'TPUB':('text','Publisher'),
		'TRCK':('text','Track'), # [0-9/]
		'TRSN':('text','Internet radio station name'),
		'TRSO':('text','Internet radio station owner'),
		'TSOA':('text','Album sort order'),
		'TSOP':('text','Performer sort order'),
		'TSOT':('text','Title sort order'),
		'TSSE':('text','Software/Hardware and settings used for encoding'),
		'TSST':('text','Set subtitle'),
		'TSRC':('text','International Standard Recording Code (ISRC)'), # 12 chars
		'TXXX':('wxxx','User defined text'),
		'UFID':('bin','Unique File Identifier'), # FIXME
		'USER':('bin','Terms of use frame'), # FIXME (similar to comment)
		'USLT':('comm','Unsynchronised lyris/text transcription'),
		'WCOM':('url','Commercial Information URL'),
		'WCOP':('url','Copyright/Legal Information'),
		'WOAF':('url','Official audio file webpage'),		
		'WOAR':('url','Official artist performance webpage'),
		'WOAS':('url','Official audio source webpage'),
		'WORS':('url','Official internet radio station homepage'),
		'WPAY':('url','Payment URL'),
		'WPUB':('url','Official publisher webpage'),
		'WXXX':('wxxx','User defined URL link frame'),
		
		'EQUA':('bin','Equalization'),
		'IPLS':('bin','Invovled people list'),
		'RVAD':('bin','Relative volume adjustment'),
		'TDAT':('text','Date'),
		'TIME':('text','Time'),
		'TORY':('text','Original Release Year'),
		'TRDA':('text','Recording date'),
		'TSIZ':('text','Size'),
		'TYER':('text','Year')		
		}
	
	version = 2.4

	def __init__(self, frame='', fid=''):
		if fid:
			if fid not in self.supported.keys():
				raise ID3Exception("Unsupported ID3v2 Field: %s" % fid)
			else:
				self.fid = fid
				self.new_frame_header()
				
		elif frame:
			self.parse_frame_header(frame)
			self.parse_field()

	def new_frame_header(self):
		self.meta = {'status':0, 'format':0, 'length':0, 'tagpreserve':0, 'filepreserve':0, 'readonly':0, 'groupinfo':0, 'compression':0, 'encryption':0, 'sync':0, 'datalength':0, 'data':0}

	def parse_frame_header(self, frame):
		# apple's id3 tags doesn't seem to follow the unsync safe format?
		frame_header = frame[:ID3V2_FRAME_HEADER_LENGTH]
		(fid, rawsize, status, format) = struct.unpack("!4sIBB", frame_header)
		
		self.fid = fid

		self.meta = {}
		self.meta["length"] = rawsize
		self.meta["status"] = status
		self.meta["format"] = format
		self.meta["tagpreserve"] = status & 0x40 >> 6
		self.meta["filepreserve"] = status & 0x020 >> 5
		self.meta["readonly"] = status & 0x10 >> 4
		self.meta["groupinfo"] = format & 0x40 >> 6
		self.meta["compression"] = format & 0x08 >> 3
		self.meta["encryption"] = format & 0x04 >> 2
		self.meta["sync"] = format & 0x02 >> 1
		self.meta["datalength"] = format & 0x01
		self.meta["data"] = frame[ID3V2_FRAME_HEADER_LENGTH:]

	def output(self):
		fieldstr = self.output_field()
		# FIXME: no syncsafe
		# FIXME: no status/format flags
		header = self.fid + struct.pack('!IBB', len(fieldstr), \
										self.meta["status"], \
										self.meta["format"])

		return header + fieldstr

	def parse_field(self):
		if self.fid not in self.supported.keys():
			_warn("Unrecognised Frame: %s" % str([self.fid]))			
			raise ID3Exception("Unsupported ID3v2 Field: %s" % self.fid)
		parser = self.supported[self.fid][0]
		self.fields = eval('self.x_' + parser + '()')

	def output_field(self):
		if self.fid not in self.supported.keys():
			_warn("Unrecognised Frame: %s" % str([self.fid]))
			raise ID3Exception("Unsupported ID3v2 Field: %s" % self.fid)
		parser = self.supported[self.fid][0]
		return eval('self.o_' + parser + '()')

	def o_string(self, s, toenc, inenc='iso8859-1'):
		"""
		Converts a String or Unicode String to a byte string of specified encoding
		"""
		try:
			outenc = self.encodings[toenc]
		except KeyError:
			outenc = 'iso8859-1'

		outstring = ''
		if type(s) == types.StringType:
			try:
				outstring = s.decode(inenc).encode(outenc)
			except (UnicodeEncodeError, UnicodeDecodeError):
				# FIXME: output warning
				outstring = s
		elif type(s) == types.UnicodeType:
			try:
				outstring = s.encode(outenc)
			except UnicodeEncodeError:
				# FIXME: output warning, unable to convert to byte string
				outstring = ''
		return outstring
		

	def o_text(self):
		targetenc = self.fields[0]
		_debug("%s %s" % (self.fid, str(self.fields)))
		strings = self.fields[2]
		newstrings = []
		for s in strings:
			newstrings.append(self.o_string(s, targetenc))
		if self.encodings[targetenc] in ['utf-16', 'utf-16be']:
			return chr(targetenc) + '\x00\x00'.join(newstrings)
		else:
			return chr(targetenc) + '\x00'.join(newstrings)

	def x_text(self):
		# FIXME: handle multiple strings seperated by \x00
		data = self.meta['data']
		encoding = ord(data[0])
		
		rawtext = data[1:]
		if self.encodings[encoding] == 'iso8859-1':
			text = rawtext
			strings = text.split('\x00')
		else:
			text = rawtext.decode(self.encodings[encoding])
			if self.encodings[encoding] == 'utf-8':
				strings = text.split('\x00')
			else:
				strings = text.split('\x00\x00')
		try:
			text.encode('utf-8')
			_debug('Read Field: %s Len: %d Enc: %d Text: %s' %
				   (self.fid, self.meta["length"], encoding, str([text])))
		except UnicodeDecodeError:
			_debug('Read Field: %s Len: %d Enc: %d Text: %s (Err)' %
				   (self.fid, self.meta["length"], encoding, str([text])))
			
		return (encoding, text, strings)

	def o_comm(self):
		targetenc = self.fields[0]
		lang = self.fields[1]
		shortcomment = self.fields[2]
		longcomment = self.fields[3]
		if self.encodings[targetenc] in ['utf-16', 'utf-16be']:
			sep = '\x00\x00'
		else:
			sep = '\x00'
			
		return chr(targetenc) + lang + \
			   self.o_string(shortcomment, targetenc) + sep + \
			   self.o_string(longcomment, targetenc) + sep

	def x_comm(self):
		data = self.meta['data']
		encoding = ord(data[0])
		language = data[1:4]
		shortcomment = ''
		longcomment = ''

		if self.encodings[encoding] in ['utf-16', 'utf-16be']:
			for i in range(4,len(data)-1):
				if data[i:i+2] == '\x00\x00':
					shortcomment = data[4:i].strip('\x00')
					longcomment = data[i+2:].strip('\x00')
					break
		else:
			for i in range(4,len(data)):
				if data[i] == '\x00':
					shortcomment = data[4:i].strip('\x00')
					longcomment = data[i+1:].strip('\x00')
					break
				
		_debug('Read Field: %s Len: %d Enc: %d Lang: %s Comm: %s' %
			   (self.fid, self.meta["length"],
				encoding, language, str([shortcomment, longcomment])))
		
		return (encoding, language, shortcomment, longcomment)



	def o_pcnt(self):
		counter = ''
		if self.meta["length"] == 4:
			counter = struct.pack('!I', self.fields[0])
		else:
			for i in range(0,bytes):
				x = (self.fields[0] >> (i*8) ) & 0xff
				counter = counter + struct.pack('!B',x)
		return counter
     
	def x_pcnt(self):
		data = self.meta["data"]
		bytes = self.meta["length"]
		counter = 0
		if bytes == 4:
			counter = struct.unpack('!I',data)[0]
		else:
			for i in range(0,bytes):
				counter += struct.unpack('B',data[i]) * pow(256,i)
				
		_debug('Read Field: %s Len: %d Count: %d' % (self.fid, bytes, counter))
		return (counter,)		

	def o_bin(self):
		return self.fields[0]

	def x_bin(self):
		return (self.meta["data"],)

	def o_wxxx(self):
		targetenc = self.fields[0]
		desc = self.fields[1]
		url = self.fields[2]
		if self.encodings[targetenc] in ['utf-16', 'utf-16be']:
			return chr(targetenc) + \
				   self.o_string(desc,targetenc) + '\x00\x00' + \
				   self.o_string(url,targetenc) + '\x00\x00'
		else:
			return chr(targetenc) + \
				   self.o_string(desc, targetenc) + '\x00' + \
				   self.o_string(url,targetenc) + '\x00'

	def x_wxxx(self):
		data = self.meta["data"]
		encoding = ord(data[0])
		if self.encodings[encoding] in ['utf-16', 'utf-16be']:
			for i in range(1,len(data)-1):
				if data[i:i+2] == '\x00\x00':
					desc = data[1:i]
					url = data[i+2:]
					break
		else:
			for i in range(1,len(data)):
				if data[i] == '\x00':
					desc = data[1:i]
					url = data[i+1:]
					break

		_debug("Read field: %s Len: %s Enc: %d Desc: %s URL: %s" %
			   (self.fid, self.meta["length"], encoding, desc, str([url])))
		
		return (encoding, desc, url)

	def o_apic(self):
		targetenc = self.fields[0]
		mimetype = self.fields[1]
		picttype = self.fields[2]
		desc = self.fields[3]		
		pictdata = self.fields[4]
		if self.encodings[targetenc] in ['utf-16','utf-16be']:
			sep = '\x00\x00'
		else:
			sep = '\x00'
		return chr(targetenc) + mimetype + '\x00' + \
			   chr(picttype) + self.o_string(desc, targetenc) + \
			   sep + pictdata


	def x_apic(self):
		data = self.meta["data"]
		encoding = ord(data[0])
		mimetype = ''
		desc = ''
		pict = ''
		picttype = 0

		# get mime type (must be iso8859-1)
		for i in range(1,len(data)):
			if data[i] == '\x00':
				mimetype = data[1:i]
				break

		picttype = ord(data[len(mimetype) + 2])

		# get picture description

		if self.encodings[encoding] in ['utf-16', 'utf-16be']:
			for i in range(len(mimetype) + 2, len(data)-1):
				if data[i:i+2] == '\x00\x00':
					desc = data[len(mimetype)+2:i]
					pict = data[i+2:]
					break
		else:
			for i in range(len(mimetype) + 2, len(data)):
				if data[i] == '\x00':
					desc = data[len(mimetype)+2:i]
					pict = data[i+1:]
					break			
		_debug('Read Field: %s Len: %d PicType: %d Mime: %s Desc: %s PicLen: %d' % 
			   (self.fid, self.meta["length"], picttype, mimetype, desc, len(pict)))
		
		# open("test.png","w").write(pictdata)
		return (encoding, mimetype, picttype, desc, pict)


	def o_url(self):
		return self.fields[0]

	def x_url(self):
		_debug("Read Field: %s Len: %d Data: %s" %
			   (self.fid, self.meta["length"], [self.meta["data"]]))
		return (self.meta["data"],)

	def o_geob(self):
		if self.encodings[self.fields[0]] in ['utf-16', 'utf-16be']:
			return chr(self.fields[0]) + self.fields[1] + '\x00' + \
				   self.fields[2] + '\x00\x00' + self.fields[3] + \
				   '\x00\x00' + self.fields[4]
		else:
			return chr(self.fields[0]) + self.fields[1] + '\x00' + \
				   self.fields[2] + '\x00' + self.fields[3] + \
				   '\x00' + self.fields[4]			

	def x_geob(self):
		data = self.meta["data"]
		encoding = ord(data[0])
		filename = ''
		desc = ''
		obj = ''
		
		for i in range(1,len(data)):
			if data[i] == '\x00':
				mimetype = data[1:i]
				break
			
		# FIXME: because filename and desc are optional, we should be
		#        smarter about splitting
		if self.encodings[encoding] in ['utf-16', 'utf-16be']:
			for i in range(len(mimetype)+2,len(data)-1):
				if data[i:i+2] == '\x00\x00':
					filename = data[len(mimetype)+2:i]
					ptr = len(mimetype) + len(filename) + 4
					break
		else:
			for i in range(len(mimetype)+2,len(data)-1):
				if data[i] == '\x00':
					filename = data[len(mimetype)+2:i]
					ptr = len(mimetype) + len(filename) + 3
					break

		if self.encodings[encoding] in ['utf-16', 'utf-16be']:
			for i in range(ptr,len(data)-1):
				if data[i:i+2] == '\x00\x00':
					desc = data[ptr:i]
					obj = data[i+2:]
					break
		else:
			for i in range(ptr,len(data)-1):
				if data[i] == '\x00':
					desc = data[ptr:i]
					obj = data[i+1:]
					break
		
		_debug("Read Field: %s Len: %d Enc: %d Mime: %s Filename: %s Desc: %s ObjLen: %d" %
			   (self.fid, self.meta["length"], encoding, mimetype, filename, desc, len(obj)))
		return (encoding, mimetype, filename, desc, obj)

class ID3v2_2Frame(ID3v2Frame):

	header_length = ID3V2_2_FRAME_HEADER_LENGTH

	supported = {
		'UFI':('bin','Unique File Identifier'), # FIXME
		'BUF':('bin','Recommended buffer size'), # FIXME
		'CNT':('pcnt','Play counter'),
		'COM':('comm','Comments'),
		'CRA':('bin','Audio Encryption'), # FIXME
		'CRM':('bin','Encrypted meta frame'), # FIXME
		'EQU':('bin','Equalisation'), # FIXME
		'ETC':('bin','Event timing codes'),
		'GEO':('geob','General Encapsulated Object'),
		'IPL':('bin','Involved People List'), # null term list FIXME
		'LNK':('bin','Linked Information'), # FIXME
		'MCI':('bin','Music CD Identifier'), # FIXME
		'MLL':('bin','MPEG Location Lookup Table'), # FIXME
		'PIC':('apic','Attached Picture'),
		'POP':('bin','Popularimeter'), # FIXME
		'REV':('bin','Reverb'), # FIXME
		'RVA':('bin','Relative volume adjustment'), # FIXME
		'STC':('bin','Synced Tempo Codes'), # FIXME
		'SLT':('bin','Synced Lyrics/Text'), # FIXME
		'TAL':('text','Album/Movie/Show'),
		'TBP':('text','Beats per Minute'),
		'TCM':('text','Composer'),
		'TCO':('text','Content Type'),
		'TCR':('text','Copyright message'),
		'TDA':('text','Date'),
		'TDY':('text','Playlist delay (ms)'),
		'TEN':('text','Encoded by'),
		'TIM':('text','Time'),
		'TKE':('text','Initial key'),
		'TLA':('text','Language(s)'),
		'TLE':('text','Length'),
		'TMT':('text','Media Type'),
		'TP1':('text','Lead artist(s)/Lead performer(s)/Performing group'),
		'TP2':('text','Band/Orchestra/Accompaniment'),
		'TP3':('text','Conductor'),
		'TP4':('text','Interpreted, remixed by'),
		'TPA':('text','Part of a set'),		
		'TPB':('text','Publisher'),
		'TOA':('text','Original artist(s)/performer(s)'),
		'TOF':('text','Original Filename'),
		'TOL':('text','Original Lyricist(s)/text writer(s)'),
		'TOR':('text','Original Release Year'),
		'TOT':('text','Original album/Movie/Show title'),
		'TRC':('text','International Standard Recording Code (ISRC'),
		'TRD':('text','Recording dates'),
		'TRK':('text','Track number/Position in set'),
		'TSI':('text','Size'),
		'TSS':('text','Software/hardware and settings used for encoding'),
		'TT1':('text','Content Group Description'),
		'TT2':('text','Title/Songname/Content Description'),
		'TT3':('text','Subtitle/Description refinement'),
		'TXT':('text','Lyricist(s)/Text Writer(s)'),
		'TYE':('text','Year'),
		'TXX':('wxxx','User defined text information'),
		'ULT':('bin','Unsynced Lyrics/Text'),
		'WAF':('url','Official audio file webpage'),
		'WAR':('url','Official artist/performer webpage'),
		'WAS':('url','Official audio source webpage'),
		'WCM':('url','Commercial information'),
		'WCP':('url','Copyright/Legal Information'),
		'WPM':('url','Official Publisher webpage'),
		'WXX':('wxxx','User defined URL link frame')
		}

	version = 2.2

	def parse_frame_header(self, frame):
		# apple's id3 tags doesn't seem to follow the unsync safe format?
		frame_header = frame[:self.header_length]
		fid = frame_header[0:3]
		size = struct.unpack('!I','\x00' + frame_header[3:6])[0]
		
		self.fid = fid

		self.meta = {}
		self.meta["length"] = size
		self.meta["data"] = frame[self.header_length:]

	def output(self):
		fieldstr = self.output_field()
		# FIXME: no syncsafe
		# NOTE: ID3v2 uses only 3 bytes for size, so we strip of MSB
		header = self.fid + struct.pack('!I', len(fieldstr))[1:]
		return header + fieldstr

	def parse_field(self):
		if self.fid not in self.supported.keys():
			_error("Unrecognised Frame: %s" % str([self.fid]))
			raise ID3Exception("Unsupported ID3v2 Field: %s" % self.fid)
		parser = self.supported[self.fid][0]
		self.fields = eval('self.x_' + parser + '()')
		
	def x_text(self):
		(encoding, text, strings) = ID3v2Frame.x_text(self)
		return (encoding, strings[0])
		
	def o_text(self):
		targetenc = self.fields[0]
		_debug("%s %s" % (self.fid, self.fields))
		newstring = self.o_string(self.fields[1], targetenc)
		if self.encodings[targetenc] in ['utf-16', 'utf-16be']:
			return chr(targetenc) + newstring + '\x00\x00'
		else:
			return chr(targetenc) + newstring + '\x00'
	
class ID3v2:
	"""ID3v2 Tag Parser for MP3 files"""

	supported = ['2.2', '2.3', '2.4']
	
	def __init__(self, filename, mode=ID3V2_FILE_READ):
		if mode == ID3V2_FILE_READ:
			self.f = open(filename, 'rb')
		elif mode in [ID3V2_FILE_MODIFY, ID3V2_FILE_NEW]:
			self.f = open(filename, 'rb+')
			
		self.mode = mode
		self.filename = filename
		
		if mode in [ID3V2_FILE_READ, ID3V2_FILE_MODIFY]:
			if self.parse_header() == 0:
				raise ID3Exception("Unable to parse ID3v2 header.")
		
			self.parse_frames()
		elif mode == ID3V2_FILE_NEW:
			self.new_header()

	def read_null_bytes(self):
		# hit null bytes, read until the end of the frame
		nullbuffer = 0
		while 1:
			if self.f.read(1) == '\x00':
				nullbuffer += 1
			else:
				break
		return nullbuffer

	def seek_to_sync(self):
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

	def new_header(self, version='2.4'):
		""" Create a new default ID3v2 tag """
		self.tag = {}
		if version == '2.4':
			self.tag["version"] = 0x0400
		elif version == '2.3':
			self.tag["version"] = 0x0300
		elif version == '2.2':
			self.tag["version"] = 0x0200

		if version in ['2.4', '2.3']:
			self.tag["ext"] = 0
			self.tag["exp"] = 0
			self.tag["footer"] = 0
		elif version == '2.2':
			self.tag["compression"] = 0
			
		self.tag["unsync"] = 0
		self.tag["size"] = 0
		self.frames = []
	
	def parse_header(self):
		data = self.f.read(ID3V2_FILE_HEADER_LENGTH)
		self.tag = {}
		self.frames = []
		id3, ver, flags, rawsize = struct.unpack("!3sHB4s", data)
		if id3 != "ID3":
			return 0
		else:
			self.tag["size"] = unsyncsafe(rawsize)
			# size  = excluding header + footer
			self.tag["version"] = ver
			self.tag["flags"] = flags
			self.tag["unsync"] = (flags & 0x80) >> 7
			if ver in [0x0400, 0x0300]:
				self.tag["ext"] = (flags & 0x40) >> 6
				self.tag["exp"] = (flags & 0x20) >> 5
				self.tag["footer"] = (flags & 0x10) >> 4
			elif ver == 0x0200:
				self.tag["compression"] = (flags & 0x40) >> 6
				
		if self.tag.has_key("ext") and self.tag["ext"]:
			self.parse_ext_header()
	
		_debug(self.tag)
		return 1
    
	def parse_ext_header(self):
		""" Parse Extension Header """
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
		""" Parse Footer """
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
					if self.tag["version"] == 0x200:
						frame = ID3v2_2Frame(frame=framedata)
					else:
						frame = ID3v2Frame(frame=framedata)
					readframes += 1
					self.frames.append(frame)
				except ID3Exception:
					pass # ignore unrecognised frames
			else:
				self.tag["padding"] = self.read_null_bytes()
				_debug("NULL Padding: %d" % self.tag["padding"])
				break
			
		return len(self.frames)

	def get_next_frame(self, max):
		if self.tag['version'] == 0x0200:
			# read first byte
			c = self.f.read(1)
			self.f.seek(-1,1)
			if c == '\x00':
				return '' # check for NULL frames
			hdr = self.f.read(ID3V2_2_FRAME_HEADER_LENGTH)
			size = struct.unpack('!I', '\x00'+hdr[3:6])[0]
			data = self.f.read(size)
			return hdr + data
		elif self.tag['version'] == 0x0300 or self.tag['version'] == 0x0400:
			# read first byte
			c = self.f.read(1)
			self.f.seek(-1,1)
			if c == '\x00': # check for NULL frames/padding
				return ''
			hdr = self.f.read(ID3V2_FRAME_HEADER_LENGTH)
			# note: apple itunes does not syncsafe this
			size = struct.unpack('!I',hdr[4:8])[0]
			data = self.f.read(size)
			return hdr + data
		
		
	def construct_header(self, size):
		if self.tag["version"] in [0x0400, 0x0300]:
			bytestring = 'ID3'
			flags = (self.tag["unsync"] << 7) | (self.tag["ext"] << 6)
			flags = flags | (self.tag["exp"] << 5) | (self.tag["footer"] << 4)
			bytestring += struct.pack('!HB', self.tag["version"], flags)
			bytestring += syncsafe(size, 4)
		elif self.tag["version"] in  [0x0200]:
			bytestring = 'ID3'
			flags = (self.tag["unsync"] << 7) | (self.tag["compression"] << 6)
			bytestring += struct.pack('!HB', self.tag["version"], flags)
			bytestring += syncsafe(size, 4)
		return bytestring

	def construct_ext_header(self):
		self.tag['ext'] = 0
		return '' # FIXME!

	def construct_footer(self):
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
			headerstring = self.construct_header(len(framesstring+extstring) + \
												 ID3V2_FILE_DEFAULT_PADDING)
			
			# need to realign - find start of MP3
			if self.tag["version"] > 0x0200 and self.tag["footer"]:
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
				print t.tell()
				t.seek(0)
			
				buf = t.read(1024)
				while buf:
					self.f.write(buf)
					buf = t.read(1024)
				t.close()
				self.f.close()
				self.f = open(self.filename, 'rb+')
			
		else:
			headerstring = self.construct_header(self.tag['size'])
			if not pretend:
				self.f.seek(0)
				self.f.write(headerstring)
				self.f.write(extstring)
				self.f.write(framesstring)
				written = len(extstring) + len(framesstring)
				_warn("Written Bytes: %d" % written)
				self.f.write('\x00' * (self.tag["size"] - written))
				self.f.write(footerstring)

class ID3v1:
    
    def __init__(self, filename, mode='rb'):
		self.f = open(filename, mode)
		self.tag = {}
	
    def __del__(self):
		self.f.close()
		
    def seek_to_id3v1(self):
		read = 0
		while 1:
			buf = self.f.read(1024)
			if len(buf) == 0:
				break
			else:
				read += len(buf)
		self.f.seek(read - 128)
	
    def parse(self):
		#self.seek_to_id3v1()
		self.f.seek(-128,2)
		id3v1 = self.f.read(128)
		tag, songname, artist, album, year, comment, genre = struct.unpack("!3s30s30s30s4s30sb", id3v1)
		if tag != "TAG":
			return 0
		else:
			if comment[28] == '\x00':
				track = ord(comment[29])
				comment = comment[0:27]
			else:
				track = -1
				
			self.tag = {}
			self.tag["songname"] = self.unpad(songname)
			self.tag["artist"] = self.unpad(artist)
			self.tag["album"] = self.unpad(album)
			self.tag["year"] = self.unpad(year)
			self.tag["comment"] = self.unpad(comment)
			self.tag["genre"] = genre
			self.tag["track"] = track
	
    def unpad(self, field, unicode=0):
		length = 0
		for x in field:
			if x == '\x00':
				break
			else:
				length += 1
		return field[:length]
	
if __name__ == "__main__":

	try:
		filename = sys.argv[1]
	except IndexError:
		filename = "Leo19-01.mp3"
		#filename = "Aaron03-02.mp3"

	id3v2 = ID3v2(filename, 'rb+')
	#id3v2.commit()
	#id3v1 = ID3v1(filename)
	#id3v1.parse()
	#print id3v1.tag
