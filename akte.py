# akte.py - library to do something with akte objects
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

class aktepersoon:
    def __init__(self,akteid = None,persoonid = None):
        self.akteid = akteid
        self.persoonid = persoonid
        self.firstname = None
        self.patronym = None
        self.prefixlastname = None
        self.lastname = None
        self.role = None
        self.age = None
        self.birthdate = None
        self.birthplace = None
        self.deathdate = None
        self.deathplace = None
        self.gender = None
        self.residence = None
        self.profession = None

    def from_sql_result(self,result):       # fromsqlresult
        # from a sql select * from aktepersoon where recordid = ?
        self.akteid = result[0]
        self.firstname = result[1]
        self.patronym = result[2]
        self.prefixlastname = result[3]
        self.lastname = result[4]
        self.role = result[5]
        self.persoonid = result[6]
        self.age = result[7]
        self.birthdate = result[8]
        self.birthplace = result[9]
        self.deathdate = result[10]
        self.deathplace = result[11]
        self.gender = result[12]
        self.residence = result[13]
        self.profession = result[14]
        
    def merge(self,other):
        """ merge two aktepersonen informatie
        """
        if not self.firstname and other.firstname:
            self.firstname = other.firstname
        if not self.patronym and other.patronym:
            self.patronym = other.patronym
        if not self.prefixlastname and other.prefixlastname:
            self.prefixlastname = other.prefixlastname
        if not self.lastname and other.lastname:
            self.lastname = other.lastname
        if not self.age and other.age:
            self.age = other.age
        if not self.birthdate and other.birthdate:
            self.birthdate = other.birthdate
        if not self.birthplace and other.birthplace:
            self.birthplace = other.birthplace
        if not self.deathdate and other.deathdate:
            self.deathdate = other.deathdate
        if not self.deathplace and other.deathplace:
            self.deathplace = other.deathplace
        if not self.gender and other.gender:
            self.gender = other.gender
        if not self.residence and other.residence:
            self.residence = other.residence
        if not self.profession and other.profession:
            self.profession = other.profession

    def create_table(self,conn):
        conn.execute('''DROP TABLE IF EXISTS aktepersoon''')
        conn.execute('''CREATE TABLE aktepersoon
             (recordid varchar(36), firstname text, patronym text, prefixlastname text, lastname text,
             role text, personid text, age text, birthdate date, birthplace text, deathdate date, deathplace text, gender text, residence text, profession text )''')
        
    def __str__(self):
        return self.to_string()

    def to_string(self,useage = True):
        """ make readable string from person
        if useage is True, use the age when no birthdate is known
        """
        if False: # for unicode fonts
            BIRTHSIGN = '\u2600'        # 2600=sun 
            DEATHSIGN = '\u2620'        # 2620=skull of 2670=cross
            MALESIGN = '\u2642'         # http://www.utf8-chartable.de/unicode-utf8-table.pl?start=9728
            FEMALESIGN = '\u2640'
            AGESIGN = '\u2248'
        else:  # for ascii fonts
            BIRTHSIGN = ''
            DEATHSIGN = ''
            MALESIGN = ''
            FEMALESIGN = ''
            AGESIGN = ''

        if self.firstname:
            naam = self.firstname
        else:
            naam = ""
        if self.patronym:
            naam += " " + self.patronym
        if self.prefixlastname:
            naam += " " + self.prefixlastname
        if self.lastname:
            naam += " " + self.lastname
        bdenp = ""   # birth date and place
        if self.birthdate:
            if self.birthplace:
                bdenp += BIRTHSIGN+self.birthdate+" "+self.birthplace
            else:
                bdenp += BIRTHSIGN+self.birthdate
        elif useage and self.age:
            if self.birthplace:
                bdenp += AGESIGN+self.age+" "+self.birthplace
            else:
                bdenp += AGESIGN+self.age
        ddenp = ""   # death date and place
        if self.deathdate:
            if self.deathplace:
                ddenp += DEATHSIGN+self.deathdate+" "+self.deathplace
            else:
                ddenp += DEATHSIGN+self.deathdate
        # add birth and death date and place to name
        if bdenp != "":
            if ddenp != "":
                naam += " ("+bdenp+","+ddenp+")"
            else:
                naam += " ("+bdenp+")"
        elif ddenp != "":
            naam += " ("+ddenp+")"
        # strip leading space
        if naam.startswith(" "):
            naam = naam[1::]
        if self.gender == "Man":
            naam = MALESIGN + naam
        if self.gender == "Vrouw":
            naam = FEMALESIGN + naam
        return naam
    
    def __html__(self):
        # make a <a href=...> string
        return '<a href="' + self.__url__() +'">'+str(self)+'</A>'

    def __url__(self):
        return 'https://www.allefriezen.nl/zoeken/deeds/'+ self.akteid

    def to_gedcom(self):
        def to_gedcom_date(date):
            d = date.split("-",2)
            maanden = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
            return d[2] + " " + maanden[int(d[1])-1] + " " + d[0]

        ret = {}
        if self.firstname:
            voornaam = self.firstname
        else:
            voornaam = ""
        if self.patronym:
            voornaam += " " + self.patronym
        if voornaam.startswith(" "):
            voornaam = voornaam[1::]
        if voornaam:
            ret["GIVN"] = voornaam
        if self.prefixlastname:
            achternaam = self.prefixlastname
            ret["SPFX"] = self.prefixlastname
        else:
            achternaam = ""
        if self.lastname:
            achternaam += " " + self.lastname
            ret["SURN"] = self.lastname
        if achternaam.startswith(" "):
            achternaam = achternaam[1::]
        ret = { "NAME " + voornaam + ' /' + achternaam + '/' : ret }
        # is bovenstaande gedcom 5.5.1 (uit gramps) ? anders:
        #ret[ "NAME" ] = voornaam + ' /' + achternaam + '/'
        
        birth = {}
        if self.birthdate:
            birth["DATE"] = to_gedcom_date(self.birthdate)
        if self.birthplace:
            birth["PLAC"] = self.birthplace
        if birth:
            ret["BIRT"] = birth 

        death = {}
        if self.deathdate:
            death["DATE"] = to_gedcom_date(self.deathdate)
        if self.deathplace:
            death["PLAC"] = self.deathplace
        if death:
            ret["DEAT"] = death

        if self.gender:
            if self.gender == "Vrouw":
                ret["SEX"] = "F"
            if self.gender == "Man":
                ret["SEX"] = "M"
        #self.residence = result[13]
        #self.profession = result[14]
        return ret
    
class akte:
    def __init__(self,akte_id = None):
        self.akte_id = akte_id
        self.personen = []
        self.eventtype = None
        self.eventdate = None
        self.eventplace = None

    def create_table(self,conn):
        conn.execute('''DROP TABLE IF EXISTS akte''')
        conn.execute('''CREATE TABLE akte
             (recordid varchar(36) primary key, eventtype text, eventdate date, eventplace text)''')
        
    def load_from_sql(self, conn, akteid):
        """
        load a akte from sql with akteid.

        @ivar conn: sqlite3 connection
        @ivar akteid: which akteid to load
        """
        conn.execute('''SELECT * FROM akte WHERE recordid=?''', [akteid])
        user = conn.fetchone()
        if user:
            self.eventtype = user[1]
            self.eventdate = user[2]
            self.eventplace = user[3]
            self.recordid = akteid
            for row in conn.execute('SELECT * FROM aktepersoon WHERE recordid=?''', [akteid]):
                p = aktepersoon()
                p.from_sql_result(row)
                self.personen.append(p)
    
    def load_from_string(self,string,akteid):
        """
        load a akte from a string

        string: the string records seperated by "#" and field by "|"
        akteid: the akteid
        """
        records = string.split('#')
        user = records[0].split('|')
        self.eventtype = user[0]
        self.eventdate = user[1]
        self.eventplace = user[2]
        self.recordid = akteid
        for record in records[1::]:
            row = [akteid] + record.split('|')
            p = aktepersoon()
            p.from_sql_result(row)
            self.personen.append(p)

    def find_person_with_role(self,role):
        """
        Find a person on a akte with this specific role

        @ivar role: The role of the person
        """

        for p in self.personen:
            if p.role == role:
                return p
        return None
    
    def find_all_persons_with_role(self,role):
        """
        Find all persons on a akte with this specific role

        @ivar role: The role of the person
        return array of persons with this role
        """
        ret = []
        for p in self.personen:
            if p.role == role:
                ret.append(p)
        return ret

    def __url__(self):
        return 'https://www.allefriezen.nl/zoeken/deeds/'+ self.akte_id

    def to_string(self,longversion = True):
        """
        Create printable string from an akte

        if longversion is True, put eventtype in header text
        return array of strings (header, info[,info])
        """
        if False:
            RELATIVESIGN = '\u2514'
            FAMILYSIGN = '\u2558'       # char 2517 is de dikke versie
        else:
            RELATIVESIGN = "-"
            FAMILYSIGN = "="
        if self.eventtype == "Geboorte":
            kind = self.find_person_with_role("Kind")
            vader = self.find_person_with_role("Vader")
            moeder = self.find_person_with_role("Moeder")
            if longversion:
                header = "Geboorte van " + kind.to_string()
            else:
                header = kind.to_string()
            if self.eventdate:
                header += " op "+self.eventdate
            if self.eventplace:
                header += " te "+self.eventplace
            subinfo = ""
            if vader:
                subinfo += FAMILYSIGN + vader.to_string() + '\n'
            if moeder:
                subinfo += FAMILYSIGN + moeder.to_string() + '\n'
            return [header,subinfo]
        if self.eventtype == "Overlijden":
            overledene = self.find_person_with_role("Overledene")
            vader = self.find_person_with_role("Vader")
            moeder = self.find_person_with_role("Moeder")
            if longversion:
                header = "Overlijden van " + overledene.to_string()
            else:
                header = overledene.to_string()
            if self.eventdate:
                header += " op "+self.eventdate
            if self.eventplace:
                header += " te "+self.eventplace
            subinfo = ""
            if vader:
                subinfo += FAMILYSIGN + vader.to_string() + '\n'
            if moeder:
                subinfo += FAMILYSIGN + moeder.to_string() + '\n'
            relaties = self.find_all_persons_with_role("Relatie")
            for relatie in relaties:
                subinfo += RELATIVESIGN + relatie.to_string() + '\n'
            # het volgende is een fout in de database
            relaties = self.find_all_persons_with_role("other:Relatie")
            for relatie in relaties:
                subinfo += RELATIVESIGN + relatie.to_string() + '\n'
            
            return [header,subinfo]
        if self.eventtype == "Huwelijk":
            bruidegom = self.find_person_with_role("Bruidegom")
            bruid = self.find_person_with_role("Bruid")
            vadervandebruidegom = self.find_person_with_role("Vadervandebruidegom")
            moedervandebruidegom = self.find_person_with_role("Moedervandebruidegom")
            vadervandebruid = self.find_person_with_role("Vadervandebruid")
            moedervandebruid = self.find_person_with_role("Moedervandebruid")
            if longversion:
                header = "Huwelijk van " + bruidegom.to_string() + " met " + bruid.to_string()
            else:
                header = bruidegom.to_string() + " & " + bruid.to_string()
            if self.eventdate:
                header += " op "+self.eventdate
            if self.eventplace:
                header += " te "+self.eventplace
                
            subinfobruidegom = ""
            if vadervandebruidegom:
                subinfobruidegom += FAMILYSIGN + vadervandebruidegom.to_string() + '\n'
            if moedervandebruidegom:
                subinfobruidegom += FAMILYSIGN + moedervandebruidegom.to_string() + '\n'
            kinderen = self.find_all_persons_with_role("Kind")
            for kind in kinderen:
                subinfobruidegom += FAMILYSIGN + kind.to_string() + '\n'
            relaties = self.find_all_persons_with_role("other:Relatiebruidegom")
            for relatie in relaties:
                subinfobruidegom += RELATIONSIGN + relatie.to_string() + '\n'

            subinfobruid = ""
            if vadervandebruid:
                subinfobruid += FAMILYSIGN + vadervandebruid.to_string() + '\n'
            if moedervandebruid:
                subinfobruid += FAMILYSIGN + moedervandebruid.to_string() + '\n'
            relaties = self.find_all_persons_with_role("other:Relatiebruid")
            for relatie in relaties:
                subinfobruid += RELATIONSIGN + relatie.to_string() + '\n'
                
            return [header,subinfobruidegom,subinfobruid]
        header = "UNKNOWN "+self.eventtype
        if self.eventdate:
            header += " op "+self.eventdate
        if self.eventplace:
            header += " te "+self.eventplace
        return [header,""]

class aktecache:
    def __init__(self,cur):
        self.aktes = {}

        cur.execute('''SELECT * FROM akte''')
        for row in cur:
            # select from personakte bla
            ret = row[1]
            for i in row[2::]:
                if i:
                    ret += '|' + str(i)
                else:
                    ret += '|'
            self.aktes[row[0]] = ret

        cur.execute('''SELECT * FROM aktepersoon''')
        for row in cur:
            if row[1]:
                ret = row[1]
            else:
                ret = ""
            for i in row[2::]:
                if i:
                    ret += '|' + str(i)
                else:
                    ret += '|'
            self.aktes[row[0]] += "#" + ret

    def flush(self):
        self.aktes = {}
