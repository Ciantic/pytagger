#!/usr/bin/env python

import sys
assert sys.version >= '2.3', "Requires Python v2.3 or above"
from distutils.core import setup, Extension

setup(
    name = "pyid3v2",
    version = "0.1",
    author = "Alastair Tse",
    author_email = "acnt2@cam.ac.uk",
    url = "http://www-lce.eng.cam.ac.uk/~acnt2/code/pyid3v2/",
	description = "Python ID3 Tag Reader and Writer",
	long_description = "An ID3v1 and ID3v2 tag reader and writer in pure Python. Supports all standards including ID3v1, ID3v1.1, ID3v2.2, ID3v2.3 and ID3v2.4",
    license = "BSD",
	py_modules = ["pyid3v2"],
    scripts = ["mp3conv.py", "mp3stats.py", "mp3check.py"]
)
