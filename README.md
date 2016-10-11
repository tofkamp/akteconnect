# akteconnect
Connect BS akten

In order to use this software, do the following:
mkdir data
and put akte.py into it, along with an empy file called "__init__.py". I don't know why, but I cannot create a directory in Github, so you have to do it yourself.

All programs run in python3 except akteconnect.py which runs on python2 because pygame.org is not available in python3. The test version of python3 pygame.org has terrible fonts, so use version 1.9.1 to have a good view. I use the portable python2 standalone distribution: http://portablepython.com/wiki/Download/
Download the dumps from https://opendata.picturae.com/ "Burgelijke stand" files (geboorte,overlijden en huwelijk) from allefriezen dataset.

If you want to create LOD files, use allefriezen.py

Run "allefriezen naar sqlite.py" to put all info into relational database (BurgelijkeStand1610.db)
run "maakpuzzels.py" to create all *.puz files from the huwelijken.
Copy koppelleeg.db to koppel.db, in order to have a place to put the connections.
Solve all puzzels with akteconnect.py

With koppelstats.py you can see your progress, just for fun.

In order to create LOD, the ids between runs must be persistant.
Create empty persistant-ids.db file:
sqlite3.exe persistant-ids.db
DROP TABLE IF EXISTS persons;
DROP TABLE IF EXISTS places;
CREATE TABLE persons(personid text,id int);
CREATE TABLE places(placeid text,id int);

You can export the connections to Linked Open Data, or Gramps csv file (https://gramps-project.org/wiki/index.php?title=Gramps_4.2_Wiki_Manual_-_Manage_Family_Trees:_CSV_Import_and_Export)

Running koppelhet4.py, will produce the LOD and .csv file.
