"""
Copyright (c) 2004. Alastair Tse <acnt2@cam.ac.uk>
http://www-lce.eng.cam.ac.uk/~acnt2/code/pytagger/

Debugging Functions
"""

__revision__ = "$Id: debug.py,v 1.2 2004/05/04 12:18:21 acnt2 Exp $"

ID3V2_DEBUG = 0

def debug(args):
	if ID3V2_DEBUG > 1: print args
def warn(args):
	if ID3V2_DEBUG > 0: print args
def error(args):
	print args
