#!/usr/bin/env python

import sys
assert sys.version >= '2.3', "Requires Python v2.3 or above"
from distutils.core import setup, Extension

setup(
    name = "pytagger",
    version = "0.5",
    author = "Alastair Tse",
    author_email = "alastair@liquidx.net",
    url = "http://www.liquidx.net/pytagger/",
	description = "Python ID3 Tag Reader and Writer Module",
	long_description = "An ID3v1 and ID3v2 tag reader and writer module in pure Python. Supports all standards including ID3v1, ID3v1.1, ID3v2.2, ID3v2.3 and ID3v2.4",
	license = "BSD",
	py_modules = ["tagger", "tagger.id3v1", "tagger.id3v2", "tagger.exceptions",
				  "tagger.constants", "tagger.utility", "tagger.id3v2frame",
				  "tagger.encoding", "tagger.debug"],
    scripts = ["mp3check.py", "apic.py"]
)
