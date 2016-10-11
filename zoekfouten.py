# zoekfouten.py - search for mistakes in the sqlite akte database
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

import re

import data.akte

roles = (
    "Bruid|291060"
    ,"Bruidegom|291072"
    ,"Kind|896211"
    ,"Moeder|1152313"
    ,"Moedervandebruid|258428"
    ,"Moedervandebruidegom|258408"
    ,"Overledene|835777"
    ,"Relatie|12797"
    ,"Vader|1139151"
    ,"Vadervandebruid|282489"
    ,"Vadervandebruidegom|282791"
    ,"other:Relatie|20307"
    ,"other:Relatiebruid|46"
    ,"other:Relatiebruidegom|83"
    )
out=open("fouten.txt","w")
conn = sqlite3.connect('e:/BurgelijkeStand1610.db')
#conn = sqlite3.connect('c:/akteconnect/BurgelijkeStand1610.db')
#conn = sqlite3.connect(':memory:')
fp = conn.cursor()
# select age,count(age) from aktepersoon group by age;
for row in fp.execute('select age,count(age) from aktepersoon group by age order by age'):
    a = row[0]
    b = row[1]
    if a == None:
        a = "None"
    if b == None:
        b = "None"
    out.write('"'+str(a)+'",'+str(b)+'\n')

    

if False:
    total = 0
    rollen = []
    for i in roles:
        r,c = i.split("|")
        print(r,c)
        total += int(c)
        rollen.append(r)
    print(total,rollen)

    for row in fp.execute('SELECT * FROM aktepersoon'):
        if row[5] not in rollen:
            print(row)
        if row[4] == "Jong\r\nJong":
            print(row)
    
achternamen = {}

for row in fp.execute('SELECT * FROM aktepersoon'):
    for name in (1,2,4):
        if row[name] and row[name].islower():
            if row[name] != "geen" and row[name] != "levenloos kind":
                if name == 1:
                    achternamen[row[0]] = "Voornaam "+row[name]
                if name == 2:
                    achternamen[row[0]] = "Patronym "+row[name]
                if name == 4:
                    achternamen[row[0]] = "Achternaam "+row[name]

if False:
    s="1 jaar en {} maand"
    for m in range(1,11):
        e = s.format(m)
        x = 'SELECT * FROM aktepersoon WHERE role = "Overledene" AND age = "{}"'.format(e)
        for row in fp.execute(x):
            print('https://www.allefriezen.nl/zoeken/deeds/'+row[0],e)
        s="1 jaar en {} maanden"

print("Preloading akten")
preload = data.aktecache.aktecache(fp)

for i in achternamen:
    a = data.akte.akte(i)
    a.load_from_string(preload.aktes[i],i)
    out.write("https://www.allefriezen.nl/zoeken/deeds/"+i+' '+a.eventtype+' '+achternamen[i]+'\n')

for i in preload.aktes:
    a = data.akte.akte(i)
    a.load_from_string(preload.aktes[i],i)
    for p in a.personen:
        if p.age:
            if p.age.endswith(' '):
                out.write("https://www.allefriezen.nl/zoeken/deeds/"+i+' '+a.eventtype+' "'+p.age+'"\n')

# check for only digits
getal = re.compile('^\d+$')
for i in preload.aktes:
    a = data.akte.akte(i)
    a.load_from_string(preload.aktes[i],i)
    for p in a.personen:
        if p.age:
            if getal.match(p.age):
                out.write("https://www.allefriezen.nl/zoeken/deeds/"+i+' '+a.eventtype+' "'+p.age+'"\n')


raar = "[]{}';><.,/?+=_)(*&^%$@!\\~`"
for c in raar:
    tel = 0
    for a in preload.aktes:
        tel += preload.aktes[a].count(c)
    if tel > 0:
        out.write(c+' '+str(tel)+'\n')
        if tel < 15:
            for a in preload.aktes:
                if preload.aktes[a].count(c) > 0:
                    out.write('https://www.allefriezen.nl/zoeken/deeds/'+a+'\n')

for a in preload.aktes:
    if preload.aktes[a].count('(') != preload.aktes[a].count(')'):
        out.write('https://www.allefriezen.nl/zoeken/deeds/'+a+" niet evenveel openen als sluiten\n")
#print(d,e)
conn.close()
#print(len(achternamen))


# zoek achternamren
out.close()
