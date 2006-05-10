from tagger import *
import sys, os, fnmatch, pickle

def get_apic(filename):
    id3 = ID3v2(filename)
    if not id3.tag_exists():
        return "No ID3 Tag Found"
        
    apicfid = 'APIC'
    if id3.version == 2.2:
        apicfid = 'PIC'
    
    try:
        apicframe = [frame for frame in id3.frames if frame.fid == apicfid][0]
    except IndexError:
        return "No APIC frame found"
        
    print "APIC: encoding: %s type: %d" % (apicframe.encoding, apicframe.picttype)
    open('test.png', 'w').write(apicframe.pict)
    
def set_apic(filename):
    id3 = ID3v2(filename)
    
    apicfid = 'APIC'
    if id3.version == 2.2:
        apicfid = 'PIC'
    
    apic = id3.new_frame(fid = apicfid)
    
    apic.encoding = 'latin_1'
    apic.mimetype = 'image/png'
    apic.picttype = 0
    apic.desc = ''
    apic.pict = open('liquidx.png').read()
    
    # replace apic frame
    id3.frames = [frame for frame in id3.frames if frame.fid != apicfid]
    id3.frames.append(apic)
    id3.commit()
    
if __name__ == "__main__":
    print set_apic(sys.argv[1])