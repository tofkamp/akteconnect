# akteconnect - Connect aktes from allefriezen BS dump at https://opendata.picturae.com/
#
#   Copyright (C) 2016 T.Hofkamp
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pygame, sys
from pygame.locals import *

import json
import sqlite3
import os

from Tkinter import Tk
from tkFileDialog import askopenfilename

import data.akte

# kleuren
# json load/save (to http?)
# documentatie
# overzicht scherm rechts onder
# delete verbinding dmv middelste muis ?

# select akte server
# oplossing sturen naar server

#http://www.w3schools.com/tags/ref_colornames.asp
BLACK  = (  0,   0,   0)
DARK   = (120, 120, 120)
LATE   = (170, 170, 170)
NOTICE = (255,   0, 255)
NORMAL = (150, 150, 150)
WHITE  = (200, 200, 200)
SHINY  = (255, 255, 255)
BLUE   = (  0,   0, 255)
MAGENTA= (128,   0, 128)
LIME   = (  0, 255,   0)
BRIGHTRED    = (255,   0,   0)
RED          = (155,   0,   0)
BRIGHTGREEN  = (  0, 255,   0)
GREEN        = (  0, 155,   0)
BRIGHTBLUE   = (  0,   0, 255)
BLUE         = (  0,   0, 155)
BRIGHTYELLOW = (255, 255,   0)
YELLOW       = (155, 155,   0)
DARKGRAY     = ( 40,  40,  40)

pygame.init()

#DISPLAYSURF = pygame.display.set_mode((950,608),pygame.RESIZABLE)

FPS = 10 # frames per second setting
fpsClock = pygame.time.Clock()

# colour of canvas
BACKGROUNDCOLOUR = WHITE

# colour and size of fonts of akte-box
#HEADERFONTSIZE = 16
HEADERFONTSIZE = 20
#HEADERFONT = pygame.font.Font('freesansbold.ttf', HEADERFONTSIZE)
HEADERFONT = pygame.font.SysFont('Tahoma Bold', HEADERFONTSIZE)
HEADERFONTCOLOUR = WHITE
TEXTFONTSIZE = 12
#TEXTFONT = pygame.font.Font('freesansbold.ttf', TEXTFONTSIZE)
TEXTFONT = pygame.font.SysFont('Tahoma', TEXTFONTSIZE)
TEXTFONTCOLOUR = WHITE
BOXCOLOUR = WHITE
GEBOORTECOLOUR = GREEN
OVERLIJDENCOLOUR = RED
HUWELIJKCOLOUR = BLUE

# the number of connects to go in the right top corner
CONNECTCOUNTFONTSIZE = 30
CONNECTCOUNTFONT = pygame.font.Font('freesansbold.ttf', CONNECTCOUNTFONTSIZE)
CONNECTCOUNTFONTCOLOUR = BLACK
# colour to show when hovering above other box in order to connect
CONNECTOKCOLOUR = BRIGHTGREEN
CONNECTNOTOKCOLOUR = BRIGHTRED

# colour of the lines between the boxes
LINEOKCOLOUR = BLACK
LINENOTOKCOLOUR = RED
LINETHICKNESS = 3

# colour of the connector on the boxes
CONNECTFROMCOLOUR = LIME
CONNECTTOCOLOUR = MAGENTA
CONNECTRADIUS = 8

# also text of type of akte in header
LONGHEADER = False

#print pygame.font.get_default_font()
#print pygame.font.get_fonts()

#pygame.display.set_caption('Feenstra - Vries')
#print(pygame.display.Info())
#print(pygame.display.get_wm_info())

class AkteSprite:
    def __init__(self,akteid = None):
        self.image = None
        self.rect = None
        self.hidden = False
        self.allow_connect_to = False
        self.allow_connect_from = False
        self.allow_connect_from2 = False
        self.aktestring = None
        self.akteid = akteid
        self.eventdate = None
        self.eventtype = None
        self.highlight = None           # show akte with this color highlithed
        self.connectedto = None
        self.connectedto2 = None        # bruid connection
        self.linecolour = WHITE
        self.linecolour2 = WHITE
        self.middleline = 0             # x pos of line between boxes, if eventtype = "Huwelijk"

    def init(self,akteid,aktestring,allow_connect_to = True,allow_connect_from = True,lastnamebruidegom = None,lastnamebruid = None):
        # if allow_connect_from is true, also lastname bruidegom&bruid must be equal
        # pak akte uit
        #akte = cag.akte....from_string(aktestring)
        #self.akteid = akte.akte_id
        
        self.hidden = False      # if true, do not draw anything (not used)
        self.aktestring = aktestring    # the string from which te akte can be extracted
        self.akteid = akteid     # the id of the akte
        akte = data.akte.akte(self.akteid)
        akte.load_from_string(self.aktestring,self.akteid)
        self.eventtype = akte.eventtype
        self.eventdate = akte.eventdate
        self.allow_connect_to = allow_connect_to
        self.allow_connect_from = allow_connect_from
        self.allow_connect_from2 = False
        if allow_connect_from:
            if akte.eventtype == "Huwelijk":
                self.allow_connect_from = False
                vader = akte.find_person_with_role("Vadervandebruidegom")
                moeder = akte.find_person_with_role("Moedervandebruidegom")
                if vader and moeder:
                    if vader.lastname.lower() == lastnamebruidegom.lower() and moeder.lastname.lower() == lastnamebruid.lower():
                        #print vader.lastname,lastnamebruidegom,moeder.lastname,lastnamebruid
                        self.allow_connect_from = True
                self.allow_connect_from2 = False
                vader = akte.find_person_with_role("Vadervandebruid")
                moeder = akte.find_person_with_role("Moedervandebruid")
                if vader and moeder:
                    if vader.lastname.lower() == lastnamebruidegom.lower() and moeder.lastname.lower() == lastnamebruid.lower():
                        #print vader.lastname,lastnamebruidegom,moeder.lastname,lastnamebruid,2
                        self.allow_connect_from2 = True
        self.generate_image()

    def generate_image(self):
        # generate the sprite image of the akte
        # akte string has to be converted to "to_string"
        def multiline_string_to_surface(font,multilinestring,antialias, colour, bgcolour):
            lines = multilinestring.split('\n')
            surfaces = []
            width = 0
            height = 0
            for line in lines:
                surface = font.render(line, antialias, colour, bgcolour)
                height += font.get_linesize()
                width = max(width, surface.get_width())
                surfaces.append(surface)
            ret = pygame.Surface((width, height))
            ret.fill(bgcolour)
            ypos = 0
            for surface in surfaces:
                ret.blit(surface,(0, ypos))
                ypos += font.get_linesize()
            return ret
        
        akte = data.akte.akte(self.akteid)
        akte.load_from_string(self.aktestring,self.akteid)
        self.eventtype = akte.eventtype
        self.evendate = akte.eventdate
        bgcolour = None
        if self.eventtype == "Geboorte":
            bgcolour = GEBOORTECOLOUR
        if self.eventtype == "Overlijden":
            bgcolour = OVERLIJDENCOLOUR
        if self.eventtype == "Huwelijk":
            bgcolour = HUWELIJKCOLOUR
        aktestring = akte.to_string(longversion = LONGHEADER)
        header = HEADERFONT.render(aktestring[0], True, HEADERFONTCOLOUR, bgcolour)
        text = multiline_string_to_surface(TEXTFONT, aktestring[1], True, TEXTFONTCOLOUR, bgcolour)
        if len(aktestring) == 3:    # if it is a marriage, two text fields are provided
            text2 = multiline_string_to_surface(TEXTFONT, aktestring[2], True, TEXTFONTCOLOUR, bgcolour)
            width = max(header.get_width(),text.get_width(), text2.get_width()) + 9
            height = header.get_height() + max(text.get_height(), text2.get_height()) + 9
        else:
            width = max(header.get_width(),text.get_width()) + 6
            height = header.get_height() + text.get_height() + 9
        # create the empty sprite
        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect()
        self.image.fill(bgcolour)
        self.image.blit(header,((width - header.get_width())/2,3))  ## centreer header
        self.image.blit(text,(3, header.get_height() + 6))
        pygame.draw.rect(self.image, BOXCOLOUR, (1,1,width - 2,height - 2),1)   # box around image
        pygame.draw.line(self.image, BOXCOLOUR, (1,header.get_height() + 4),(width - 2,header.get_height() + 4),1)  # line between header and text
        if len(aktestring) == 3:
            # verdeel de ruimte die over is tussen de twee boxen
            space = (width - text.get_width() - text2.get_width() - 9) / 2
            self.middleline = text.get_width() + 4 + space
            pygame.draw.line(self.image, BOXCOLOUR, (self.middleline,header.get_height() + 4),(self.middleline, height - 2),1)  # line between text (left) and text1 (right)
            self.image.blit(text2,(text.get_width() + 6 + space, header.get_height() + 6))
            if self.allow_connect_from:
                #pygame.draw.rect(self.image, CONNECTFROMCOLOUR,(0,0,2,2),0)
                pygame.draw.circle(self.image, CONNECTFROMCOLOUR,self.rect.topleft, CONNECTRADIUS,0)
                #pygame.draw.rect(self.image, CONNECTFROMCOLOUR,(width - 3,0,3,3),0)
            if self.allow_connect_from2:
                pygame.draw.circle(self.image, CONNECTFROMCOLOUR,self.rect.topright, CONNECTRADIUS,0)
        else:
            if self.allow_connect_from:
                #pygame.draw.rect(self.image, CONNECTFROMCOLOUR,(width / 2 - 1,0,3,3),0)
                pygame.draw.circle(self.image, CONNECTFROMCOLOUR,self.rect.midtop, CONNECTRADIUS,0)
        if self.allow_connect_to:
            pygame.draw.circle(self.image, CONNECTTOCOLOUR,self.rect.midbottom, CONNECTRADIUS, 0)
    

    def update_line_colour(self,aktesprites):
        """ determine line colour for all connections from this akte
        LINENOTOKCOLOUR if source akte is older than destn akte
                        or aktes are from same type
        """
        if self.connectedto:
            if self.connectedto in aktesprites:
                if self.eventdate < aktesprites[self.connectedto].eventdate or self.eventtype == aktesprites[self.connectedto].eventtype:
                    self.linecolour = LINENOTOKCOLOUR
                else:
                    self.linecolour = LINEOKCOLOUR
        if self.connectedto2 and self.eventtype == "Huwelijk":
            if self.connectedto2 in aktesprites:
                #print self.connectedto2
                #print self.eventdate
                #print aktesprites[self.connectedto2].eventdate
                #print aktesprites[self.connectedto2].eventtype
                if self.eventdate < aktesprites[self.connectedto2].eventdate or self.eventtype == aktesprites[self.connectedto2].eventtype:
                    self.linecolour2 = LINENOTOKCOLOUR
                else:
                    self.linecolour2 = LINEOKCOLOUR
                    
    def draw_sprite(self,surface,viewport,hightlight_connect_from):
        """
        draw the generated sprite of the akte on the surface

        surface: the surface to draw on
        viewport: the portion the user is seeing
        todo: do nothing if outside viewport
        """
        if self.hidden:
            return
        if self.highlight:
            pygame.draw.rect(surface, self.highlight, self.rect.move(-viewport.x,-viewport.y))
        else:
            surface.blit(self.image,self.rect.move(-viewport.x,-viewport.y))
            if hightlight_connect_from and self.number_of_connection_to_make() > 0:
                pygame.draw.ellipse(surface, (255,255,255), self.rect.move(-viewport.x,-viewport.y),1)
            

    def draw_line(self,surface,viewport,aktesprites):
        """
        draw te lines on the canvas between the akten

        surface: the surface to draw to
        viewport: the portion the user is seeing
        aktesprites: dict of sprites, to draw to
        """
        if self.hidden:
            return
        src_rect = self.rect.move(-viewport.x, -viewport.y)
        if self.connectedto:
            if self.connectedto in aktesprites:
                dest_rect = aktesprites[self.connectedto].rect.move(-viewport.x, -viewport.y)
                if self.eventtype == "Geboorte" or self.eventtype == "Overlijden":
                     pygame.draw.line(surface, self.linecolour, src_rect.midtop ,dest_rect.midbottom, LINETHICKNESS)
                elif self.eventtype == "Huwelijk":
                    pygame.draw.line(surface, self.linecolour, src_rect.topleft ,dest_rect.midbottom, LINETHICKNESS)
        if self.connectedto2:
            if self.connectedto2 in aktesprites:
                dest_rect = aktesprites[self.connectedto2].rect.move(-viewport.x, -viewport.y)
                if self.eventtype == "Huwelijk":
                    pygame.draw.line(surface, self.linecolour2, src_rect.topright ,dest_rect.midbottom, LINETHICKNESS)
            
    def to_json_string(self):          # old, not used anymore
        return json.dumps({"pos" : self.rect.topleft,
                           #"akteid" : self.akteid,
                           "aktestring" : self.aktestring,
                           "connectedto" : self.connectedto,
                           "connectedto2" : self.connectedto2,
                           "allowconnectto" : self.allow_connect_to,
                           "allowconnectfrom2" : self.allow_connect_from2,
                           "allowconnectfrom" : self.allow_connect_from },separators=(',',':'),indent=4)
    def to_json_struct(self):
        return {"pos" : self.rect.topleft,
                           #"akteid" : self.akteid,
                           "aktestring" : self.aktestring,
                           "connectedto" : self.connectedto,
                           "connectedto2" : self.connectedto2,
                           "allowconnectto" : self.allow_connect_to,
                           "allowconnectfrom2" : self.allow_connect_from2,
                           "allowconnectfrom" : self.allow_connect_from }
    
    def from_json_dict(self,parsed_json):
        #parsed_json = json.loads(jsonstring)
        #self.akteid = parsed_json["akteid"]
        self.aktestring = parsed_json["aktestring"]
        self.connectedto = parsed_json["connectedto"]
        self.connectedto2 = parsed_json["connectedto2"]
        self.allow_connect_to = parsed_json["allowconnectto"]
        self.allow_connect_from = parsed_json["allowconnectfrom"]
        if "allowconnectfrom2" in parsed_json:
            self.allow_connect_from2 = parsed_json["allowconnectfrom2"]
        else:
            self.allow_connect_from2 = self.allow_connect_from
        self.generate_image()
        self.rect.topleft = parsed_json["pos"]

    def to_result(self):
        ret = []
        if self.eventtype == "Huwelijk":
            if self.connectedto:
                ret.append(("Bruidegom",self.akteid,self.connectedto))
            if self.connectedto2:
                ret.append(("Bruid",self.akteid,self.connectedto2))
        elif self.eventtype == "Geboorte" or self.eventtype == "Overlijden":
            if self.connectedto:
                ret.append((self.eventtype,self.akteid,self.connectedto))
        if len(ret) == 0:
            return None
        return ret
        
    def move(self,pos):
        """
        Move the sprite to new location

        pos: tuple of movement
        """
        self.rect.move_ip(pos)

    def number_of_connection_to_make(self):
        """ how many connections still to make from this sprite
        """
        count = 0
        if self.allow_connect_from:
            if not self.connectedto:
                count = 1
        if self.allow_connect_from2:
            if not self.connectedto2:
                count += 1
        return count
    
    def allowed_to_connect_to(self,sprite,dragfromtype):
        """ determine if other sprite can connect to this one

        return True is so, else False
        """
        if dragfromtype == "Bruid":
            if self.allow_connect_from2 and sprite.allow_connect_to:
                #if self.eventtype == "Geboorte" and sprite.eventtype == "Geboorte":
                #    return False
                #if self.eventtype == "Overlijden" and sprite.eventtype == "Overlijden":
                #    return False
                return True
        else:
            if self.allow_connect_from and sprite.allow_connect_to:
                return True
        return False

    def get_sort_id(self):
        """ return id of akte to sort on, first letters, than eventdate
        """
        akte = data.akte.akte(self.akteid)
        akte.load_from_string(self.aktestring,self.akteid)
        if akte.eventtype == "Huwelijk":
            vader = akte.find_person_with_role("Bruidegom")
            moeder = akte.find_person_with_role("Bruid")
            vader2 = None
            moeder2 = None
            if self.allow_connect_from:
                vader2 = akte.find_person_with_role("Vadervandebruidegom")
                moeder2 = akte.find_person_with_role("Moedervandebruidegom")
            if self.allow_connect_from2:
                vader2 = akte.find_person_with_role("Vadervandebruid")
                moeder2 = akte.find_person_with_role("Moedervandebruid")
            if vader2 and moeder2:
                vader = vader2
                moeder = moeder2
        if akte.eventtype == "Geboorte" or akte.eventtype == "Overlijden":
            vader = akte.find_person_with_role("Vader")
            moeder = akte.find_person_with_role("Moeder")
        if vader and vader.firstname:
            vader = vader.firstname
        else:
            vader = chr(ord('z')+1)
        if moeder and moeder.firstname:
            moeder = moeder.firstname
        else:
            moeder = chr(ord('z')+1)
        # nog iets met eventdate
        return vader[0] + moeder[0] + akte.eventdate
    
class AkteCanvas:
    def __init__(self):
        self.aktesprites = {}   # dict[akteid] to aktesprite structures
        self.rect = None        # the totalsize of the canvas
        self.lastnamebruidegom = "Feenstra"
        self.lastnamebruid = "Vries"

    def calc_size(self):
        """ calculate the surounding box, and inflate this by 1000 pixels
        """
        self.rect = pygame.Rect(0,0,1000,1000)
        for i in self.aktesprites:
            self.rect.union_ip(self.aktesprites[i].rect)
        self.rect.inflate_ip(1000,1000)
        #print(self.rect)
            
    def clamp_rect(self,rect):
        """ Make sure rect is not outside canvas size
        """
        rect.clamp_ip(self.rect)
        
    def init(self,filename):
        """ Load a puzzle from file
        """
        fp = open(filename,"r")
        parsed_json = json.load(fp)
        fp.close()
        self.lastnamebruidegom = parsed_json["achternaambruidegom"]
        self.lastnamebruid = parsed_json["achternaambruid"]
        self.aktesprites = {}

        for i in parsed_json["connectfromto"]:
            self.aktesprites[i] = AkteSprite(i)
            self.aktesprites[i].init(i,parsed_json["connectfromto"][i],True,True,self.lastnamebruidegom,self.lastnamebruid)
        for i in parsed_json["connectfrom"]:
            self.aktesprites[i] = AkteSprite(i)
            self.aktesprites[i].init(i,parsed_json["connectfrom"][i],False,True,self.lastnamebruidegom,self.lastnamebruid)
        for i in parsed_json["connectto"]:
            self.aktesprites[i] = AkteSprite(i)
            self.aktesprites[i].init(i,parsed_json["connectto"][i],True,False,None,None)     # lastnamebruidegom&bruid niet nodig wegens connectfrom == False

        # becaus pygame (and python 2) can't handle unicode stuf, normalize
        #self.lastnamebruidegom = self.lastnamebruidegom.encode('cp1252')
        #self.lastnamebruid = self.lastnamebruid.encode('cp1252')

        for i in parsed_json["connections"]:
            # i = [rol,src akte,dstn akte]
            if i[1] in self.aktesprites:
                if i[0] == "Geboorte" or i[0] == "Overlijden" or i[0] == "Bruidegom":
                    self.aktesprites[i[1]].connectedto = i[2]
                if i[0] == "Bruid":
                    self.aktesprites[i[1]].connectedto2 = i[2]

        for i in self.aktesprites:
            self.aktesprites[i].update_line_colour(self.aktesprites)

        self.auto_place()
                    
    def auto_place(self,spacing = 10):
        """ Place aktes on canvas with this space between them
        sort on first letter of firstnames and then on eventdate
        """
        index = {}      # index om alle sotids te bewaren
        
        totalheight = 0
        for i in self.aktesprites:
            totalheight += self.aktesprites[i].rect.height + spacing
            tosortid = self.aktesprites[i].get_sort_id()
            if tosortid in index:
                index[tosortid].append(i)
            else:
                index[tosortid] = [i]
        zort = []    # tmp list because dict can not be sorted
        for i in index:
            zort.append(i)
        zort = sorted(zort)
        
        screensize = 1000
        nrcolumns = 1
        nrrows = 1
        
        while totalheight > nrcolumns * nrrows * screensize:
            if nrcolumns > nrrows:
                nrrows += 1
            else:
                nrcolumns += 1
        moveto = [0,0]
        
        snakedown = True
        width = screensize
        for j in zort:
            for i in index[j]:
                width = max(width,self.aktesprites[i].rect.width + spacing)
                if snakedown:
                    self.aktesprites[i].rect.topleft = moveto
                    moveto[1] += self.aktesprites[i].rect.height + spacing
                    if moveto[1] > nrrows * screensize:
                        # reached the end of a column, move to next
                        moveto[0] += width
                        width = screensize
                        moveto[1] = nrrows * screensize
                        snakedown = False
                else:
                    self.aktesprites[i].rect.bottomleft = moveto
                    moveto[1] -= self.aktesprites[i].rect.height + spacing
                    if moveto[1] < 0:
                        # reached the end of a column, move to next
                        moveto[0] += width
                        width = screensize
                        moveto[1] = 0
                        snakedown = True

    def save(self,filename,rect):
        """ save the connecting game state to json file
        """
        balk = pygame.Rect(rect.topleft,(0,rect.height))
        fp = open(filename,"wb")
        savestruct = { "lastnamebruidegom":self.lastnamebruidegom,"lastnamebruid":self.lastnamebruid,"aktesprites":{}}
        tel = 0
        for i in self.aktesprites:
            balk.width = rect.width * tel / len(self.aktesprites)
            tel += 1
            savestruct["aktesprites"][i] = self.aktesprites[i].to_json_struct()
            pygame.draw.rect(DISPLAYSURF,GREEN,balk)
            pygame.display.update()
        json.dump(savestruct,fp,separators=(',',':'),indent=4)
        fp.close()
        pygame.draw.rect(DISPLAYSURF,GREEN,rect)

    def load(self,filename):
        """ load the savegame to continue "connecting"
        """
        fp = open(filename,"r")
        parsed_json = json.load(fp)
        fp.close()
        self.lastnamebruidegom = parsed_json["lastnamebruidegom"]
        self.lastnamebruid = parsed_json["lastnamebruid"]
        self.aktesprites = {}
        for i in parsed_json["aktesprites"]:
            self.aktesprites[i] = AkteSprite(i)
            self.aktesprites[i].from_json_dict(parsed_json["aktesprites"][i])
        for i in parsed_json["aktesprites"]:
            self.aktesprites[i].update_line_colour(self.aktesprites)

    def get_puzzle(self,achternaambruidegom,achternaambruid):
        """ get puzzle from central server
        """
        # https://docs.python.org/3.5/howto/urllib2.html?highlight=url
        # https://docs.python.org/3.5/library/urllib.request.html#module-urllib.request
        #
        self.achternaambruidegom = achternaambruidegom
        self.achternaambruid = achternaambruid
        # http://akteconnect.tresoar.int/get_puzzle?achternaambruidegom="Feenstra"&achternaambruid="Vries"
        # return connectto:[ lijst..]
        # connectfrom:[lijst]  (meestal leeg)
        # connectfromto: [lijst] (bijna alle akten, behalve de huwelijken met de namen)

    def put_result(self,where,rect):
        """ send result to central server
        """
        balk = pygame.Rect(rect.topleft,(0,rect.height))
        result = []
        con = sqlite3.connect(where)
        con.isolation_level = None
        cur = con.cursor()
        tel = 0
        for i in self.aktesprites:
            balk.width = rect.width * tel / len(self.aktesprites)
            tel += 1
            res = self.aktesprites[i].to_result()
            if res:
                #cur.executemany('''INSERT OR REPLACE INTO koppel(rol,srcakte,dstnakte,wie) values(?,?,?,'{}')'''.format(os.getenv('USERNAME','Unknown')),res)
                result += res
                pygame.draw.rect(DISPLAYSURF,GREEN,balk)
                pygame.display.update()
                #pygame.time.wait(1000)
        #print result
        cur.executemany('''INSERT OR REPLACE INTO koppel(rol,srcakte,dstnakte,wie) values(?,?,?,'{}')'''.format(os.getenv('USERNAME','Unknown')),result)
        con.commit()
        con.close()
        pygame.draw.rect(DISPLAYSURF,GREEN,rect)
        
    def set_caption(self):
        #print self.lastnamebruidegom + " - " + self.lastnamebruid
        pygame.display.set_caption((self.lastnamebruidegom + " - " + self.lastnamebruid).encode('utf-8'))
    
    def draw(self,surface,viewport,hightlight_connect_from):
        """ Draw all akte sprite and lines between them on a surface
        """
        # draw lines
        for i in self.aktesprites:
            self.aktesprites[i].draw_line(surface,viewport,self.aktesprites)
        # draw sprites
        for i in self.aktesprites:
            self.aktesprites[i].draw_sprite(surface,viewport,hightlight_connect_from)

    def find_sprite_point(self,x,y):
        """ find which akte sprite is on location x,y
        return akteid or None if nothing is found
        """
        for i in self.aktesprites:
            if self.aktesprites[i].rect.collidepoint(x,y):
                return i
        return None

    def find_sprite_rect(self,dragsprite):
        """ find which sprite is in de rectagle op dragsprite
        Used for collision detection in order to connect to akten
        exclude the sprite itself
        """
        rect = dragsprite.rect
        for i in self.aktesprites:
            if self.aktesprites[i] != dragsprite and self.aktesprites[i].rect.colliderect(rect):
                return self.aktesprites[i]
        return None
    
    def get_sprite(self,akteid):
        """
        Return the sprite for akteid
        used for dragging
        """
        if akteid in self.aktesprites:
            return self.aktesprites[akteid]
        return None

    def update_line_colour(self,dragsprite):
        """ determine and set the linecolour of all connections op sprite
        """
        dragsprite.update_line_colour(self.aktesprites)

    def number_of_connection_to_make(self):
        """ count the number of connections still to make
        """
        count = 0
        for i in self.aktesprites:
            count += self.aktesprites[i].number_of_connection_to_make()
        return count

DISPLAYSURF = pygame.display.set_mode((950,608),pygame.RESIZABLE)
def akteconnect(filepath,filename):
    global DISPLAYSURF
    #DISPLAYSURF = pygame.display.set_mode((950,608),pygame.RESIZABLE)
    # viewport is a portion of the total canvas
    canvas = AkteCanvas()
    if filename.endswith(".puz"):
        canvas.init(filepath + '/' + filename)
    elif filename.endswith(".ac"):
        canvas.load(filepath + '/' + filename)
    else:
        print "ERROR wrong filename"
        return

    canvas.set_caption()
    toconnectcount = canvas.number_of_connection_to_make()    # determine the number of connections to make

    # the rect what is shown on the screen
    viewport = DISPLAYSURF.get_rect()
    running = True

    mousedown = False
    #dragfrompos = None
    dragsprite = None
    dragorigpos = (0,0)
    dragfromtype = "Normal"        # or "Bruid" if dragging the bruid
    collidedwith = None
    hightlight_connect_from = False
    canvas.calc_size()

    while running: # main game loop
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYUP and event.key == K_ESCAPE:
                running = False
            if event.type == KEYUP and event.key == ord('x'):    # toggle highlight connect from sprites
                hightlight_connect_from = not hightlight_connect_from
            if event.type == pygame.MOUSEMOTION:
                #lastmousepos = event.pos
                #pixObj = pygame.PixelArray(DISPLAYSURF)
                #pixObj[event.pos[0]][event.pos[1]] = WHITE
                #del pixObj
                if mousedown:
                    if dragsprite:
                        # get en set pos
                        dragsprite.rect.move_ip(event.rel)
                        collidedwith = canvas.find_sprite_rect(dragsprite)
                    else:
                        #print event.rel
                        viewport.move_ip(-event.rel[0],-event.rel[1])
                        viewport.clamp_ip(canvas.rect)
                
            if event.type == pygame.MOUSEBUTTONUP:
                mousedown = False
                #print "Drag from",dragfrompos,"to",event.pos
                #print event.button
                
                if dragsprite:
                    collidedwith = canvas.find_sprite_rect(dragsprite)
                    if collidedwith:
                        dragsprite.rect.topleft = dragorigpos
                        #if dragsprite.allow_connect_from and collidedwith.allow_connect_to:
                        if dragsprite.allowed_to_connect_to(collidedwith,dragfromtype):
                            # A connection has been made
                            if dragfromtype == "Normal":
                                if dragsprite.connectedto == None:
                                    toconnectcount -= 1
                                dragsprite.connectedto = collidedwith.akteid
                            elif dragfromtype == "Bruid":
                                if dragsprite.connectedto2 == None:
                                    toconnectcount -= 1
                                dragsprite.connectedto2 = collidedwith.akteid
                            canvas.update_line_colour(dragsprite)

                dragsprite = None
                # if collision with dragcollisionbox, connect
                # else move box (if no collision from dragdrawbox)
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                #print event.button
                if event.button == 1:   # left button   #### rechtermuis = koppel gelijkwaardig ????
                    mousedown = True
                    collidedwith = None
                    sprite = canvas.find_sprite_point(event.pos[0] + viewport.x, event.pos[1] + viewport.y)
                    if sprite:
                        dragsprite = canvas.get_sprite(sprite)
                        #print dragsprite.akteid
                        #print dragsprite.linecolour
                        #print dragsprite.connectedto
                        #print dragsprite.allow_connect_to
                        dragorigpos = dragsprite.rect.topleft   # remember begin position, to return to if connected
                        if dragsprite.eventtype == "Huwelijk" and event.pos[0] + viewport.x > dragsprite.middleline + dragsprite.rect.left:
                            dragfromtype = "Bruid"      # drag bruid part of huwelijk
                            #print "drag bruid"
                        else:
                            dragfromtype = "Normal"
                    else:
                        dragsprite = None
                elif event.button == 2:     # middle button = delete conectto
                    sprite = canvas.find_sprite_point(event.pos[0] + viewport.x, event.pos[1] + viewport.y)
                    if sprite:
                        dragsprite = canvas.get_sprite(sprite)
                        if dragsprite.eventtype == "Huwelijk" and event.pos[0] + viewport.x > dragsprite.middleline + dragsprite.rect.left:
                            if dragsprite.connectedto2:
                                dragsprite.connectedto2 = None
                                toconnectcount += 1
                        else:
                            if dragsprite.connectedto:
                                dragsprite.connectedto = None
                                toconnectcount += 1
                        dragsprite = None
                            
            if event.type == pygame.VIDEORESIZE:
                #print "New size",event.size
                DISPLAYSURF = pygame.display.set_mode(event.size,pygame.RESIZABLE)

        DISPLAYSURF.fill(BACKGROUNDCOLOUR)
        if dragsprite and collidedwith:
            if dragsprite.allowed_to_connect_to(collidedwith,dragfromtype):
            #if dragsprite.allow_connect_from and collidedwith.allow_connect_to:    
                collidedwith.highlight = CONNECTOKCOLOUR
            else:
                collidedwith.highlight = CONNECTNOTOKCOLOUR
        canvas.draw(DISPLAYSURF,viewport,hightlight_connect_from)
        if dragsprite and collidedwith:
            collidedwith.highlight = None

        # show max number of connections still to make
        countblit = CONNECTCOUNTFONT.render(str(toconnectcount), True, CONNECTCOUNTFONTCOLOUR)
        DISPLAYSURF.blit(countblit, (DISPLAYSURF.get_width() - countblit.get_width() - 30,10))
        
        pygame.display.update()
        fpsClock.tick(FPS)
    #now = pygame.time.get_ticks()
    rect = pygame.Rect(0,0,DISPLAYSURF.get_width()*4/5,50)
    rect.move_ip(DISPLAYSURF.get_width()/10, DISPLAYSURF.get_height()/2 - 25)
    DISPLAYSURF.fill(BLACK,rect)
    pygame.draw.rect(DISPLAYSURF,WHITE,rect,3)
    pygame.draw.rect(DISPLAYSURF,BLACK,rect,1)
    rect.inflate_ip(-5,-5)
    rect.width = rect.width / 2
    pygame.display.update()
    #pygame.time.wait(1000)
    canvas.put_result('koppel.db',rect)
    #pygame.draw.rect(DISPLAYSURF,GREEN,rect)
    rect.move_ip(rect.width,0)
    pygame.display.update()
    #pygame.time.wait(1000)
    #canvas.put_result("akteconnectserver.company.int")
    canvas.save(filepath + '/' + canvas.lastnamebruidegom + "-" + canvas.lastnamebruid + ".ac",rect)
    #pygame.draw.rect(DISPLAYSURF,GREEN,rect)
    DISPLAYSURF.fill(BACKGROUNDCOLOUR)
    pygame.display.update()
    #print "Afsluiten duurde",(pygame.time.get_ticks() - now)/1000.0,"seconden"
############### main

options = {}
options['defaultextension'] = '.puz'
options['filetypes'] = [('Puzzels', '.puz;*.ac')]
options['initialdir'] = 'puzzels'
#options['initialfile'] = 'myfile.puz'
#options['parent'] = root
options['title'] = 'AkteConnect'

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
filename = "xxxx"
while filename:
    filename = askopenfilename(**options) # show an "Open" dialog box and return the path to the selected file
    if filename:
        f = filename.rsplit('/',1)
        #print(f[0],"&&&&&",f[1])
        akteconnect(f[0],f[1])
        options['initialfile'] = f[1]
        options['initialdir'] = f[0]

pygame.quit()
