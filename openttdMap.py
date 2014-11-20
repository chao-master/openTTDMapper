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
    def __init__(self,tHeight,gameMap):
        self.height = tHeight
        self.gameMap = gameMap
        self.owner = None
        
    @staticmethod
    def ofType(tType,tHeight,mapRef):
        if tType == 0:
            return ClearTile(tHeight,mapRef)
        elif tType == 1:
            return RailTile(tHeight,mapRef)
        elif tType == 2:
            return RoadTile(tHeight,mapRef)
        elif tType == 3:
            return HouseTile(tHeight,mapRef)
        elif tType == 4:
            return TreeTile(tHeight,mapRef)
        elif tType == 5:
            return StationTile(tHeight,mapRef)
        elif tType == 6:
            return WaterTile(tHeight,mapRef)
        elif tType == 7:
            return VoidTile(tHeight,mapRef)
        elif tType == 8:
            return IndyTile(tHeight,mapRef)
        elif tType == 9:
            return TunnelTile(tHeight,mapRef)
        elif tType == 10:
            return ObjTile(tHeight,mapRef)
    
    def handle_MAPO(self,value):
        pass
    def handle_MAP2(self,value):
        pass
    
    def colourWithHeight(self):
        return tuple(x+self.height*20 for x in self.colour)

    def getIndyColour(self):
        return tuple(x+self.height*20 for x in ClearTile.colour)

class TileWithOwner(Tile):
    def handle_MAPO(self,value):
        self.owner = value & 0b11111 #Only the lower 5 bytes seem to be used
	#XXX compay_type.h enum owner seems to have this data

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
    def getIndyColour(self):
        return tuple(x+self.height*20 for x in self.colour)

class VoidTile(Tile):
    colour = (0xFF,0x00,0xFF)

class IndyTile(Tile):
    colour = (0x79,0x00,0x11)
    def handle_MAP2(self,value):
        self.indyRef = value

    def getIndyColour(self):
        try:
            return Industry.colours[self.gameMap.industries[self.indyRef].type]
        except KeyError as e:
            #print e
            return (255,127,0)
        except IndexError as e:
            #print e
            return (0,0,0)

class TunnelTile(Tile):
    colour = (0xFF,0x77,0x00)

class ObjTile(Tile):
    colour = (0x77,0x77,0x77)

class Industry(object):
    colours = {
        0x0c: (0xfc,0xfc,0xfc), #Bank
        0x00: (0x10,0x10,0x10), #Coal Mine
        0x06: (0xa8,0x88,0xe0), #Factory
        0x03: (0x68,0x94,0x1c), #Forest
        0x12: (0x74,0x58,0x1c), #IronMine
        0x04: (0xfc,0xfc,0x00), #Oil Refinary
        0x01: (0xfc,0x00,0x00), #Power Plant
        0x05: (0x80,0xc4,0xfc), #Oil Well
        0x0b: (0x80,0xc4,0xfc), #Oil Rig
        0x09: (0xec,0x9c,0xa4), #Farm
        0x02: (0xfc,0x9c,0x00), #Sawmill
        0x08: (0xa8,0xa8,0xa8), #Steel Mill
    }
    def __init__(self,infoString):
        self.type = ord(infoString[43])
        #There is a lot of other infomation in here but right now we just want the type.

class Player(object):
    #TODO More Parsing
    def __init__(self,infoString):
        sl1 = ord(infoString[6])
        sl2 = ord(infoString[13+sl1])
        start = 14+sl1+sl2
        
        self.name = infoString[7:7+sl1]
        self.pName = infoString[14+sl1:start]
        
        self.face = infoString[start:start+4]
        self.money = struct.unpack(">q",infoString[start+4:start+12])
        self.loan = struct.unpack(">q",infoString[start+12:start+20])
        self.colour = ord(infoString[start+20:start+21]) #Needs compared to lookup table
        self.mFrac = infoString[start+21:start+22]
    
        

class OpenTTDFileParser(object):
    def __init__(self,filen):
        self.fileName = filen
        self.filePt = open(filen)
        self.header = None
        self.version = None
        self.chunks = []
        self.mapTiles = []
        self.industries = []
        
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

    #Map size infomation
    def _parse_MAPS(self,block,payload):
        self.size = struct.unpack(">II",payload)
        print "Map Size:", self.size
    
    #Tile type & Height map 
    def _parse_MAPT(self,block,payload):
        width,height = self.size
        x,y = 0,0
        
        self.mapTiles = [[None for j in xrange(height)] for i in xrange(width)]
        
        for c in payload:
            n = ord(c)
            tileHeight = n & 0xF
            tileType = n >> 4
            self.mapTiles[x][y] = Tile.ofType(tileType,tileHeight,self)
            x += 1
            if x == width:
                x=0
                y+=1
    
    #Tile Ownership infomation
    def _parse_MAPO(self,block,payload):
        width,height = self.size
        x,y = 0,0
        for c in payload:
            self.mapTiles[x][y].handle_MAPO(ord(c))
            x += 1
            if x == width:
                x=0
                y+=1
    
    #Industry Type infomation (proably other things too)
    def _parse_MAP2(self,block,payload):
        width,height = self.size
        i = 0
        for i in xrange(width*height):
            c,x,y = payload[i*2:i*2+2],i%width,i/width
            self.mapTiles[x][y].handle_MAP2(struct.unpack(">H",c)[0])

    def _parse_INDY(self,block,payload):
        for infoString in payload:
            if infoString:
                self.industries.append(Industry(infoString))
    
    def _parse_PLYR(self,block,payload):
        self.players = [Player(p) for p in payload

if __name__ == "__main__":
    f = OpenTTDFileParser(sys.argv[1])

    def getCol(n):
        if not n in colStore:
            i = len(colStore)
            colStore[n] = tuple([ int(z*255) for z in colorsys.hsv_to_rgb((0.618033988749895 * i) % 1,0.8,0.8)])
            pixOwner[n%32,h+2+(n/32)] = colStore[n]
        return colStore[n]
    
    colStore = {0x10:(255,255,255),0x11:(255,255,255)} #Both 0x10 and 0x11 seem to refer to unown land, the later being unowned water
    w,h=f.size
    imgTiles = Image.new("RGB",(h,w))
    imgOwner = Image.new("RGB",(h,w+10))
    imgIndy  = Image.new("RGB",(h,w))
    pixTiles = imgTiles.load()
    pixOwner = imgOwner.load()
    pixIndy  = imgIndy.load()
    c=0
    for x in xrange(w):
        for y in xrange(h):
            pixTiles[y,x] = f.mapTiles[x][y].colourWithHeight()
            owner = f.mapTiles[x][y].owner
            if not owner is None:
                pixOwner[y,x] = getCol(owner)
            pixIndy[y,x] = f.mapTiles[x][y].getIndyColour()
            if isinstance(f.mapTiles[x][y],IndyTile):
                c+=1
    imgTiles.save("ottdTiles.png") 
    imgOwner.save("ottdOwnership.png")
    imgIndy.save("ottdIndy.png")
