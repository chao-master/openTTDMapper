import struct,sys
import traceback
import lzma
import StringIO
import colorsys

from openttdMap import *

itr = open("indyTypeRaw","w") #DEBUG

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
    
    def getOwnerColour(self):
        return (0x45,0x71,0x0e) #TODO get colour


class TileWithOwner(Tile):
    def handle_MAPO(self,value):
        self.owner = value & 0b11111 #Only the lower 5 bytes seem to be used
	#XXX compay_type.h enum owner seems to have this data
    
    def getOwnerColour(self):
        if self.owner == 0x0F: #TOWN
            return (0x79,0x00,0x11)
        elif self.owner == 0x10 or self.owner is None: #None - Ground
            return (0x45,0x71,0x0e)
        elif self.owner == 0x11: #None - Water
            return (0x3c,0x59,0xa2)
        elif self.owner == 0x12: #Script/Superuser
            return (255,0,255) #TODO get colour
        else:
            return self.gameMap.players[self.owner].getColour()


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
        itr.write("{:03} ".format(value))

    def getIndyColour(self): #TODO Fix this, the issue is mostly with the industy lookup though...
        try:
            return Industry.colours[self.gameMap.industries[self.indyRef].type]
        except KeyError as e:
            print e
            return (255,127,0)
        except IndexError as e:
            print e
            return (0,0,0)

    def getOwnerColour(self):
        return (0x62,0x65,0x62)

class TunnelTile(Tile):
    colour = (0xFF,0x77,0x00)

class ObjTile(Tile):
    colour = (0x77,0x77,0x77)
