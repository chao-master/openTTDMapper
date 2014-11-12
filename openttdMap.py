#!/usr/bin/python

import struct,sys
import traceback

from PIL import Image

class OpenTTDFileParser():
    def __init__(self,filen):
        self.fileName = filen
        self.filePt = open(filen)
        self.header = None
        self.version = None
        self.chunks = []
        self._readHeaders()
        if self.header == 'OTTN':
            try:
                self._readAllChunks()
            except:
                traceback.print_exc()
        else:
            print 'Unsupported save encryption'
            sys.exit()

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
            
if __name__ == "__main__":
    f = OpenTTDFileParser(sys.argv[1])


    cols = [
        (64,255,64),    #Clear
        (64,64,64),     #Railway
        (16,16,16),     #Road
        (8,8,8),        #House
        (0,180,180),    #Tree
        (32,32,32),     #Station
        (0,0,128),      #Water
        (255,0,255),    #Void
        (8,8,8),        #Industry
        (255,127,0),    #Tunnel
        (180,180,180)   #Object
    ]

    w,h=f.size
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.tileMap[x][y]
            pix[x,y] = cols[t]
            #print x,y,t,cols[t]
    img.resize((w*10,h*10)).save("ottdmaptest.png")
    
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.mapO[x][y]
            pix[x,y] = (t,t,t)
    img.resize((w*10,h*10)).save("ottdmaptestO.png")
    
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            t = f.map5[x][y]
            pix[x,y] = (t,t,t)
    img.save("ottdmaptest5.png")
