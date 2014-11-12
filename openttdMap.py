#!/usr/bin/python

import struct,sys
import traceback
import lzma
import StringIO
import colorsys

from PIL import Image

class UnRecognisedFormat(Exception):
    def __init__(self,magicNumber,majorVersion,minorVersion):
        self.magicNumber = magicNumber
        self.majorVersion = majorVersion
        self.minorVersion = minorVersion
    
    def __repr__(self):
        return "Un-recognised save format: {},{},{}".format(magicNumber,majorVersion,minorVersion)

class Tile(object):
    def __init__(self,tHeight):
        self.height = tHeight
        self.owner = None
        
    @staticmethod
    def ofType(tType,tHeight):
        if tType == 0:
            return ClearTile(tHeight)
        elif tType == 1:
            return RailTile(tHeight)
        elif tType == 2:
            return RoadTile(tHeight)
        elif tType == 3:
            return HouseTile(tHeight)
        elif tType == 4:
            return TreeTile(tHeight)
        elif tType == 5:
            return StationTile(tHeight)
        elif tType == 6:
            return WaterTile(tHeight)
        elif tType == 7:
            return VoidTile(tHeight)
        elif tType == 8:
            return IndyTile(tHeight)
        elif tType == 9:
            return TunnelTile(tHeight)
        elif tType == 10:
            return ObjTile(tHeight)
    
    def handle_MAPO(self,value):
        pass
    
    def colourWithHeight(self):
        return tuple(x+self.height*20 for x in self.colour)

class TileWithOwner(Tile):
    def handle_MAPO(self,value):
        self.owner = value

class ClearTile(TileWithOwner):
    colour = (0x3b,0x4d,0x27)

class RailTile(TileWithOwner):
    colour = (0xa8,0xa8,0xa8)

class RoadTile(TileWithOwner):
    colour = (0x17,0x17,0x17)

class HouseTile(Tile):
    colour = (0xfc,0xfc,0xfc)

class TreeTile(TileWithOwner):
    colour = (0x80,0xa9,0x2d)

class StationTile(TileWithOwner):
    colour = (0xef,0x00,0x23)

class WaterTile(TileWithOwner):
    colour = (0x3c,0x59,0xa2)

class VoidTile(Tile):
    colour = (0xFF,0x00,0xFF)

class IndyTile(Tile):
    colour = (0x79,0x00,0x11)

class TunnelTile(Tile):
    colour = (0xFF,0x77,0x00)

class ObjTile(Tile):
    colour = (0x77,0x77,0x77)


class OpenTTDFileParser(object):
    def __init__(self,filen):
        self.fileName = filen
        self.filePt = open(filen)
        self.header = None
        self.version = None
        self.chunks = []
        self.mapTiles = []
        
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
        
    
    #Tile type & Height map 
    def _parse_MAPT(self,block,payload):
        width,height = self.size
        x,y = 0,0
        
        self.mapTiles = [[None for j in xrange(width)] for i in xrange(height)]
        
        for c in payload:
            n = ord(c)
            tileHeight = n & 0xF
            tileType = n >> 4
            self.mapTiles[y][x] = Tile.ofType(tileType,tileHeight)
            x += 1
            if x == width:
                x=0
                y+=1
        
    def _parse_MAPO(self,block,payload):
        width,height = self.size
        x,y = 0,0
        for c in payload:
            self.mapTiles[y][x].handle_MAPO(ord(c))
            x += 1
            if x == width:
                x=0
                y+=1
    
if __name__ == "__main__":
    f = OpenTTDFileParser(sys.argv[1])

    def getCol(n):
        if not n in colStore:
            i = len(colStore)
            colStore[n] = tuple([ int(z*255) for z in colorsys.hsv_to_rgb((0.618033988749895 * i) % 1,1,1)])
            pix[n%32,h+2+(n/32)] = colStore[n]
        return colStore[n]
    
    colStore = {0x10:(255,255,255)}
    w,h=f.size
    img = Image.new("RGB",(w,h))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            pix[x,y] = f.mapTiles[x][y].colourWithHeight()
    img.save("ottdTiles.png")
    

    img = Image.new("RGB",(w,h+10))
    pix = img.load()
    for x in xrange(w):
        for y in xrange(h):
            owner = f.mapTiles[x][y].owner
            if not owner is None:
                pix[x,y] = getCol(owner)
    img.save("ottdOwnership.png")
