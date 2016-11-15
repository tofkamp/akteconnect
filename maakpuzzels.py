# maakpuzzels.py - Create .puz files from database
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

import sqlite3
import os
import json

import data.akte
import data.aktecache

#2016-08 {'Kapstokken': 218005, 'Stukjes': 1086670, 'Puzzels': 209545}
#2016-09 {'Kapstokken': 218005, 'Stukjes': 1086727, 'Puzzels': 209547}

# koppelcursor.execute('''CREATE TABLE koppel (rol text,srcakte text,dstnakte text)''')

con = sqlite3.connect('e:/BurgelijkeStand1611.db')
con.isolation_level = None
cur = con.cursor()

print("Preloading akten")
preload = data.aktecache.aktecache(cur)

class puzzelstukje:
    def __init__(self):
        self.done = False
        
    
class puzzel:
    def __init__(self):
        self.achternaambruidegom = None
        self.achternaambruid = None
        self.done = False
        self.puzzelstukjes = []    # connectfromto
        self.kapstok = []          # connectto
        self.connections = []
        self.modified = False
        #self.aktesnadatum = "9999-12-31"

    def clear_done_flag(self):
        for stukje in self.puzzelstukjes:
                self.puzzelstukjes[stukje].done = False

    def add_connections(self,koppels,bruidkoppels):
        for i in self.puzzelstukjes:
            akte = data.akte.akte(i)
            akte.load_from_string(preload.aktes[i],i)
            if akte.eventtype == "Huwelijk":
                koptype = "Bruidegom"
            else:
                koptype = akte.eventtype
            if i in koppels:
                if koppels[i] in self.puzzelstukjes:
                    self.connections.append((koptype,i,koppels[i]))
                elif koppels[i] in self.kapstok:
                    self.connections.append((koptype,i,koppels[i]))
            if i in bruidkoppels:
                if bruidkoppels[i] in self.puzzelstukjes:
                    self.connections.append(("Bruid",i,bruidkoppels[i]))
                elif bruidkoppels[i] in self.kapstok:
                    self.connections.append(("Bruid",i,bruidkoppels[i]))
                
    def export_puzzel(self,path,filename):    
        connectto = {}
        connectfromto = {}
        for i in self.puzzelstukjes:
            connectfromto[i] = preload.aktes[i]
        for i in self.kapstok:
            if i not in self.puzzelstukjes:
                connectto[i] = preload.aktes[i]
        
        if len(self.puzzelstukjes) > 0:
            #print(filename)
            os.makedirs(path,exist_ok=True)
            fp = open(path + '/' + filename,"w")
            fp.write(json.dumps({"connectfromto":connectfromto,"connectto":connectto,"connectfrom":{},
            "achternaambruid":self.achternaambruid,"achternaambruidegom":self.achternaambruidegom,
            "connections":self.connections},indent=4))
            fp.close()
        
class puzzels:
    def __init__(self):
        self.achternamen = {}
        #self.kapstokindex = {}

    def load_from_sql(self,cursor):
        # iets van select etc
        pass

    def save_to_sql(self,cursor):
        # iets van select etc
        pass

    def clear_done_flag(self):
        for bruidegom in self.achternamen:
            for bruid in self.achternamen[bruidegom]:
                self.achternamen[bruidegom][bruid].clear_done_flag()

    def xxxxxstatistics(self):
        totalkapstok = 0
        totalpuzzels = 0
        totalstukjes = 0
        for bruidegom in self.achternamen:
            totalpuzzels += len(self.achternamen[bruidegom])
            for bruid in self.achternamen[bruidegom]:
                if len(self.achternamen[bruidegom][bruid].puzzelstukjes) > 0:
                    totalkapstok += len(self.achternamen[bruidegom][bruid].kapstok)
                    totalstukjes += len(self.achternamen[bruidegom][bruid].puzzelstukjes)
        return { "Puzzels" : totalpuzzels, "Kapstokken" : totalkapstok, "Stukjes" : totalstukjes }

    def statistics(self):
        nrnamen = {}
        nrpuzzels = {}
        nrstukjes = {}
        nrconnects = {}
        for bruidegom in self.achternamen:
            if bruidegom:
                letter = bruidegom[0].upper()
                #if letter == 'Ö':
                #    print(bruidegom)
            else:
                letter = '-'
            if letter not in nrnamen:
                nrnamen[letter] = 0
                nrstukjes[letter] = 0
                nrpuzzels[letter] = 0
                nrconnects[letter] = 0
            nrnamen[letter] += 1
            for bruid in self.achternamen[bruidegom]:
                if len(self.achternamen[bruidegom][bruid].puzzelstukjes) > 0:
                    nrpuzzels[letter] += 1
                    nrstukjes[letter] += len(self.achternamen[bruidegom][bruid].puzzelstukjes)
                    nrstukjes[letter] += len(self.achternamen[bruidegom][bruid].kapstok)
                    nrconnects[letter] += len(self.achternamen[bruidegom][bruid].connections)
        for i in nrnamen:
            print(i,nrnamen[i],nrpuzzels[i],nrstukjes[i],nrconnects[i])
    
    def find_puzzel(self,achternaambruidegom,achternaambruid):
        achternaambruidegom = achternaambruidegom.lower()
        achternaambruid = achternaambruid.lower()
        if not achternaambruidegom in self.achternamen:
            return None
        if not achternaambruid in self.achternamen[achternaambruidegom]:
            return None
        return self.achternamen[achternaambruidegom][achternaambruid]
    
    def create_puzzel(self,achternaambruidegom,achternaambruid,akteid):
        achternaambruidegom = achternaambruidegom.lower()
        achternaambruid = achternaambruid.lower()
        if not achternaambruidegom in self.achternamen:
            self.achternamen[achternaambruidegom] = {}
        if not achternaambruid in self.achternamen[achternaambruidegom]:
            self.achternamen[achternaambruidegom][achternaambruid] = puzzel()
        puz = self.achternamen[achternaambruidegom][achternaambruid]
        #if self.kapstokindex[akteid] != puz:
        #    pass
        if not akteid in puz.kapstok:
            puz.kapstok.append(akteid)
            #self.kapstokindex[akteid] = puz

    def create_puzzel_stukje(self,achternaamman,achternaamvrouw,akteid):
        achternaamman = achternaamman.lower()
        achternaamvrouw = achternaamvrouw.lower()
        puz = self.find_puzzel(achternaamman,achternaamvrouw)
        if puz is None:
            return
        #if akteid in puz.kapstok:
        #    return
        if not akteid in puz.puzzelstukjes:
            puz.puzzelstukjes.append(akteid)
            #puz.index[akteid] = puz

    def add_akte_to_puzzels(self,akte):
        if akte.eventtype == "Geboorte" or akte.eventtype == "Overlijden":
            vader = akte.find_person_with_role("Vader")
            moeder = akte.find_person_with_role("Moeder")
            if vader and moeder:
                if vader.lastname and moeder.lastname:
                    self.create_puzzel_stukje(vader.lastname,moeder.lastname,akte.akte_id)
        if akte.eventtype == "Huwelijk":
            # bruidegom
            vader = akte.find_person_with_role("Vadervandebruidegom")
            moeder = akte.find_person_with_role("Moedervandebruidegom")
            if vader and moeder:
                if vader.lastname and moeder.lastname:
                    self.create_puzzel_stukje(vader.lastname,moeder.lastname,akte.akte_id)
            # bruid
            vader = akte.find_person_with_role("Vadervandebruid")
            moeder = akte.find_person_with_role("Moedervandebruid")
            if vader and moeder:
                if vader.lastname and moeder.lastname:
                    self.create_puzzel_stukje(vader.lastname,moeder.lastname,akte.akte_id)

    def export_puzzels(self,path):
        os.makedirs(path,exist_ok=True)
        for bruidegom in self.achternamen:
            for bruid in self.achternamen[bruidegom]:
                if bruidegom:
                    self.achternamen[bruidegom][bruid].achternaambruidegom = bruidegom
                    self.achternamen[bruidegom][bruid].achternaambruid = bruid
                    self.achternamen[bruidegom][bruid].export_puzzel(path + "/" + bruidegom[0] + '/'+ bruidegom,bruidegom + "-" + bruid + ".puz")

    def add_connections(self,koppelfilename):
        koppels = {}
        bruidkoppels = {}
        koppel = sqlite3.connect(koppelfilename)
        koppelcursor = koppel.cursor()

        for row in koppelcursor.execute('SELECT rol,srcakte,dstnakte FROM koppel'):
            if row[0] == "Bruid":
                bruidkoppels[row[1]] = row[2]
            else:
                koppels[row[1]] = row[2]
        koppel.close()
        #print(bruidkoppels)
        #print(koppels)
        for bruidegom in self.achternamen:
            for bruid in self.achternamen[bruidegom]:
                self.achternamen[bruidegom][bruid].add_connections(koppels,bruidkoppels)
        #for bruidegom in self.achternamen:
        #    for bruid in self.achternamen[bruidegom]:
        #        if self.achternamen[bruidegom][bruid].connections != []:
        #            print(bruidegom,bruid)


print("Creating puzzels")
puzs = puzzels()
for akteid in preload.aktes:
    if akteid == '9df40cd8-fa49-deec-faab-32bb428be7ae':     # HCL Jong\r\nJong gepruts
        continue
    akte = data.akte.akte(akteid)
    akte.load_from_string(preload.aktes[akteid],akteid)
    if akte.eventtype == "Huwelijk":
        bruidegom = akte.find_person_with_role("Bruidegom")
        if bruidegom:
            bruid = akte.find_person_with_role("Bruid")
            if bruid:
                puzs.create_puzzel(bruidegom.lastname,bruid.lastname,akteid)

print("Adding pieces")
for akteid in preload.aktes:
    akte = data.akte.akte(akteid)
    akte.load_from_string(preload.aktes[akteid],akteid)
    puzs.add_akte_to_puzzels(akte)

print("Adding connections")
puzs.add_connections('koppelmaster.db')

print("Counting")
puzs.statistics()

print("Exporting")
puzs.export_puzzels("e:/puzzels")

con.close()
