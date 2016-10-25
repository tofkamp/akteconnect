# koppelstats.py - get some koppel db statistics
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

# koppel statistics
# max diepte
# verdeling van diepte
# aantal clusters
# max aantal akten in 1 cluster

import sqlite3

koppel = sqlite3.connect('koppelmaster.db',uri=True)
#koppel = sqlite3.connect('e:/koppelgonodes.db')
koppelcursor = koppel.cursor()

diepte = {}
maxdiepte = 0
maxdieptecount = 0
aantalkoppelingen = 0
for row in koppelcursor.execute("SELECT * FROM koppel"):
    # row[0] = rol
    # row[1] = src
    # row[2] = destn
    aantalkoppelingen += 1
    if not row[2] in diepte:
        diepte[row[2]] = 1
    if not row[1] in diepte:
        diepte[row[1]] = 1
    if diepte[row[1]] < diepte[row[2]] + 1:
        diepte[row[1]] = diepte[row[2]] + 1
    if maxdiepte == diepte[row[1]]:
        maxdieptecount += 1
    if maxdiepte < diepte[row[1]]:
        maxdieptecount = 1
        maxdiepte = diepte[row[1]]
print("Aantal koppelingen",aantalkoppelingen)
print("Aantal gekoppelde akten",len(diepte))
print("Max diepte",maxdiepte,"komt",maxdieptecount,"keer voor")

# clusters
# geef alle nodes een nummer
clusternr = 1
for i in diepte:
    diepte[i] = clusternr
    clusternr += 1
# verspreid het kleinste getal binnen het cluster van gekoppelde akten
modified = True
while modified:
    modified = False
    for row in koppelcursor.execute("SELECT * FROM koppel"):
        # row[0] = rol
        # row[1] = src
        # row[2] = destn
        if diepte[row[1]] < diepte[row[2]]:
            diepte[row[2]] = diepte[row[1]]
            modified = True
        if diepte[row[1]] > diepte[row[2]]:
            diepte[row[1]] = diepte[row[2]]
            modified = True
        
cluster_count = {}
for i in diepte:
    if not diepte[i] in cluster_count:
        cluster_count[diepte[i]] = 1
    else:
        cluster_count[diepte[i]] += 1
print("Aantal clusters",len(cluster_count))
maxclustercount = 0
for i in cluster_count:
    maxclustercount = max(maxclustercount,cluster_count[i])
print("Max aantal gekoppelde akten in 1 cluster",maxclustercount)
if False:
    # hoe vaak hebben we dat grootste cluster
    verzamelinggrootsteclusters = []
    for i in cluster_count:
        if cluster_count[i] == maxclustercount:
            verzamelinggrootsteclusters.append(i)
    # welke akten zitten er in dat cluster
    for i in verzamelinggrootsteclusters:
        print("Cluster",i,"bestaat uit de volgende akten:")
        komma = "("
        for j in diepte:
            if diepte[j] == i:
                print(komma+'"'+j+'"')
                komma = ","
    print(")")

koppel.close()
