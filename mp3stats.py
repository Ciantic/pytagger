#!C:\Python23\python.exe

from pyid3v2 import *

import sys, string, os, pickle, fnmatch

def strip_newline(data):
	# find new line and strip everything before it
	for i in range(0,len(data)):
		if data[i] == '\n':
			return data[i+1:]

	# oops, didn't find anything offending
	return data
	

versions = {0x0200:[], 0x0300:[], 0x0400:[], "unknown":[]}
frames = {}
errors = []

def do_id3(filename):
	try:
		id3 = ID3v2(filename, ID3V2_FILE_READ)
		if versions.has_key(id3.tag["version"]):
			versions[id3.tag["version"]].append(filename)
		else:
			versions["unknown"].append(filename)
			
		for f in id3.frames:
			if frames.has_key(f.fid):
				frames[f.fid].append(filename)
			else:
				frames[f.fid] = [filename]
			
	except ID3Exception:
		print "Unable to find ID3v2 Tag"
		errors.append((filename,"unable to find id3v2 tag"))	

def do_recurse(filename):
	if os.path.isdir(filename):
		print "traversing dir:", filename
		for f in fnmatch.filter(os.listdir(filename), '*.mp3'):
			do_recurse(os.path.join(filename, f))
	else:
		print "checking file:", filename
		do_id3(filename)

for filename in sys.argv[1:]:
	do_recurse(filename)
	

# dump stats:
#pickle.dump(versions,open("stats.versions",'wb'))
#pickle.dump(frames,open("stats.frames",'wb'))
#pickle.dump(errors,open("stats.errors",'wb'))

print "Version Distributions:"
for k,v in versions.items():
	print k, len(v)
print "Frames Used:"
for k,v in frames.items():
	print k, len(v)
print "Errors:"
for e in errors:
	print e[0], ":", e[1]
		
