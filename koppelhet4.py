# koppelhet4.py - Export koppellingen to LOD en Gramps csv
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
import json
import csv

import data.akte

NEWIDS = 10000000    # previuos unknown persons get ids above this number
# https://gramps-project.org/wiki/index.php?title=Gramps_4.2_Wiki_Manual_-_Manage_Family_Trees:_CSV_Import_and_Export

con = sqlite3.connect('e:/BurgelijkeStand1610.db')
con.isolation_level = None
cur = con.cursor()

#todo:  huwelijk vullen met akte + source ?,verwijder akte anders aktestring gebruiken
# csv export in procedure
BASEURI = "http://data.kultuer.frl/"
PLACESURI = BASEURI + "personen/"
PERSOONURI = BASEURI + "personen/"
AKTESURI = BASEURI + "allefriezen/"

def formattriple(uri):
    prefixes = {
        "rdf" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs" : "http://www.w3.org/2000/01/rdf-schema#",
        "owl" : "http://www.w3.org/2002/07/owl#",
        "xsd" : "http://www.w3.org/2001/XMLSchema#",
        "dc" :  "http://purl.org/dc/elements/1.1/",
        "dcterms" : "http://purl.org/dc/terms/",
        "skos" : "http://www.w3.org/2004/02/skos/core#",
        "foaf" : "http://xmlns.com/foaf/0.1/",
        "vocab" : "http://data.kultuer.frl/allefriezen/",
        "a2a" : "http://Mindbus.nl/A2A/",
        "schema" : "http://schema.org/"}
    if uri.startswith('http://') or uri.startswith('https://'):
        return "<" + uri + ">"
    if ':' in uri:
        prefix,url = uri.split(':',maxsplit=1)
        if prefix in prefixes:
            return "<{}{}>".format(prefixes[prefix],url)
        #return "ERROR unknown prefix {}".format(prefix)
    return '"' + uri + '"'

def outn3(fp,subject,predicate,obj):
    #lineoutcount += 1
    subject = formattriple(subject)
    predicate = formattriple(predicate)
    obj = obj.replace('\\','\\\\')
    obj = obj.replace('\n','\\n')
    obj = obj.replace('\r','\\r')    # of weg halen ?
    obj = obj.replace('"','\\"')
    obj = obj.replace("'","\\'")
    obj = formattriple(obj)
    #print('{} {} {} .'.format(subject,predicate,obj))
    fp.write('{} {} {} .\n'.format(subject,predicate,obj))


class Places:
    """place - a reference to this place
    title - title of place
    name - name of place
    type - type of place (eg, City, County, State, etc.)
    latitude - latitude of place
    longitude - longitude of place
    code - postal code, etc.
    enclosed_by - the reference to another place that encloses this one
    date - date that the enclosed_by place was in effect
    """
    def __init__(self):
        self.place_list = {}
        self.last_place_id = 0
        self.persist_ids = {}
        self.grens = 0
    
    def load_persist_ids(self):
        """ load known persistant places with their id from database

        self.grens is the border of already known, and previuos unknown places
        """
        pcon = sqlite3.connect('persistant-ids.db',uri=True)
        pcur = pcon.cursor()
        self.grens = 0
        for row in pcur.execute('SELECT placeid,id FROM places'):
            self.persist_ids[row[0]] = row[1]
            self.grens = max(self.grens,row[1])
        pcon.close()
        self.last_place_id = self.grens

    def save_persist_ids(self):
        """ write all new places to database, inorder to use them the next time
        """
        pcon = sqlite3.connect('persistant-ids.db')
        pcur = pcon.cursor()
        for i in self.place_list:
            if self.place_list[i] > self.grens:
                #print('INSERT INTO places(placeid,id) VALUES({},{})'.format(i,self.place_list[i]))
                pcur.execute('INSERT INTO places(placeid,id) VALUES(?,?)',(i,self.place_list[i]))
        pcon.commit()
        pcon.close()

    def register(self,place):
        """ make sure place is known with a id, if unknown, add it
        """
        if place is None:
            return
        if place not in self.place_list:
            if place in self.persist_ids:
                self.place_list[place] = self.persist_ids[place]
            else:
                self.last_place_id += 1
                self.place_list[place] = self.last_place_id
            #return self.last_place_id
        return self.place_list[place]

    def get_export_csv_header(self):
        return "Locatie,Titel,Naam,Type,Breedtegraad,Lengtegraad,Code,Besloten in,Datum".split(",")
    
    def export_csv_places(self,dictwriter):
        for place in self.place_list:
            row = { "Locatie" : "[P"+str(self.place_list[place])+']', "Naam" : place, "Type" : "Onbekend" }
            dictwriter.writerow(row)

    def export_lod(self,fp):
        """ write out the places with their persistant ids
        """
        global PLACESURI
        for place in self.place_list:
            outn3(fp,PLACESURI + 'P' + str(self.place_list[place]),"rdf:type","schema:Place")
            outn3(fp,PLACESURI + 'P' + str(self.place_list[place]),"rdfs:label",place)

places = Places()
places.load_persist_ids()

class Individual:
    def __init__(self,aktepersoon):
        self.aktepersoon = data.akte.aktepersoon()
        self.aktepersonen = []
        self.attributes = {}
        if aktepersoon:
            self.aktepersoon.merge(aktepersoon)
            self.from_akte_persoon(aktepersoon)
            #self.aktepersonen = [aktepersoon.akteid + "/" + aktepersoon.persoonid]   # voor als persoon niet uniek is binnen database
            self.aktepersonen = [aktepersoon.persoonid]

    #def get_export_csv_header_people(self):
    #    return ["person","firstname","prefix","lastname","gender","birthdate","birthplaceid","deathdate","deathplaceid"]
    #"Persoon,Achternaam,Voornaam,Roep,Achtervoegsel,Voorvoegsel,Titel,Geslacht,Geboortedatum,Geboorteplaats,Geboortebron,doopdatum,doopplaats,Doopbron
    #,Sterfdatum,Sterfplaats,Overlijdensbron,Begrafenisdatum,Begraafplaats,Begrafenisbron,Opmerking".split(","),lineterminator='\n')
    
    def export_csv_people(self,dictwriter,identifier):
        """ write csv with attributes """
        self.add_attribute("Persoon","[I" + str(identifier) + ']')
        dictwriter.writerow(self.attributes)
        #self.attributes = {}

    def export_lod(self,fp,identifier):
        global PERSOONURI
        global PLACESURI
        global AKTESURI
        outn3(fp,PERSOONURI + "I" + str(identifier),"rdf:type","schema:Person")
        outn3(fp,PERSOONURI + "I" + str(identifier),"rdfs:label",self.aktepersoon.to_string(useage = False))
        if self.aktepersoon.firstname:
            if self.aktepersoon.patronym:
                outn3(fp,PERSOONURI + "I" + str(identifier),"schema:givenName",self.aktepersoon.firstname + " " + self.aktepersoon.patronym)
            else:
                outn3(fp,PERSOONURI + "I" + str(identifier),"schema:givenName",self.aktepersoon.firstname)
        if self.aktepersoon.lastname:
            if self.aktepersoon.prefixlastname:
                outn3(fp,PERSOONURI + "I" + str(identifier),"schema:familyName",self.aktepersoon.prefixlastname + " " + self.aktepersoon.lastname)
            else:
                outn3(fp,PERSOONURI + "I" + str(identifier),"schema:familyName",self.aktepersoon.lastname)
        if self.aktepersoon.gender:
            if self.aktepersoon.gender == "Vrouw":
                outn3(fp,PERSOONURI + "I" + str(identifier),"schema:gender","schema:Female")
            if self.aktepersoon.gender == "Man":
                outn3(fp,PERSOONURI + "I" + str(identifier),"schema:gender","schema:Male")
        if self.aktepersoon.birthplace:
            place_id = "P" + str(places.register(self.aktepersoon.birthplace))
            outn3(fp,PERSOONURI + "I" + str(identifier),"schema:birthPlace",PLACESURI + place_id)
        if self.aktepersoon.deathplace:
            place_id = "P" + str(places.register(self.aktepersoon.deathplace))
            outn3(fp,PERSOONURI + "I" + str(identifier),"schema:deathPlace",PLACESURI + place_id)
        if self.aktepersoon.birthdate:
            outn3(fp,PERSOONURI + "I" + str(identifier),"schema:birthDate",self.aktepersoon.birthdate)
        if self.aktepersoon.deathdate:
            outn3(fp,PERSOONURI + "I" + str(identifier),"schema:deathDate",self.aktepersoon.deathdate)
        for i in self.aktepersonen:
            outn3(fp,PERSOONURI + "I" + str(identifier),"owl:sameAs",AKTESURI + i.replace(':',''))
        
    def from_akte_persoon(self,aktepersoon):
        """ create a person with info from a person on a akte """
        if aktepersoon.firstname:
            if aktepersoon.patronym:
                self.add_attribute("Voornaam",aktepersoon.firstname + " " + aktepersoon.patronym)
            else:
                self.add_attribute("Voornaam",aktepersoon.firstname)
        if aktepersoon.lastname:
            self.add_attribute("Achternaam",aktepersoon.lastname)
        if aktepersoon.prefixlastname:
            self.add_attribute("Voorvoegsel",aktepersoon.prefixlastname)
        if aktepersoon.gender:
            if aktepersoon.gender == "Vrouw":
                self.add_attribute("Geslacht","vrouwelijk")
            if aktepersoon.gender == "Man":
                self.add_attribute("Geslacht","mannelijk")
        if aktepersoon.birthplace:
            place_id = places.register(aktepersoon.birthplace)
            self.add_attribute("Geboorteplaats id","P"+str(place_id))
        if aktepersoon.deathplace:
            place_id = places.register(aktepersoon.deathplace)
            self.add_attribute("Sterfplaats id","P"+str(place_id))
        if aktepersoon.birthdate:
            self.add_attribute("Geboortedatum",aktepersoon.birthdate)
        if aktepersoon.deathdate:
            self.add_attribute("Sterfdatum",aktepersoon.deathdate)

    def add_attribute(self,key,value):
        if value:
            self.attributes[key] = value
    
    def merge_with(self,indi):
        """ merge to individuals together . used for sameas """
        for key in indi.attributes:
            self.add_attribute(key,indi.attributes[key])
        # merge attributes ?
        #self.akte_personen += indi.akte_personen
        if indi.aktepersoon:
            self.aktepersoon.merge(indi.aktepersoon)
        self.aktepersonen += indi.aktepersonen
    
class Individuals:

    def __init__(self):
        self.lijst = {}
        self.grens = 0
        self.persist_ids = {}
        self.nextid = 10000001

    def create_table(self,conn):
        """ not used, but for documentation of format """
        conn.execute('''DROP TABLE IF EXISTS persons''')
        conn.execute('''DROP TABLE IF EXISTS places''')
        conn.execute('''CREATE TABLE persons(personid text,id int)''')
        conn.execute('''CREATE TABLE places(placeid text,id int)''')
        

    def load_persist_ids(self):
        """ load all known persistant ids into memory
        Search with python is a lot faster than with sqlite select statements """
        pcon = sqlite3.connect('persistant-ids.db',uri=True)
        pcur = pcon.cursor()
        self.grens = 0
        for row in pcur.execute('SELECT personid,id FROM persons'):
            self.persist_ids[row[0]] = row[1]
            self.grens = max(self.grens,row[1])
        pcon.close()

    def save_persist_ids(self):
        """ write out new ids to be persistant in the next run """
        pcon = sqlite3.connect('persistant-ids.db')
        pcur = pcon.cursor()
        for i in self.persist_ids:
            if self.persist_ids[i] > self.grens:
                pcur.execute('INSERT INTO persons(personid,id) VALUES(?,?)',(i,self.persist_ids[i]))
        pcon.commit()
        pcon.close()

    def renumber_ids(self):
        self.nextid = self.grens + 1
        addtolijst = {}
        for i in self.lijst:
            if type(self.lijst[i]) is not int:
                if i >= 10000000 and len(self.lijst[i].aktepersonen) > 0:
                    addtolijst[self.nextid] = self.lijst[i]
                    self.lijst[i] = self.nextid
                    self.nextid += 1
        for i in addtolijst:
            self.lijst[i] = addtolijst[i]
            self.persist_ids[addtolijst[i].aktepersonen[0]] = i
        print("Added",len(addtolijst),"identifiers")
        addtolijst = {}
        for i in self.lijst:
            if type(self.lijst[i]) is int:
                self.lijst[i] = self.normalize(self.lijst[i])
        
    def new_individual(self,aktepersoon):
        if aktepersoon:
            if aktepersoon.persoonid in self.persist_ids:
                self.lijst[self.persist_ids[aktepersoon.persoonid]] = Individual(aktepersoon)
                return self.persist_ids[aktepersoon.persoonid]
        self.lijst[self.nextid] = Individual(aktepersoon)
        self.nextid += 1
        return self.nextid - 1

    def same_as(self,p1,p2):
        """ make sure two individuals are the same,
        keep the lowest number """
        p1 = self.normalize(p1)
        p2 = self.normalize(p2)
        if p1 < p2:
            self.lijst[p1].merge_with(self.lijst[p2])
            self.lijst[p2] = p1
        if p1 > p2:
            self.lijst[p2].merge_with(self.lijst[p1])
            self.lijst[p1] = p2

    def normalize(self,p1):
        while type(self.lijst[p1]) is int:
            p1 = self.lijst[p1]
        return p1

    def normalize_to_object(self,p1):
        p1 = self.normalize(p1)
        return self.lijst[p1]

    def count(self):
        count = 0
        for i in self.lijst:
            if type(self.lijst[i]) is not int:
                count += 1
        return count

    def status(self):
        for i in self.lijst:
            if type(self.lijst[i]) is not int:
                print(self.lijst[i].aktepersoon)

    def export_to_csv(self,csvfile):
        """ produce csv format for gramps """
        writer = csv.DictWriter(csvfile, fieldnames="Persoon,Achternaam,Voornaam,Roep,Achtervoegsel,Voorvoegsel,Titel,Geslacht,Geboortedatum,Geboorteplaats id,Geboortebron,doopdatum,doopplaats,Doopbron,Sterfdatum,Sterfplaats id,Overlijdensbron,Begrafenisdatum,Begraafplaats,Begrafenisbron,Opmerking".split(","),lineterminator='\n')
        writer.writeheader()
        for i in self.lijst:
            if i < 10000000 and type(self.lijst[i]) is not int:
                self.lijst[i].export_csv_people(writer,i)
             
    def export_lod(self,fp):
        """ output linked open data format with schema.org """
        for i in self.lijst:
            if i < 10000000 and type(self.lijst[i]) is not int:
                self.lijst[i].export_lod(fp,i)

class Family:
    def __init__(self,individuals,man,vrouw,kind):
        self.vader = individuals.new_individual(man)
        self.moeder = individuals.new_individual(vrouw)
        self.kind = individuals.new_individual(kind)

class Node:
    def __init__(self,akte,individuals):
        #self.akte = akte   # is dit nodig ?
        self.eventtype = akte.eventtype
        self.eventplace = akte.eventplace
        self.eventdate = akte.eventdate
        #print(self.eventtype,self.eventplace,self.eventdate,akte.recordid)
        if self.eventtype == "Geboorte":
            self.gezin = Family(individuals,akte.find_person_with_role("Vader"),akte.find_person_with_role("Moeder"),akte.find_person_with_role("Kind"))
        if self.eventtype == "Overlijden":
            self.gezin = Family(individuals,akte.find_person_with_role("Vader"),akte.find_person_with_role("Moeder"),akte.find_person_with_role("Overledene"))
        if self.eventtype == "Huwelijk":
            self.gezin = Family(individuals,akte.find_person_with_role("Vadervandebruidegom"),akte.find_person_with_role("Moedervandebruidegom"),akte.find_person_with_role("Bruidegom"))
            self.gezin2 = Family(individuals,akte.find_person_with_role("Vadervandebruid"),akte.find_person_with_role("Moedervandebruid"),akte.find_person_with_role("Bruid"))

class Marriage:
    last_id = 1
    def __init__(self,eventdate = None,eventplace = None):
        self.children = []     # array of children id numbers
        self.eventdate = eventdate
        
        self.eventplace = places.register(eventplace)
        self.id = Marriage.last_id
        Marriage.last_id += 1
        #print("nieuw huwelijk ",self.id)

    def get_id(self):
        return "F" + str(self.id)

    def set_date_and_place(self,eventdate,eventplace):
        if eventdate:
            self.eventdate = eventdate
        if eventplace:
            if self.eventplace:
                print("Error,overwrite place",self.eventplace,"with",eventplace)
            else:
                self.eventplace = places.register(eventplace)
                
    def add_child(self,child_id):
        if child_id not in self.children:
            self.children.append(child_id)

    def export_csv_children(self,dictwriter):
        for child in self.children:
            if child < 10000000:
                row = { "Gezin" : self.get_id(), "Kind" : "I"+str(child) }
                dictwriter.writerow(row)

    def export_csv_marriage(self,dictwriter,man,vrouw):
        row = { "Huwelijk" : self.get_id() }
        if self.eventplace:
            row["Locatie id"] = "P"+str(self.eventplace)
        if self.eventdate:
            row["Datum"] = self.eventdate
        if man < 10000000 or vrouw < 10000000:
            if man < 10000000:
                row["Echtgenoot"] = "I"+str(man)
            if vrouw < 10000000:
                row["Echtgenote"] = "I"+str(vrouw)
            dictwriter.writerow(row)

    def export_lod(self,fp,man,vrouw):
        if man < 10000000 and vrouw < 10000000:
            outn3(fp,PERSOONURI + "I" + str(man),"schema:spouse",PERSOONURI + "I" + str(vrouw))
            outn3(fp,PERSOONURI + "I" + str(vrouw),"schema:spouse",PERSOONURI + "I" + str(man))
        for child in self.children:
            if child < 10000000:
                if man < 10000000:
                    outn3(fp,PERSOONURI + "I" + str(man),"schema:children",PERSOONURI + "I" + str(child))
                    outn3(fp,PERSOONURI + "I" + str(child),"schema:parent",PERSOONURI + "I" + str(man))
                if vrouw < 10000000:
                    outn3(fp,PERSOONURI + "I" + str(vrouw),"schema:children",PERSOONURI + "I" + str(child))
                    outn3(fp,PERSOONURI + "I" + str(child),"schema:parent",PERSOONURI + "I" + str(vrouw))

    def normalize(self,individuals):
        normchilds = []
        for child in self.children:
            normchild = individuals.normalize(child)
            if normchild not in normchilds:
                normchilds.append(normchild)
        self.children = normchilds
        
class Marriages:
    def __init__(self):
        self.lijst = {}          # double index containig Marriage() objects

    def add_marriage(self,man,vrouw,individuals,eventdate = None,eventplace = None):     # aktestring???
        man = individuals.normalize(man)
        vrouw = individuals.normalize(vrouw)
        if man not in self.lijst:
            self.lijst[man] = {}
        if vrouw not in self.lijst[man]:
            self.lijst[man][vrouw] = Marriage(eventdate,eventplace)
        else:
            self.lijst[man][vrouw].set_date_and_place(eventdate,eventplace)

    def add_child(self,man,vrouw,child,individuals):
        man = individuals.normalize(man)
        vrouw = individuals.normalize(vrouw)
        child = individuals.normalize(child)
        assert man in self.lijst,"geen huwelijk"
        assert vrouw in self.lijst[man],"bruid niet"
        self.lijst[man][vrouw].add_child(child)

    def get_export_csv_header_marriage(self):
        #print(self.lijst)
        return "Huwelijk,Echtgenoot,Echtgenote,Datum,Locatie id,Bron,Opmerking".split(",")
        #return ["Marriage", "Husband", "Wife", "Date", "Placeid", "Source", "Note"]
        

    def get_export_csv_header_children(self):
        return "Gezin,Kind".split(",")
        #return ["family", "child", "source", "note", "gender"]

    def export_csv(self,csvfile):
        writer = csv.DictWriter(csvfile, fieldnames=self.get_export_csv_header_marriage(),lineterminator='\n')
        writer.writeheader()
        for man in self.lijst:
            for vrouw in self.lijst[man]:
                self.lijst[man][vrouw].export_csv_marriage(writer,man,vrouw)
        csvfile.write('\n')
        writer = csv.DictWriter(csvfile, fieldnames=self.get_export_csv_header_children(),lineterminator='\n')
        writer.writeheader()
        for man in self.lijst:
            for vrouw in self.lijst[man]:
                self.lijst[man][vrouw].export_csv_children(writer)
        csvfile.write('\n')

    def export_lod(self,fp):
        for man in self.lijst:
            for vrouw in self.lijst[man]:
                self.lijst[man][vrouw].export_lod(fp,man,vrouw)

    def normalize(self,individuals):
        for man in self.lijst:
            for vrouw in self.lijst[man]:
                self.lijst[man][vrouw].normalize(individuals)
        
class Nodes:
    def __init__(self):
        self.individuals = Individuals()
        self.nodes = {}
        self.marriages = Marriages()
        self.individuals.load_persist_ids()
        #self.places = Places()

    def lees_koppelingen(self,koppelcursor):
        for row in koppelcursor.execute('SELECT rol,srcakte,dstnakte FROM koppel'):
            #print(row)
            # zoek/laad akte
            if row[2] not in self.nodes:
                a = data.akte.akte(row[2])
                a.load_from_string(preloadaktes[row[2]],row[2])
                self.nodes[row[2]] = Node(a,self.individuals)
            dstnakte = self.nodes[row[2]]
            if row[1] not in self.nodes:
                a = data.akte.akte(row[1])
                a.load_from_string(preloadaktes[row[1]],row[1])
                self.nodes[row[1]] = Node(a,self.individuals)
            srcakte = self.nodes[row[1]]

            srcgezin = srcakte.gezin
            if srcakte.eventtype == "Huwelijk":
                if row[0] == "Bruid":
                    srcgezin = srcakte.gezin2

            if dstnakte.eventtype == "Huwelijk":
                self.individuals.same_as(dstnakte.gezin.kind,srcgezin.vader)
                self.individuals.same_as(dstnakte.gezin2.kind,srcgezin.moeder)
            else:
                self.individuals.same_as(dstnakte.gezin.kind,srcgezin.kind)
                #print("same_as(",dstnakte.gezin.moeder,srcgezin.moeder,")")
                #print(self.individuals.lijst)
                self.individuals.same_as(dstnakte.gezin.moeder,srcgezin.moeder)
                self.individuals.same_as(dstnakte.gezin.vader,srcgezin.vader)

        for n in self.nodes:
            node = self.nodes[n]
            #print(n,node.eventtype)
            self.marriages.add_marriage(node.gezin.vader,node.gezin.moeder,self.individuals)
            self.marriages.add_child(node.gezin.vader,node.gezin.moeder,node.gezin.kind,self.individuals)
            if node.eventtype == "Huwelijk":    
                self.marriages.add_marriage(node.gezin2.vader,node.gezin2.moeder,self.individuals)
                self.marriages.add_child(node.gezin2.vader,node.gezin2.moeder,node.gezin2.kind,self.individuals)
                #print(node.eventdate,node.eventplace)
                self.marriages.add_marriage(node.gezin.kind,node.gezin2.kind,self.individuals, node.eventdate,node.eventplace)
        #print("done")

        self.individuals.renumber_ids()
        self.marriages.normalize(self.individuals)
        self.individuals.save_persist_ids()

print("Preloading akten")
#fp = open("bs1608.json","r")
#preloadaktes = json.load(fp)
#fp.close()
preload = data.akte.aktecache(cur)
preloadaktes = preload.aktes
cur.close()
print("Loaded")
nodes = Nodes()

koppel = sqlite3.connect('koppelmaster.db',uri=True)
koppelcursor = koppel.cursor()
nodes.lees_koppelingen(koppelcursor)
koppel.close()
places.save_persist_ids()

print("Unieke individuen:",nodes.individuals.count())
# renumber ?
# normalize alles ???
csvfile = open("allefriezen.csv","w")
writer = csv.DictWriter(csvfile,fieldnames=places.get_export_csv_header(),lineterminator='\n')
writer.writeheader()
places.export_csv_places(writer)
csvfile.write('\n')
nodes.individuals.export_to_csv(csvfile)
csvfile.write('\n')
nodes.marriages.export_csv(csvfile)
csvfile.close()

if True:
    fp = open("personen.nt","w")
    places.export_lod(fp)
    nodes.individuals.export_lod(fp)
    nodes.marriages.export_lod(fp)
    fp.close()
