#!/usr/bin/python2.3

from pyid3v2 import *

import sys, string

def strip_newline(data):
	# find new line and strip everything before it
	for i in range(0,len(data)):
		if data[i] == '\n':
			return data[i+1:]

	# oops, didn't find anything offending
	return data
	

for filename in sys.argv[1:]:
	print "Checking %s" % filename
	try:
		id3 = ID3v2(filename, ID3V2_FILE_READ)

		for f in id3.frames:
			if f.fid[0] == 'T':
				print f.fid, f.fields
	except ID3Exception:
		print "Unable to find ID3v2 Tag"
		
		
	# check id3v1 tag
	try:
		id3v1 = ID3v1(filename)
		id3v1.parse()
		print id3v1.tag
	except AttributeError:
		print "Error parsing ID3v1 tag"

