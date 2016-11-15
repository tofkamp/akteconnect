# allefriezen naar sqlite.py - Convert A2A dump to relational sqlite3 database
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


import xml.etree.ElementTree as ET
import time
import sqlite3
baseurl = "http://data.kultuer.frl/allefriezen/"
# 2016 09 2027218 akten

def stripnamespace(tag):
    # strip any {namespace url} from tag
    if tag.find("}") >= 1:
        namespace_uri, tag = tag.split("}", 1)
    return tag

def getelement(elem,relpath):
    dirs = relpath.split('|')
    for tag in dirs:
        if tag.startswith('@'):
            return elem.get(tag[1::])
        x = elem.findall(tag)
        if len(x) == 0:
            return None
        if len(x) > 1:
            return None
        elem = x[0]
    return elem.text

idsdone = {}        # array van alle akte ids die we al gehad hebben
                    # dit is nodig omdat er tijdens de dump modificaties plaats vinden, waardoor akten twee keer in de dump voorkomen
                    # programma foutje van picturea
                    
def record(elem):
    global idsdone
    eventtype = getelement(elem,"{http://www.openarchives.org/OAI/2.0/}metadata|{http://Mindbus.nl/A2A}A2A|{http://Mindbus.nl/A2A}Event|{http://Mindbus.nl/A2A}EventType")
    if False:
        source = elem.find("{http://www.openarchives.org/OAI/2.0/}metadata").find("{http://Mindbus.nl/A2A}A2A").find("{http://Mindbus.nl/A2A}Source")
        #source = getelement(elem,"{http://www.openarchives.org/OAI/2.0/}metadata|{http://Mindbus.nl/A2A}A2A|{http://Mindbus.nl/A2A}Source")
        if source:
            for remark in source.findall("{http://Mindbus.nl/A2A}SourceRemark"):
                k = remark.get("Key")
                v = getelement(remark,"{http://Mindbus.nl/A2A}Value")
                if k == "AkteSoort":
                    #print(v)
                    eventtype = v
       
    subject = getelement(elem,"{http://www.openarchives.org/OAI/2.0/}header|{http://www.openarchives.org/OAI/2.0/}identifier")
    if subject in idsdone:    # hebben we deze akte al gehad (foutje in dump prog van picturea)
        # zo ja, gooi eerdere akte weg
        fp.execute('''DELETE from akte where recordid = ?''',(subject,))
        fp.execute('''DELETE from aktepersoon where recordid = ?''',(subject,))
        print('Akte',subject,'staat er meer dan 1 keer in de dump')
    else:
        idsdone[subject] = 1
        
    eventplace = getelement(elem,"{http://www.openarchives.org/OAI/2.0/}metadata|{http://Mindbus.nl/A2A}A2A|{http://Mindbus.nl/A2A}Event|{http://Mindbus.nl/A2A}EventPlace|{http://Mindbus.nl/A2A}Place")
    dag = getelement(elem,"{http://www.openarchives.org/OAI/2.0/}metadata|{http://Mindbus.nl/A2A}A2A|{http://Mindbus.nl/A2A}Event|{http://Mindbus.nl/A2A}EventDate|{http://Mindbus.nl/A2A}Day")
    maand = getelement(elem,"{http://www.openarchives.org/OAI/2.0/}metadata|{http://Mindbus.nl/A2A}A2A|{http://Mindbus.nl/A2A}Event|{http://Mindbus.nl/A2A}EventDate|{http://Mindbus.nl/A2A}Month")
    jaar = getelement(elem,"{http://www.openarchives.org/OAI/2.0/}metadata|{http://Mindbus.nl/A2A}A2A|{http://Mindbus.nl/A2A}Event|{http://Mindbus.nl/A2A}EventDate|{http://Mindbus.nl/A2A}Year")
    eventdate=""
    if jaar:
        eventdate = str(jaar)
        if maand:
            eventdate += "-"+str(maand)
            if dag:
                eventdate += "-"+str(dag)
    #print(subject)
    # zoek personen
    personen = {}
    for per in elem.findall("{http://www.openarchives.org/OAI/2.0/}metadata/{http://Mindbus.nl/A2A}A2A/{http://Mindbus.nl/A2A}Person"):
        personen[per.get("pid")] = Person(per)
    # zoek bijbehorende rol bij persoon
    for rel in elem.findall("{http://www.openarchives.org/OAI/2.0/}metadata/{http://Mindbus.nl/A2A}A2A/{http://Mindbus.nl/A2A}RelationEP"):
        #print(getelement(rel,"{http://Mindbus.nl/A2A}PersonKeyRef"))
        #print(getelement(rel,"{http://Mindbus.nl/A2A}RelationType").replace(" ",""))
        i = getelement(rel,"{http://Mindbus.nl/A2A}PersonKeyRef")
        t = getelement(rel,"{http://Mindbus.nl/A2A}RelationType").replace(" ","")
        (personen[i]).reltype = t
        if t == "Overledene":
            personen[i].deathdate = eventdate
            #personen[i].deathplace = eventplace
        #personen[getelement(rel,"{http://Mindbus.nl/A2A}PersonKeyRef")].reltype = getelement(rel,"{http://Mindbus.nl/A2A}RelationType").replace(" ","")
    for rel in elem.findall("{http://www.openarchives.org/OAI/2.0/}metadata/{http://Mindbus.nl/A2A}A2A/{http://Mindbus.nl/A2A}RelationPP"):
        #print(getelement(rel,"{http://Mindbus.nl/A2A}PersonKeyRef"))
        #print(getelement(rel,"{http://Mindbus.nl/A2A}RelationType").replace(" ",""))
        p1 = None
        if rel[0].tag == "{http://Mindbus.nl/A2A}PersonKeyRef":
            p1 = rel[0].text
        p2 = None
        if rel[1].tag == "{http://Mindbus.nl/A2A}PersonKeyRef":
            p2 = rel[1].text
        t = getelement(rel,"{http://Mindbus.nl/A2A}RelationType").replace(" ","")
        if p1 and p2:
            if personen[p2].reltype == "Overledene":
                personen[p1].reltype = t
            elif personen[p1].reltype == "Overledene":
                personen[p2].reltype = t
            else:
                print("wel keyrefs maar geen overledene",subject)
        else:
            print("Vreemd https://www.allefriezen.nl/zoeken/deeds/"+subject)
            print(personen[p1],personen[p2],personen[p1].reltype,personen[p2].reltype)
            #if subject == "06394230-a058-c6cf-58e1-62c73d6e3d74":
            #    ET.dump(elem)
        #personen[getelement(rel,"{http://Mindbus.nl/A2A}PersonKeyRef")].reltype = getelement(rel,"{http://Mindbus.nl/A2A}RelationType").replace(" ","")

    persql = []
    for p in personen:
        #print(p,personen[p].reltype,personen[p])
        persql.append((subject,personen[p].givenname,personen[p].patroniem,personen[p].prefixlastname,personen[p].lastname,
                       personen[p].reltype,p,personen[p].age,personen[p].birthdate,personen[p].birthplace,personen[p].deathdate,personen[p].deathplace,
                       personen[p].gender,personen[p].residence,personen[p].profession))
    #print(persql)
    fp.execute('''INSERT INTO akte(recordid,eventtype,eventdate,eventplace)
                  VALUES(?,?,?,?)''',(subject,eventtype,eventdate,eventplace))
    
    fp.executemany('''INSERT INTO aktepersoon(recordid,firstname,patronym,prefixlastname,lastname,role,personid,age,birthdate,birthplace,deathdate,deathplace,gender,residence,profession)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?, ?,?,?,?)''',persql)
    return True

class Person:
    def __init__(self,elem):
        self.givenname = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}PersonNameFirstName")
        self.patroniem = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}PersonNamePatronym")
        self.prefixlastname = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}PersonNamePrefixLastName")
        self.lastname = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}PersonNameLastName")
        self.age = getelement(elem,"{http://Mindbus.nl/A2A}Age|{http://Mindbus.nl/A2A}PersonAgeLiteral")
        self.birthplace = getelement(elem,"{http://Mindbus.nl/A2A}BirthPlace|{http://Mindbus.nl/A2A}Place")
        self.deathplace = getelement(elem,"{http://Mindbus.nl/A2A}DeathPlace|{http://Mindbus.nl/A2A}Place")
        self.deathdate = None
        self.residence = getelement(elem,"{http://Mindbus.nl/A2A}Residence|{http://Mindbus.nl/A2A}Place")
        self.profession = getelement(elem,"{http://Mindbus.nl/A2A}Profession")
        self.gender = getelement(elem,"{http://Mindbus.nl/A2A}Gender")
        dag = getelement(elem,"{http://Mindbus.nl/A2A}BirthDate|{http://Mindbus.nl/A2A}Day")
        maand = getelement(elem,"{http://Mindbus.nl/A2A}BirthDate|{http://Mindbus.nl/A2A}Month")
        jaar = getelement(elem,"{http://Mindbus.nl/A2A}BirthDate|{http://Mindbus.nl/A2A}Year")
        self.birthdate=""
        if jaar:
            self.birthdate = str(jaar)
            if maand:
                self.birthdate += "-"+str(maand)
                if dag:
                    self.birthdate += "-"+str(dag)
        #self.deathdate = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}Age|{http://Mindbus.nl/A2A}PersonAgeLiteral")
        self.reltype = None

    def __str__(self):
        #if self.reltype:
        #    ret = self.reltype+":"
        #else:
        ret = ""
        if self.givenname:
            ret += self.givenname
        if self.patroniem:
            ret += " "+self.patroniem
        if self.prefixlastname:
            ret += " "+self.prefixlastname
        if self.lastname:
            ret += " "+self.lastname
        if ret.startswith(" "):
            return ret[1::]
        return ret

    ### vergelijk functie ???
    def _1_eq__(self,other):
        if self.givenname == other.givenname:
            if self.patroniem == other.patroniem:
                if self.prefixlastname == other.prefixlastname:
                    return self.lastname == other.lastname
        return False

files = (
	"frl_a2a_bs_o-201611.xml"
	,"frl_a2a_bs_h-201611.xml"
	,"frl_a2a_bs_g-201611.xml")

conn = sqlite3.connect('e:/BurgelijkeStand1611.db')
#conn = sqlite3.connect(':memory:')
fp = conn.cursor()

# Create table
fp.execute('''DROP TABLE IF EXISTS akte''')
fp.execute('''DROP TABLE IF EXISTS aktepersoon''')

# Create table
fp.execute('''CREATE TABLE akte
             (recordid varchar(36) primary key, eventtype text, eventdate date, eventplace text)''')
fp.execute('''CREATE TABLE aktepersoon
             (recordid varchar(36), firstname text, patronym text, prefixlastname text, lastname text,
             role text, personid text, age text, birthdate date, birthplace text, deathdate date, deathplace text, gender text, residence text, profession text )''')
fp.execute('''PRAGMA synchronous=OFF''')
fp.execute('''PRAGMA journal_mode=OFF''')

for file in files:
#for file in {"bal2.xml"}:
    print("Bezig met",file)
    starttime = time.time() 
    recordcount = 0
    context = ET.iterparse('C:/users/tjibbe/Desktop/resources/'+file)
    #context = ET.iterparse('resources/'+file)
    # turn it into an iterator
    context = iter(context)
    for event, elem in context:
        #print(event,elem.tag)
        tag = stripnamespace(elem.tag)
        if event == 'end' and tag == "record":
            recordcount += 1
            ret = record(elem)
            if ret:
                elem.clear()
    #fp.close()
    endtime = time.time() 
    print(file,recordcount,endtime - starttime,recordcount /(endtime - starttime))

# Save (commit) the changes
conn.commit()
for row in fp.execute('SELECT count(*) FROM aktepersoon'):
    print(row[0])    #5740379 in 11-2016
for row in fp.execute('SELECT count(*) FROM akte'):
    print(row[0])    #2027215 in 11-2016

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()
