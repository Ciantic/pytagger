#!/usr/bin/env python

from tagger import *

import sys, os, fnmatch, pickle

def print_debug(filename, msg):
    print os.path.basename(filename), ':',  msg

def do_id3(filename, verbose=1):
    try:
        id3 = ID3v2(filename)
        if not id3.tag_exists():
            print_debug(filename, "Unable to find ID3v2 tag")
        else:
            print_debug(filename, "Found ID3v2 tag ver: %.1f frames: %d" % \
                (id3.version, len(id3.frames)))

            if verbose:
                for frame in id3.frames:
                    try:
                        print_debug(filename, "%s (%s) %s" % \
                            (frame.fid, frame.encoding, str(frame.strings)))
                    except:
                        print_debug(filename, "%s - unprintable" % frame.fid)
    
            # commit changes to mp3 file (pretend mode)
            id3.commit(pretend=1)
        
    except ID3Exception, e:
        print_debug(filename, "ID3v2 exception: %s" % str(e))

    try:
        id3 = ID3v1(filename)
        if not id3.tag_exists():
            print_debug(filename, "Unable to find ID3v1 tag")
        else:
            print_debug(filename, "ID3v1 tag found")
            if verbose:
                print_debug(filename, "song: %s" % str(id3.songname))
                print_debug(filename, "artist: %s" % str(id3.artist))
    except ID3Exception, e:
        print_debug(filename, "ID3v1 exception: %s" % str(e))

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
