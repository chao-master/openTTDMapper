#!/usr/bin/python

import struct,sys
import traceback
import lzma
import StringIO

from PIL import Image

class UnRecognisedFormat(Exception):
    def __init__(self,magicNumber,majorVersion,minorVersion):
        self.magicNumber = magicNumber
        self.majorVersion = majorVersion
        self.minorVersion = minorVersion
    
    def __repr__(self):
        return "Un-recognised save format: {},{},{}".format(magicNumber,majorVersion,minorVersion)

class OpenTTDFileParser(object):
    def __init__(self,filen):
        self.fileName = filen
        self.filePt = open(filen)
        self.header = None
        self.version = None
        self.chunks = []
        self._readHeaders()
        if self.header == 'OTTN':
            pass
        elif self.header == 'OTTX':
            self.filePt = StringIO.StringIO(lzma.decompress(self.filePt.read()))
        else:
            raise UnRecognisedFormat(self.header,self.version[0],self.version[1])
        self._readAllChunks()

    def _readHeaders(self):
        self.header = self.filePt.read(4)
        self.version = struct.unpack(">HH",self.filePt.read(4))
    
    def _readByte(self):
        n = struct.unpack(">B",self.filePt.read(1))[0]
        return n
    
    def _readGamma(self):
        i = self._readByte()
        if (i >> 7) & 1:
            i &= ~0x80
            if (i >> 6) & 1:
                i &= ~0x40
                if (i >> 5) & 1:
                    i &= ~0x20
                    if (i >> 4) & 1:
                        i &= ~0x10
                        if (i >> 3) & 1:
                            assert False
                        i = self._readByte()
                    i = (i << 8) | self._readByte()
                i = (i << 8) | self._readByte()
            i = (i << 8) | self._readByte()
        return i
    
    def _readSparseChunk(self):
        length = self._readGamma()
        parts = []
        while length != 0:
            payload = self.filePt.read(length-1)
            parts.append(payload)
            length = self._readGamma()
        return parts
    
    def _readAllChunks(self):
        cTyp = self.filePt.read(4)
        
        while cTyp != "\x00\x00\x00\x00":
            cMod = self.filePt.read(1)
            if cMod == '\x02' or cMod == '\x01':
                payload = self._readSparseChunk()               
            else:
                rl = self.filePt.read(3)
                length = struct.unpack(">I",cMod+rl)[0]
                payload = self.filePt.read(length)
            getattr(self,"_parse_"+cTyp,self._noparse)(cTyp,payload)
            cTyp = self.filePt.read(4)

    def _noparse(self,block,payload):
        print "unhandled chunk",block,
        if isinstance(payload,str) or len(payload) == 0:
            print len(payload)
        else:
            print len(payload),"of",len(payload[0])
        self.chunks.append((block,payload,))

    def _parse_MAPS(self,block,payload):
        self.size = struct.unpack(">II",payload)
        print "SIZE",self.size
    
    #Tile type & Height map 
    def _parse_MAPT(self,block,payload):
        width,height = self.size
        x,y = 0,0
        self.heightMap = [[-1 for j in xrange(height)] for i in xrange(width)]
        self.tileMap = [[-1 for j in xrange(height)] for i in xrange(width)]
        for c in payload:
            n = ord(c)
            h = n & 0xF
            t = n >> 4
            self.heightMap[y][x] = h
            self.tileMap[y][x] = t
            x += 1
            if x == width:
                x=0
                y+=1
        
    def _parse_MAPO(self,block,payload):
        width,height = self.size
        x,y = 0,0
        self.mapO = [[-1 for j in xrange(height)] for i in xrange(width)]
        for c in payload:
            n = ord(c)
            self.mapO[y][x] = n
            x += 1
            if x == width:
                x=0
                y+=1

    """ Dosent work as Map2 has 16 bits per tile.
    def _parse_MAP2(self,block,payload):
        width,height = self.size
        x,y = 0,0
        self.map2 = [[-1 for j in xrange(height)] for i in xrange(width)]
        for c in payload:
            n = ord(c)
            self.map2[y][x] = n
            x += 1
            if x == width:
                x=0
                y+=1
    """
    
    def _parse_MAP5(self,block,payload):
        width,height = self.size
        x,y = 0,0
        self.map5 = [[-1 for j in xrange(height)] for i in xrange(width)]
        for c in payload:
            n = ord(c)
            self.map5[y][x] = n
            x += 1
            if x == width:
                x=0
                y+=1
    
    def _parse_M3LO(self,block,payload):
        width,height = self.size
        x,y = 0,0
        self.m3lo = [[-1 for j in xrange(height)] for i in xrange(width)]
        for c in payload:
            n = ord(c)
            self.m3lo[y][x] = n
            x += 1
            if x == width:
                x=0
                y+=1
    
    def _parse_M3HI(self,block,payload):
        width,height = self.size
        x,y = 0,0
        self.m3hi = [[-1 for j in xrange(height)] for i in xrange(width)]
        for c in payload:
            n = ord(c)
            self.m3hi[y][x] = n
            x += 1
            if x == width:
                x=0
                y+=1

    def _parse_MAPE(self,block,payload):
        width,height = self.size
        x,y = 0,0
        self.mapE = [[-1 for j in xrange(height)] for i in xrange(width)]
        for c in payload:
            n = ord(c)
            self.mapE[y][x] = n
            x += 1
            if x == width:
                x=0
                y+=1
                
    def _parse_MAP7(self,block,payload):
        width,height = self.size
        x,y = 0,0
        self.map7 = [[-1 for j in xrange(height)] for i in xrange(width)]
        for c in payload:
            n = ord(c)
            self.map7[y][x] = n
            x += 1
            if x == width:
                x=0
                y+=1
            
if __name__ == "__main__":
    f = OpenTTDFileParser(sys.argv[1])

    cols = [
        (0x3b,0x4d,0x27),     #Clear
        (0xa8,0xa8,0xa8),     #Railway
        (0x17,0x17,0x17),     #Road
        (0xfc,0xfc,0xfc),     #House
        (0x80,0xa9,0x2d),    #Tree
        (0xef,0x00,0x23),     #Station
        (0x3c,0x59,0xa2),      #Water
        (0xFF,0x00,0xFF),     #Void
        (0x79,0x00,0x11),     #Industry
        (0xFF,0x77,0x00),     #Tunnel
        (0x77,0x77,0x77)   #Object
    ]

    w,h=f.size
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.tileMap[x][y]
            pix[x,y] = cols[t]
            #print x,y,t,cols[t]
    img.save("ottdmaptest.png")
    
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.mapO[x][y]
            pix[x,y] = (t,t,t)
    img.save("ottdmaptestO.png")
    
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.map5[x][y]
            pix[x,y] = (t,t,t)
    img.save("ottdmaptest5.png")
    
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.m3lo[x][y]
            pix[x,y] = (t,t,t)
    img.save("ottdmaptest3lo.png")
    
    mg = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.m3hi[x][y]
            pix[x,y] = (t,t,t)
    img.save("ottdmaptest3hi.png")
    
    mg = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.mapE[x][y]
            pix[x,y] = (t,t,t)
    img.save("ottdmaptestE.png")
    
    mg = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.map7[x][y]
            pix[x,y] = (t,t,t)
    img.save("ottdmaptest7.png")
    
    """
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.map2[x][y]
            pix[x,y] = (t,t,t)
    img.save("ottdmaptest2.png")
    """
