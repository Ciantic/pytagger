"""
Copyright (c) 2004. Alastair Tse <acnt2@cam.ac.uk>
http://www-lce.eng.cam.ac.uk/~acnt2/code/pytagger/

Encoding maps
"""

__revision__ = "$Id: encoding.py,v 1.3 2004/05/09 23:25:40 acnt2 Exp $"

ID3V2_FIELD_ENC_LATIN_1 = 0
ID3V2_FIELD_ENC_UTF16 = 1
ID3V2_FIELD_ENC_UTF16BE = 2
ID3V2_FIELD_ENC_UTF8 = 3

encodings = {'latin_1':ID3V2_FIELD_ENC_LATIN_1,
			 'utf_16':ID3V2_FIELD_ENC_UTF16,
			 'utf_16_be':ID3V2_FIELD_ENC_UTF16BE,
			 'utf_8':ID3V2_FIELD_ENC_UTF8,
			 ID3V2_FIELD_ENC_LATIN_1:'latin_1',
			 ID3V2_FIELD_ENC_UTF16:'utf_16',
			 ID3V2_FIELD_ENC_UTF16BE:'utf_16_be',
			 ID3V2_FIELD_ENC_UTF8:'utf_8'}



ID3V2_DOUBLE_BYTE_ENCODINGS = ["utf_16", "utf_16_be"]
ID3V2_SINGLE_BYTE_ENCODINGS = ["latin_1", "utf_8"]
ID3V2_VALID_ENCODINGS = ["latin_1", "utf_16", "utf_16_be", "utf_8"]
