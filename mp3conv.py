#!/usr/bin/python2.3

# TODO: need to do filter on multiple string TEXT fields

from pyid3v2 import *
from optparse import OptionParser

import sys, string

FIELDS_TO_CONVERT = ['TIT2','TPE1','TALB', 'TT2', 'TP1', 'TAL']

def quicktext(enc, text):
	return (enc, text, [text])

def main():
	global FIELDS_TO_CONVERT
	
	# construct option parser
	parser = OptionParser()
	parser.add_option("-f","--from", dest="fromencoding",
					  help="Override original encoding (ascii)",
					  default='ascii')
	parser.add_option("-t","--to", dest="toencoding",
					  help="Override target encoding (utf-16)",
					  default='utf-16')
	parser.add_option("-4","--strip-integer", action="store_true",
					  dest="stripint", default=False,
					  help="Strip first 4 bytes of tag contents. To clean some malformed tags")
	parser.add_option('-s','--singletag', dest="singletag",
					  help="Only convert this single tag",
					  default='')
	parser.add_option('-p','--pretend', action="store_true",
					  dest="pretend", default=False,
					  help="Pretend (don't write to file)")

	(options, files) = parser.parse_args()
	
	if options.singletag:
		FIELDS_TO_CONVERT = [options.singletag]
		
	errors = []
	
	for filename in files:
		print "Converting %s:" % filename
		try:
			id3 = ID3v2(filename, ID3V2_FILE_MODIFY)
		except ID3Exception:
			errors.append((filename, "Unable to find ID3v2 tag"))
			id3 = ID3v2(filename, ID3V2_FILE_NEW)

		id3v1 = ID3v1(filename)
		id3v1.parse()
		if not id3v1.tag.has_key("songname"):
			errors.append((filename, "Unable to find ID3v1 tag"))
			
		framekeys = []
		

		for f in id3.frames:
			framekeys.append(f.fid)
			if f.fid in FIELDS_TO_CONVERT:
				if options.stripint:
					stripped = f.fields[1][4:]
				else:
					stripped = f.fields[1]

				# if the field is empty, maybe check ID3v1 ?
				if len(f.fields[1]) == 0:
					if f.fid == 'TALB' and id3v1.tag.has_key("album"):
						f.fields = quicktext(ID3V2_FIELD_ENC_ISO8859_1, id3v1.tag["album"])
					elif f.fid == 'TPE1' and id3v1.tag.has_key("artist"):
						f.fields = quicktext(ID3V2_FIELD_ENC_ISO8859_1, id3v1.tag["artist"])
					elif f.fid == 'TIT2' and id3v1.tag.has_key("songname"):
						f.fields = quicktext(ID3V2_FIELD_ENC_ISO8859_1, id3v1.tag["songname"])
						
				# convert from ascii
				if ID3v2Frame.encodings[f.fields[0]] == 'iso8859-1':
					try:
						utf = stripped.decode(options.fromencoding)
					except (UnicodeDecodeError, UnicodeEncodeError):
						errors.append((filename, "Unable to convert: %s from %s encoding (%s)" % (f.fid, options.fromencoding, str([stripped]))))
						continue
				else:
					utf = stripped

				if options.toencoding in ['utf-8', 'utf-16', 'utf-16be']:
					f.fields = (ID3v2Frame.encodings[options.toencoding], utf, [utf])
				else:
					f.fields = (ID3V2_FIELD_ENC_ISO8859_1, utf.encode(parser.toencoding), [utf.encode(parser.toencoding)])
			elif f.fid[0] == 'T':
				if options.stripint:
					f.fields = (f.fields[0], f.fields[1][4:], [f.fields[1][4:]])


		# check if TALB, TPE1 and TIT2 are present, if not, add them from ID3v1
		if 'TALB' not in framekeys and \
			   'TAL' not in framekeys and \
			   id3v1.tag.has_key("album"):
			
			if id3.tag["version"] > 0x200: newframe = ID3v2Frame(fid='TALB')
			elif id3.tag["version"] == 0x200: newframe = ID3v2_2Frame(fid='TAL')
			try:
				newframe.fields = quicktext(ID3V2_FIELD_ENC_UTF16,
											id3v1.tag["album"].strip().decode(options.fromencoding))
				newframe.meta = {"status":0,"format":0}			
				id3.frames.append(newframe)
			except UnicodeDecodeError:
				errors.append((filename, "Unable to convert ID3v1 to TALB"))
				
		if 'TIT2' not in framekeys \
			   and 'TT2' not in framekeys \
			   and id3v1.tag.has_key("songname"):
			if id3.tag["version"] > 0x200: newframe = ID3v2Frame(fid='TIT2')
			elif id3.tag["version"] == 0x200: newframe = ID3v2_2Frame(fid='TT2')
			try:
				newframe.fields = quicktext(ID3V2_FIELD_ENC_UTF16,
								   id3v1.tag["songname"].strip().decode(options.fromencoding))
				newframe.meta = {"status":0,"format":0}			
				id3.frames.append(newframe)
			except UnicodeDecodeError:
				errors.append((filename, "Unable to convert ID3v1 to TIT2"))
				pass			
			
		if 'TPE1' not in framekeys \
			   and 'TP1' not in framekeys \
			   and id3v1.tag.has_key("artist"):
			if id3.tag["version"] > 0x200: newframe = ID3v2Frame(fid='TPE1')
			elif id3.tag["version"] == 0x200: newframe = ID3v2_2Frame(fid='TP1')
			try:
				newframe.fields = quicktext(ID3V2_FIELD_ENC_UTF16,
								   id3v1.tag["artist"].strip().decode(options.fromencoding))
				newframe.meta = {"status":0,"format":0}			
				id3.frames.append(newframe)
			except UnicodeDecodeError:
				errors.append((filename, "Unable to convert ID3v1 to TPE1"))
				pass

		if 'TRCK' not in framekeys \
			   and 'TRK' not in framekeys \
			   and id3v1.tag.has_key("track") \
			   and id3v1.tag["track"] != -1:
			if id3.tag["version"] > 0x200: newframe = ID3v2Frame(fid='TRCK')
			elif id3.tag["version"] == 0x200: newframe = ID3v2_2Frame(fid='TRK')
			try:
				newframe.fields = (ID3V2_FIELD_ENC_ISO8859_1,
								   str(id3v1.tag["track"]),
								   [str(id3v1.tag["track"])])

				newframe.meta = {"status":0,"format":0}			
				id3.frames.append(newframe)
			except UnicodeDecodeError:
				errors.append((filename, "Unable to convert ID3v1 to TRK"))
				pass

		if 'TYER' not in framekeys \
			   and 'TYE' not in framekeys \
			   and id3v1.tag.has_key("year"):
			if id3.tag["version"] > 0x200: newframe = ID3v2Frame(fid='TYER')
			elif id3.tag["version"] == 0x200: newframe = ID3v2_2Frame(fid='TYE')
			try:
				newframe.fields = (ID3V2_FIELD_ENC_ISO8859_1,
								   id3v1.tag["year"],
								   [id3v1.tag["year"]])

				newframe.meta = {"status":0,"format":0}			
				id3.frames.append(newframe)
			except UnicodeDecodeError:
				errors.append((filename, "Unable to convert ID3v1 to TYE"))
				pass						

		id3.commit(pretend=options.pretend)

	if errors:
		for x in errors:
			print x[0], ":", x[1]
		
if __name__ == "__main__":
	main()
