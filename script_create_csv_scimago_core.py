#!/usr/bin/python
#-*- coding: utf-8 -*-

####################################
# Script create CSV SCIMago
####################################
# SCIMAGO et CORE sont des agences de notation de journaux et conferences scientifiques
# SCIMAGO est generaliste et donne des notes Q1, Q2, Q3 et Q4 et ne note que les journaux
# https://www.scimagojr.com/
# CORE est specialise en informatique et donne des notes A*, A, B et C et note journaux et conferences
# http://portal.core.edu.au/conf-ranks/
#
# Ce script permet la creation de CSV contenant pour les journaux le titre et la note, et pour les conferences, le titre, l'acronyme et la note
# Principe : 
# - on telecharge des CSV a partir d'URL dans des fichiers
# - on parse les CSV en recuperant les infos souhaitees (titre et note ou titre, acronyme et note) dans une ou des listes
# - on reconstruit un CSV a partir de la ou les listes
#
# Pour SCIMAGO, les journaux sont recuperes par annee et tous les domaines sont analyses 
# Pour CORE, les conf sont recuperes par annee mais une seule base pour les journaux
####################################

import wget
import csv
import os


###########
# VARIABLES
###########

# URLs SCIMAGO pour les domaines informatique (computer science), mathematiques et engineering
url_sci_2017 = 'https://www.scimagojr.com/journalrank.php?year=2017&type=j&out=xls'
url_sci_2016 = 'https://www.scimagojr.com/journalrank.php?year=2016&type=j&out=xls'
url_sci_2015 = 'https://www.scimagojr.com/journalrank.php?year=2015&type=j&out=xls'
url_sci_2014 = 'https://www.scimagojr.com/journalrank.php?year=2014&type=j&out=xls'
url_sci_2013 = 'https://www.scimagojr.com/journalrank.php?year=2013&type=j&out=xls'


# URLs CORE pour les conferences
url_core_conf_2018="http://portal.core.edu.au/conf-ranks/?search=&by=all&source=CORE2018&sort=arank&page=1&do=Export"
url_core_conf_2017="http://portal.core.edu.au/conf-ranks/?search=&by=all&source=CORE2017&sort=arank&page=1&do=Export"
url_core_conf_2014="http://portal.core.edu.au/conf-ranks/?search=&by=all&source=CORE2014&sort=arank&page=1&do=Export"
url_core_conf_2013="http://portal.core.edu.au/conf-ranks/?search=&by=all&source=CORE2013&sort=arank&page=1&do=Export"
url_core_jnl_all="http://portal.core.edu.au/jnl-ranks/?search=&by=all&source=all&sort=atitle&page=1&do=Export"

# Fichiers CSV crees
new_csv_sci_17="ranking/SCIMago-J-2017.csv"
new_csv_sci_16="ranking/SCIMago-J-2016.csv"
new_csv_sci_15="ranking/SCIMago-J-2015.csv"
new_csv_sci_14="ranking/SCIMago-J-2014.csv"
new_csv_sci_13="ranking/SCIMago-J-2013.csv"

new_csv_core_c_18="ranking/CORE-C-2018.csv"
new_csv_core_c_17="ranking/CORE-C-2017.csv"
new_csv_core_c_14="ranking/CORE-C-2014.csv"
new_csv_core_c_13="ranking/CORE-C-2013.csv"
new_csv_core_j_all="ranking/CORE-J-all.csv"

# Compteurs
cnt_scimago_jrn=0
cnt_core_conf=0
cnt_core_jrn=0
cnt_problems_sautligne=0

###########
# FONCTIONS
###########

# delete the downloaded file from scimago or core
def delete_file(download_file):
    if os.path.isfile(download_file):
        os.remove(download_file)

# Creation des fichiers SCIMago contenant titre des journaux et notes pour tous les domaines
# Lecture du CSV telecharge envoye en parametres 
# Enregistrement titre et note a partir des 3 CSV dans 3 listes : list_sci_com, list_sci_mat, list_sci_eng si note = Q1, Q2, Q3 ou Q4
# Ecriture d'un nouveau fichier csv a partir des 3 listes
def create_csv_scimago(csvsci, new_csv) :
    global cnt_scimago_jrn
    cnt_scimago_jrn+=1
    print "begin create_csv_scimago"
    csv_sci_com = csv.reader(open(csvsci,"rb"), delimiter=str(';'), quotechar='|')
    list_sci_com = []
    for row in csv_sci_com :
        title = str(row[2])
        print title
        title = title.replace('"','')
        if (row[6] == "Q1") or (row[6] == "Q2") or (row[6] == "Q3") or (row[6] == "Q4") :
            list_sci_com.append((title,str(row[6])))



    with open(new_csv, 'wb') as myfile:
        for journal in list_sci_com :
            line = (journal[0]+'|'+journal[1])
            myfile.write(line)
            myfile.write('\n')


# Creation des fichiers CORE conferences contenant titre des conf, acronymes et notes
# Lecture du CSV telecharge envoye en parametre 
# Enregistrement nom_conf, acronyme et note dans 1 liste : list_core si note = A*, A, B ou C
# Ecriture d'un nouveau fichier csv a partir de la liste
def create_csv_core_conf(csv_core_conf, new_csv) :
    global cnt_core_conf
    cnt_core_conf+=1

    csv_core = csv.reader(open(csv_core_conf,"rb"), delimiter=str(','), quotechar='"')
    list_core = []
    global cnt_problems_sautligne
    for row in csv_core :
        title = str(row[1])
        if "\n" in title :
            title=title.replace("\r\n","") 
            cnt_problems_sautligne+=1
        acronym = str(row[2])
        note = str(row[4])
        if (note == "A*") or (note == "A") or (note == "B") or (note == "C") :
            list_core.append((title,acronym,note))

    with open(new_csv, 'wb') as myfile:
        for conf in list_core :
            line = (conf[0]+'|'+conf[1]+'|'+conf[2])
            myfile.write(line)
            myfile.write('\n')

# Creation des fichiers CORE journaux (un seul actuellement) contenant titre du journal et note
# Lecture du CSV telecharge envoye en parametre 
# Enregistrement titre et note dans 1 liste : list_core si note = A*, A, B ou C
# Ecriture d'un nouveau fichier csv a partir de la liste
def create_csv_core_jrn(csv_core_jrn, new_csv) :
    global cnt_core_jrn
    cnt_core_jrn+=1
    csv_core = csv.reader(open(csv_core_jrn,"rb"), delimiter=str(','), quotechar='"')
    list_core = []
    for row in csv_core :
        title = str(row[1])
        if "\n" in title :
            title.replace("\n","") 
            cnt_problems_sautligne+=1
        note = str(row[3])
        if (note == "A*") or (note == "A") or (note == "B") or (note == "C") :
            list_core.append((title,note))

    with open(new_csv, 'wb') as myfile:
        for conf in list_core :
            line = (conf[0]+'|'+conf[1])
            myfile.write(line)
            myfile.write('\n')

###########
# PROGRAMME
###########

# Download files from SCIMAGO and create 5 CSV
file_sci_com_17 = wget.download(url_sci_2017)
create_csv_scimago(file_sci_com_17, new_csv_sci_17)

file_sci_com_16 = wget.download(url_sci_2016)
create_csv_scimago(file_sci_com_16, new_csv_sci_16)

file_sci_com_15 = wget.download(url_sci_2015)
create_csv_scimago(file_sci_com_15, new_csv_sci_15)

file_sci_com_14 = wget.download(url_sci_2014)
create_csv_scimago(file_sci_com_14, new_csv_sci_14)

file_sci_com_13 = wget.download(url_sci_2013)
create_csv_scimago(file_sci_com_13, new_csv_sci_13)

# Delete downloaded files SCIMAGO

delete_file(file_sci_com_17)
delete_file(file_sci_com_16)
delete_file(file_sci_com_15)
delete_file(file_sci_com_14)
delete_file(file_sci_com_13)


# Download files from CORE ,create CSV and delete file
file_core_conf_18 = wget.download(url_core_conf_2018)
create_csv_core_conf(file_core_conf_18,new_csv_core_c_18)
delete_file(file_core_conf_18)

file_core_conf_17 = wget.download(url_core_conf_2017)
create_csv_core_conf(file_core_conf_17,new_csv_core_c_17)
delete_file(file_core_conf_17)

file_core_conf_14 = wget.download(url_core_conf_2014)
create_csv_core_conf(file_core_conf_14,new_csv_core_c_14)
delete_file(file_core_conf_14)

file_core_conf_13 = wget.download(url_core_conf_2013)
create_csv_core_conf(file_core_conf_13,new_csv_core_c_13)
delete_file(file_core_conf_13)

file_core_jrn_all = wget.download(url_core_jnl_all)
create_csv_core_jrn(file_core_jrn_all,new_csv_core_j_all)
delete_file(file_core_jrn_all)
print ""
print "RESULTATS"
print "Fichiers CSV SCIMago : "+str(cnt_scimago_jrn)
print "Fichiers CSV CORE conf : "+str(cnt_core_conf)
print "Fichiers CSV CORE journaux : "+str(cnt_core_jrn)
print "problemes saut de lignes regles : "+str(cnt_problems_sautligne)
print "fin"

