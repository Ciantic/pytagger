#!/usr/bin/env python

from tagger import *
from optparse import OptionParser

import sys, os, string

CONV_FIELDS_2_3 = ['TIT2','TPE1','TALB']
CONV_FIELDS_2_2 = ['TT2', 'TP1', 'TAL']

def usage():
    print "usage: mp3tagconv.py -f <from encoding> -t <to encoding> [-v tagver] <file(s)/directory>"

def main(args):
    global CONV_FIELDS_2_3, CONV_FIELDS_2_2
    
    parser = OptionParser()

    
    
if __name__ == "__main__":
    main(sys.args)


