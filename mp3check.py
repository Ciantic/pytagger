#!/usr/bin/env python

from tagger import *

import sys, os, fnmatch, pickle

#headers_id3v2 = []
has_footer = 0

def do_id3(filename, verbose=1):
	try:
		id3 = ID3v2(filename)
		#headers_id3v2.append((filename, id3.dump_header()))
		print "ID3v2: %s: ver: %f frames: %d length: %d" % \
			  (os.path.basename(filename),
			   id3.version, len(id3.frames), id3.tag["size"])
		if verbose:
			for frame in id3.frames:
				try:
					print frame.fid, ":", frame.encoding, ":"
				except:
					print frame.fid, ":"

		if id3.tag.has_key("footer") and id3.tag["footer"]: has_footer+=1
		id3.commit(pretend=1)
	except ID3Exception, e:
		print "Error: ID3v2: %s: %s" % (os.path.basename(filename), e)

	try:
		id3 = ID3v1(filename)
	except ID3Exception, e:
		print "Error: ID3v1: %s: %s" % (os.path.basename(filename), e)


def do_recurse(filename):
	if os.path.isdir(filename):
		#print "traversing dir:", filename
		for f in fnmatch.filter(os.listdir(filename), '*.mp3'):
			do_recurse(os.path.join(filename, f))
		for f in os.listdir(filename):
			if os.path.isdir(os.path.join(filename, f)):
				do_recurse(os.path.join(filename, f))
	else:
		#print "checking file:", filename
		do_id3(filename)

try:
	do_recurse(sys.argv[1])
finally:
	pass
	#pickle.dump(headers_id3v2, open("headers_id3v2.pkl", "w"))

print has_footer
