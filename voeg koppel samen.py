# voeg koppel samen.py - merge two koppel databases together
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

# read master database
koppel = sqlite3.connect('koppel.db')
koppelcursor = koppel.cursor()

koppels = {}
for row in koppelcursor.execute('SELECT rol,srcakte,dstnakte,wie,timestamp FROM koppel'):
    koppels[(row[0],row[1])] = (row[2],row[3],row[4])

# read other
#kopsamen = sqlite3.connect('e:/akteconnect/koppel.db')
#kopsamen = sqlite3.connect('e:/akteconnect/koppeltr10038.db')
kopsamen = sqlite3.connect('koppeljan2.db')
kopsamcur = kopsamen.cursor()
replacecount = 0
doublecount = 0
newcount = 0
tooold = 0
for row in kopsamcur.execute('SELECT rol,srcakte,dstnakte,wie,timestamp FROM koppel'):
    index = (row[0],row[1])
    if index in koppels:
        if koppels[index][0] == row[2]:
            # connection is already in db
            doublecount += 1
        else:
            # replace
            if row[4] > koppels[index][2]:
                replacecount += 1
                koppelcursor.execute('''INSERT OR REPLACE INTO koppel(rol,srcakte,dstnakte,wie,timestamp) values(?,?,?,?,?)''',row)
            else:
                tooold += 1
    else:
        newcount += 1
        koppelcursor.execute('''INSERT OR REPLACE INTO koppel(rol,srcakte,dstnakte,wie,timestamp) values(?,?,?,?,?)''',row)
        #print("https://www.allefriezen.nl/zoeken/deeds/"+row[1],"https://www.allefriezen.nl/zoeken/deeds/"+row[2])
        
print("Double",doublecount)
print("Replaced",replacecount)
print("Too old to replace",tooold)
print("New",newcount)
kopsamen.close()

# write result

koppel.commit()
koppel.close()
