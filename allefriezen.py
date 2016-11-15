# allefriezen.py - convert A2A dumps to LOD
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

# unicode omzetten
# https://wiki.python.org/moin/UnicodeEncodeError


# thing to do
# zoek naam op tagnaam en niet een index
# naar uri's ipv literals
# in een class stoppen
# controleer alle andere a2a bestanden op structuur
# voeg alle a2a velden toe
# meer commentaar
# ipv index gebruiken, doe iets met namen en zoeken eg. getattribuut() maar dan voor xml tags

#http://effbot.org/zone/element.htm
# het volgende in een aparte class module ?
#========== test -------------
XMLstruct = {
#list Person Predicates = Gender,Place,Personpid,PersonAgeLiteral,PersonNameFirstName,PersonNamePrefixLastName,PersonNameLastName,PersonNamePatronym,Deprecated tag = []
             "Person" : {
               "PersonRemark" : {
                 "Value" : "schema:description"
               }
               ,"Profession" : "schema:jobTitle"
               ,"PersonName" : {
                 "PersonNamePrefixLastName" : "vocab:personNamePrefixLastName"
                 ,"PersonNamePatronym" : "schema:additionalName"
                 ,"PersonNameLastName" : "schema:familyName"
                 ,"PersonNameFirstName" : "schema:givenName"
               }
               ,"Residence" : {
                 "Place" : "schema:homeLocation"
               }
               ,"BirthDate" : {
                 "Day" : "vocab:birthDay"
                 ,"Year" : "vocab:birthYear"
                 ,"Month" : "vocab:birthMonth"
               }
               ,"BirthPlace" : {
                 "Place" : "birthPlace|schema:birthPlace"
               }
               ,"Age" : {
                 "PersonAgeLiteral" : "foaf:age"
                }
               #,"Gender" : "schema:gender"
             }
#list RelationEP Predicates = EventKeyRef,PersonKeyRef,RelationType,Deprecated tag = []
#             ,"RelationEP" : {
#               "RelationType" : "a2a:RelationType"
#               ,"PersonKeyRef" : "a2a:PersonKeyRef"
#               ,"EventKeyRef" : "a2a:EventKeyRef"
#             }
#list RelationPP Predicates = RelationType,Deprecated tag = []
#             # geen idee wat ik hier mee moet
#             ,"RelationPP" : {
#               "RelationType" : "a2a:RelationType"
#             }
#list Scan Predicates = UriPreview,Uri,OrderSequenceNumber,UriViewer,Deprecated tag = []
                 ,"Scan" : {
                   "UriPreview" : "foaf:thumbnail"
                   ,"UriViewer" : "vocab:uriViewer"
                   ,"Uri" : "foaf:Image"
                   #,"OrderSequenceNumber" : "OrderSequenceNumber"
                 }
}

baseurl = "http://data.kultuer.frl/allefriezen/"

def stripnamespace(tag):
    # strip any {namespace url} from tag
    if tag.find("}") >= 1:
        namespace_uri, tag = tag.split("}", 1)
    return tag

def ExtractAlphanumeric(InputString):
    from string import ascii_letters, digits
    return "".join([ch for ch in InputString if ch in (ascii_letters + digits)])

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

def outn3(subject,predicate,obj):
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
    fp.write('{} {} {} .\r\n'.format(subject,predicate,obj).encode('utf-8'))


def ToRDF(tree,elem,subject):
    # doe iets met attributes
    # doe iets met tags
    for child in elem:
        tag = stripnamespace(child.tag)
        #print("child ",tag)
        if tag in tree:
            if type(tree[tag]) is str:
                if '|' in tree[tag]:   # is a type specified ?
                    pre,tiepe = tree[tag].split('|',1)
                    sub = baseurl+pre+'/'+ExtractAlphanumeric(child.text).lower()
                    outn3(sub,"rdfs:type",tiepe)
                    outn3(sub,"schema:label",child.text)
                    outn3(subject,"schema:location",sub)
                else:
                    outn3(subject,tree[tag],child.text)
                #print('<{}>\t{}\t"{}" .'.format(subject,tree[tag],child.text))
            elif type(tree[tag]) is dict:
                ToRDF(tree[tag],child,subject)
            elif type(tree[tag]).__name__ == "function":    # should be "is function", but that does not work
                tree[tag](tree[tag],child,subject)
    return False

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

def record(tree,elem,parentsubject):
    #recordcount = recordcount + 1
    #subject = parentsubject + elem['header']['{http://Mindbus.nl/A2A}identifier'].text + '/'
    #subject = parentsubject + elem[0][0].text
    #print(elem)
    #print(elem[0])
    #print(elem[0][0])
    subject = parentsubject + getelement(elem,"{http://www.openarchives.org/OAI/2.0/}header|{http://www.openarchives.org/OAI/2.0/}identifier")
    outn3(subject,"schema:url","https://allefriezen.nl/zoeken/deeds/"+elem[0][0].text)
    outn3(subject,"rdfs:class",baseurl + "Record")
    ToRDF(tree,elem,subject)
    return True

def Person(tree,elem,parentsubject):
    #personcount += 1
    #subject = parentsubject + '/' + elem.attrib['pid']
    subject = baseurl + elem.attrib['pid'].replace(':','')
    #outn3(parentsubject,"dcterms:isReferencedBy",subject)
    outn3(subject,"rdfs:class","vocab:Person")

    t = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}PersonNameFirstName")
    if t:
        label = t
    else:
        label = ""
    t = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}PersonNamePatronym")
    if t:
        label += " " + t
    t = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}PersonNamePrefixLastName")
    if t:
        label += " " + t
    t = getelement(elem,"{http://Mindbus.nl/A2A}PersonName|{http://Mindbus.nl/A2A}PersonNameLastName")
    if t:
        label += " " + t
    if label.startswith(" "):
        outn3(subject,"rdfs:label",label[1::])
    else:
        outn3(subject,"rdfs:label",label)
    t = getelement(elem,"{http://Mindbus.nl/A2A}Gender")
    if t:
        if t == "Man":
            outn3(subject,"schema:gender","schema:Male")
        elif t == "Vrouw":
            outn3(subject,"schema:gender","schema:Female")
        else:
            outn3(subject,"schema:gender",t)
        
    ToRDF(XMLstruct["Person"],elem,subject)
    return True

def Scan(tree,elem,parentsubject):
    #a2a:OrderSequenceNumber
    #subject = parentsubject + '/' + elem[0].text
    subject = parentsubject
    #outn3(subject,"rdfs:class","schema:CreativeWork")
    #outn3(subject,"rdfs:class","vocab:Scan")
    #outn3(subject,"dcterms:isPartOf",parentsubject)
    # schema.org/Image ?
    ToRDF(XMLstruct["Scan"],elem,subject)
    return True

def RelationEP(tree,elem,parentsubject):
    #PersonKeyRef
    #subject = parentsubject + "/" + elem[0].text     # person naar akte of vv
    subject = baseurl + elem[0].text.replace(':','')     # person naar akte of vv
    #outn3(subject,"vocab:"+elem[2].text.replace(" ",""),parentsubject)    # PersonKeyRef "rol" akte
    outn3(subject,"vocab:"+getelement(elem,"{http://Mindbus.nl/A2A}RelationType").replace(" ",""),parentsubject)    # PersonKeyRef "rol" akte
    #ToRDF(XMLstruct["RelationEP"],elem,subject)
    return True

#<a2a:RelationPP><a2a:PersonKeyRef>Person3</a2a:PersonKeyRef><a2a:PersonKeyRef>Person2</a2a:PersonKeyRef><a2a:RelationType>other:Relatie</a2a:RelationType></a2a:RelationPP>
def RelationPP(tree,elem,parentsubject):
    #PersonKeyRef
    #subject = parentsubject + elem[0].text     # person naar akte of vv
    #outn3(subject,elem[0].text.replace(" ",""),parentsubject)    # PersonKeyRef "rol" akte
    #ToRDF(XMLstruct["RelationPP"],elem,subject)
    return True

def Concept(tree,elem,parentsubject):
    #print(elem)
    tag = stripnamespace(elem.tag)
    sub = baseurl+tag+'/'+ExtractAlphanumeric(elem.text).lower()
    outn3(sub,"rdfs:type","skos:Concept")
    outn3(sub,"skos:inSchema",baseurl + tag)
    outn3(sub,"schema:label",elem.text)
    outn3(parentsubject,"dcterms:subject",sub)
    return True


#list record Predicates = InstitutionName,Book,SourceDateDay,SourceDateMonth,From,SourcePlacePlace,EventDateDay,datestamp,Key,Value,To,EventDateYear,EventDateMonth,EventType,SourceLastChangeDate,eid,DocumentNumber,RecordGUID,SourceDateYear,SourceReferencePlace,Archive,Version,SourceType,identifier,Deprecated tag = ['Place', 'Day', 'Month', 'Year']
topXMLstruct = {"record" : {
         "header" : {
           "datestamp" : "vocab:datestamp"
           #,"identifier" : "identifier"
         }
         ,"metadata" : {
           "A2A" : {
               "Person" : Person,
               "RelationEP" : RelationEP,
               "RelationPP" : RelationPP,
             "Event" : {
               "EventDate" : {
                 "Day" : "vocab:eventDateDay"
                 ,"Month" : "vocab:eventDateMonth"
                 ,"Year" : "vocab:eventDateYear"
               }
               ,"EventType" : Concept
               #,"EventType" : "vocab:EventType"
               ,"EventPlace" : {
                 "Place" : "eventPlace|schema:Place"
                 #"Place" : "vocab:EventPlace"
               }
             }
             ,"Source" : {
               "SourceAvailableScans" : {
                   "Scan" : Scan
               }
               ,"SourcePlace" : {
                 "Place" : "sourcePlace|schema:Place"
                 #"Place" : "vocab:SourcePlace"
               }
               ,"SourceType" : "vocab:SourceType"
               ,"SourceReference" : {
                 "Place" : "surceReferencePlace|schema:Place"
                 #"Place" : "vocab:SourceReferencePlace"
                 ,"DocumentNumber" : "vocab:DocumentNumber"
                 ,"Folio" : "vocab:Folio"
                 ,"InstitutionName" : "vocab:InstitutionName"
                 ,"Book" : Concept
                 #,"Book" : "vocab:Book"
                 ,"Place" : "vocab:SourceReferencePlace"
                 ,"Archive" : Concept
                 #,"Archive" : "vocab:Archive"
               }
               ,"SourceRemark" : {
                 "Value" : "vocab:SourceRemark"
               }
               ,"SourceIndexDate" : {
                 "To" : "vocab:SourceIndexDateTo"
                 ,"From" : "vocab:SourceIndexDateFrom"
               }
               ,"SourceDate" : {
                 "Day" : "vocab:SourceDateDay"
                 ,"Month" : "vocab:SourceDateMonth"
                 ,"Year" : "vocab:SourceDateYear"
               }
               #,"RecordGUID" : "a2a:RecordGUID"
               ,"SourceLastChangeDate" : "vocab:SourceLastChangeDate"
             }
           }
         }
       }
}

files = (
	"frl_a2a_bb_a-201607.xml"
	,"frl_a2a_be_a-201607.xml"
	,"frl_a2a_br_a-201607.xml"
	,"frl_a2a_bs_g-201606.xml"
	,"frl_a2a_bs_h-201606.xml"
	,"frl_a2a_bs_o-201606.xml"
	,"frl_a2a_cc_a-201607.xml"
	,"frl_a2a_cv_a-201607.xml"
	,"frl_a2a_dtb_b-201607.xml"
	,"frl_a2a_dtb_d-201607.xml"
	,"frl_a2a_dtb_l-201607.xml"
	,"frl_a2a_dtb_t-201607.xml"
	,"frl_a2a_em_a-201607.xml"
	,"frl_a2a_mvs_a-201607.xml"
	,"frl_a2a_na_a-201607.xml"
	,"frl_a2a_ra_a-201607.xml"
	,"frl_a2a_t01_a-201605.xml"
	,"frl_a2a_t02_a-201607.xml"
	,"frl_a2a_t03_a-201607.xml"
	,"frl_a2a_t04_a-201607.xml"
	,"frl_a2a_t05_a-201607.xml"
	,"frl_a2a_t06_a-201607.xml"
	,"frl_a2a_t07_a-201607.xml"
	,"frl_a2a_t08_a-201607.xml"
	,"frl_a2a_t09_a-201607.xml"
	,"frl_a2a_t10_a-201607.xml"
	,"frl_a2a_t11_a-201607.xml"
	,"frl_a2a_t12_a-201607.xml"
	,"frl_a2a_t15_a-201607.xml"
	,"frl_a2a_t16_a-201607.xml"
	)
files = (
	"frl_a2a_bs_o"
	,"frl_a2a_bs_h"
	,"frl_a2a_bs_g")

for file in files:
#for file in {"bal2.xml"}:
    file += "-201611.xml"
    print("Bezig met ",file)
    starttime = time.time() 
    #lineoutcount = 0
    recordcount = 0
    #personcount = 0
    #
    context = ET.iterparse('C:/Users/Tjibbe/Desktop/resources/'+file)
    #context = ET.iterparse('C:/tmp/allefriezen/'+files[file])
    fp = open('e:/'+file+'.nt','wb')
    #fp = open('C:/tmp/allefriezen/'+files[file]+'.nt','w')
    # turn it into an iterator
    context = iter(context)
    for event, elem in context:
        #print(event,elem.tag)
        tag = stripnamespace(elem.tag)
        if event == 'end' and tag in topXMLstruct:
            recordcount += 1
            #print("found end ",elem.tag)
            ret = record(topXMLstruct[tag],elem,baseurl)
            #ret = ToRDF(XMLstruct[tag],elem)
            if ret:
                elem.clear()
    fp.close()
    endtime = time.time() 
    #print(file,recordcount,personcount,lineoutcount,endtime - starttime)
    print(file,'bevat',recordcount,'akten, in',endtime - starttime,'seconden verwerkt')
