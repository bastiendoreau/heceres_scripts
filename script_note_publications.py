#!/usr/bin/python
#-*- coding: utf-8 -*-

######################################################################################################################
# Script python : script_note_publications.py
# Objectif : Noter les publis dans des journaux avec une notation Q1, Q2, Q3, Q4 et  A*, A, B, C a partir de CSV issus de SCIMAGO et CORE
#
# Les CSV Scimago permettent uniquement de noter les journaux, les CSV CORE permettent de noter journaux et conf
# Les CSV SCIMAGO ont un champ avec le journal et un autre avec la note
# Le CSV CORE pour les journaux a un champ avec le journal et un autre avec la note
# Les CSV CORE pour les conf ont un champ avec la conf, un champ avec l'acronyme de la conf et un autre champ avec la note
#
# Dans la base de donnees, les publis notees ARTICLE peuvent avoir des journaux associes et les publis notees COMM, des conferences associees
# Le principe est de faire matcher un journal ou une conf du CSV avec le journal ou la conf de la publi en base
# 
# La notation dans SCIMAGO ou CORE d'un journal ou d'une conf peut apparaitre quelques annees apres la parution de la publi
# On regarde donc selon la date de la publi, la liste (des journaux ou conf de Scimago ou CORE) de la meme annee pour faire le matching
# Ceci est valable pour les journaux. Pour les confs, si aucun matching ne se fait, on regarde la liste de l'annee suivante, ... 
# 
# Deux methodes ont ete definies
# - 'updatePubliJournalNote' pour mettre a jour le champ 'not_scimago' ou 'not_core' si un matching se fait entre le journal de la publi et une des lignes
# du CSV donne en argument. Avant le matching, le journal de la publi est nettoye (suppression des tirets, points, ...) et la comparaison se fait entre les 
# valeurs mises en majuscules
# - 'updatePubliConfNote' pour mettre a jour le champ 'not_scimago' ou 'not_core' si un matching se fait entre la conf de la publi et une des lignes
# du CSV donne en argument. Un autre champ est donne en argument, le booleen 'acroBool' pour savoir si on veut trouver le titre de la conf du CSV 
# dans la conf de la publi ou l'acronyme de de la conf du CSV dans la conf de la publi 
#
# Etapes :
# * Recuperation de toutes les publis ayant un champ 'journal' different de "" -> recup des champs id, journal et date de publication
# Pour des publis de 2010 a 2013, on verifie dans le CSV de 2013, pour des publis de 2014, dans le CSV de 2014, ...
# * Recuperation de toutes les publis ayant un champ 'conference' different de "" -> recup des champs id, conference et date de publication
# Pour des publis de 2010 a 2013, on verifie dans le CSV de 2013, pour des publis de 2010 a 2014, dans le CSV de 2014, ...
# Si la matching est fait, on ne recherche pas sur les annees suivantes, sinon on continue la recherche
# Apres avoir verifie les confs et si le matching n'est pas fait, on verifie avec les acronymes
#######################################################################################################################

from __future__ import unicode_literals
import MySQLdb
import csv



print "begin script "

# connection database silimos

db = MySQLdb.connect(host='localhost',
                     user='*****',
                     passwd='*****',
                     db='*****',
		             use_unicode=True,
		             charset='utf8')

######## VARIABLES
### SCIMAGO Files

# Articles
S_J_csv2013 = "/home/bastien/limenv/silimos/scriptbase/ranking/SCIMago-J-2013.csv"
S_J_csv2014 = "/home/bastien/limenv/silimos/scriptbase/ranking/SCIMago-J-2014.csv"
S_J_csv2015 = "/home/bastien/limenv/silimos/scriptbase/ranking/SCIMago-J-2015.csv"
S_J_csv2016 = "/home/bastien/limenv/silimos/scriptbase/ranking/SCIMago-J-2016.csv"
S_J_csv2017 = "/home/bastien/limenv/silimos/scriptbase/ranking/SCIMago-J-2017.csv"

### CORE Files
# Conf
C_C_csv2013 = "/home/bastien/limenv/silimos/scriptbase/ranking/CORE-C-2013.csv"
C_C_csv2014 = "/home/bastien/limenv/silimos/scriptbase/ranking/CORE-C-2014.csv"
C_C_csv2017 = "/home/bastien/limenv/silimos/scriptbase/ranking/CORE-C-2017.csv"
C_C_csv2018 = "/home/bastien/limenv/silimos/scriptbase/ranking/CORE-C-2018.csv"

# Articles
C_J_csvAll = "/home/bastien/limenv/silimos/scriptbase/ranking/CORE-J-all.csv"

### Others
# cursors for DB
curNbPublisJ = db.cursor()
curPublisJ = db.cursor()
curUpdatePubJ = db.cursor()

curNbPublisC = db.cursor()
curPublisC = db.cursor()
curUpdatePubC = db.cursor()

# counters
count_scimago_journals=0
count_core_journals=0
count_core_conf=0

problems_name_title=""

######## METHODS

# supprime le contenu des parentheses et les parentheses de la conf issue du CSV
def splitParenthese(nameConf):
    #global count_parenthese
    p1 = nameConf.find("(")
    p2 = nameConf.find(")")    
    nameWithoutParenthese = nameConf[:p1]+nameConf[p2+1:]
    #count_parenthese+=1
    return nameWithoutParenthese


# Met a jour la base avec une note Scimago ou Core pour une publi de type ARTICLE ayant un journal
# En entree, un CSV, le journal de la publi, l'id de la publi et l'organsime (soit 'not_scimago' soit 'not_core')
# - met le contenu du CSV (journal + note) dans une liste -> list_journal
# - pour chaque element de cette liste, si le journal du CSV correspond au journal de la publi -> maj
# - maj avec curUpdatePubJ puis incrementation de compteurs
def updatePubliJournalNote(csv, journalpub, idpub, typeOrganism, match_conf) :
    global count_scimago_journals, count_core_journals, problems_name_title
    if (match_conf == False) :
        list_journal = []
        for row in csv:
            try :
                journal = row[0]#.decode("utf-8")
                note = row[1]
                list_journal.append((journal,note))
            except :
                problems_name_title = problems_name_title + row[0] + "\n"


        for journal in list_journal :
            journrank=journal[0].decode('utf-8')
            journalpub=journalpub.replace(',','')
            journrank = journrank.replace(',','')
            journalpub=journalpub.replace(':','')
            journrank = journrank.replace(':','')
            journalpub=journalpub.replace('.','')
            journrank = journrank.replace('.','')
            journalpub=journalpub.replace('  ',' ')
            journrank = journrank.replace('  ',' ')
            journalpub=journalpub.strip()
            journrank = journrank.strip()

            if journrank.upper() == journalpub.upper() :
                print ("-> match, journal= ",journal[0],"note= ",journal[1])
                match_conf==True
                curUpdatePubJ.execute("UPDATE publication set {2}=\"{0}\" where id={1}".format(journal[1],idpub, typeOrganism))    
                if typeOrganism == "not_scimago" :
                    count_scimago_journals+=1
                if typeOrganism == "not_core" :
                    count_core_journals+=1
    return match_conf

# Met a jour la base avec une note Core (pas Scimago) pour une publi de type COMM ayant une conf referencee
# En entree, un CSV, la conf de la publi, l'id de la publi, l'organisme (seulement 'not_core' cette fois), la valeur booleenne acronym (False si on compare la conf, True si on compare l'acronyme), la valeur booleenne match_conf indiquant si la note a deja ete trouvee
# - met le contenu du CSV (conf + acronym + note) dans une liste -> list_conf
# - pour chaque element de cette liste, si la conf du CSV correspond a la conf de la publi -> maj
# - maj avec curUpdatePubC puis incrementation de compteurs
# - renvoie un booleen 'match_conf' indiquant si le matching a ete fait. 
def updatePubliConfNote(csv, confpub, idpub, typeOrganism, acroBool, match_conf) :
    global count_core_conf, problems_name_title
    if (match_conf == False) :
        list_conf = []

        for row in csv:
            try :
                conf = row[0]#.decode("utf-8")
                if conf.find("(") > 0 :
                    conf = splitParenthese(conf)
                acronym = row[1]
                note = row[2]
                #print ("conf ",conf," - acronym ",acronym, " - note",note)
                list_conf.append((conf,acronym,note))
            except IndexError :
                problems_name_title = problems_name_title + row[0] + "\n"

        if acroBool == False :
            for conf in list_conf :
                confrank=conf[0]
                confpub=confpub.replace(',','')
                confrank = confrank.replace(',','')
                confpub=confpub.replace(':','')
                confrank = confrank.replace(':','')
                confpub=confpub.replace('.','')
                confrank = confrank.replace('.','')
                confpub=confpub.replace('  ',' ')
                confrank = confrank.replace('  ',' ')
                confpub=confpub.strip()
                confrank = confrank.strip()
                #print(conf[0].upper(),'--', confpub.upper())
                #if ("Financial Cryptography and Data Security Conference" in confrank) :
                #    print ("************* ************* ********** ",confpub.upper(),"-----",confrank.upper())
                if confrank.upper() in confpub.upper() :
                    print ("-> match, conf= ",conf[0],"note= ",conf[2])
                    curUpdatePubC.execute("UPDATE publication set {2}=\"{0}\" where id={1}".format(conf[2],idpub, typeOrganism))
                    match_conf = True    
                    #if typeOrganism == "not_scimago" :
                    #    count_scimago_conf+=1
                    if typeOrganism == "not_core" :
                        count_core_conf+=1
        if acroBool == True :
            for conf in list_conf :

                acronymconf = conf[1]
                if (len(acronymconf) > 3) and (acronymconf.upper()==acronymconf):
                    acronymconftest1=" "+acronymconf
                    acronymconftest2="("+acronymconf
                    acronymconftest3=acronymconf+" "
                    acronymconftest4=acronymconf+"'"
                    acronymconftest5=acronymconf+")"
                    if (acronymconftest1 in confpub) or (acronymconftest2 in confpub)  or (acronymconftest3 in confpub)  or (acronymconftest4 in confpub) or (acronymconftest5 in confpub) :
                    # A VOIR if (acronymconftest1 in confpub) or (acronymconftest2 in confpub) or (acronymconftest3 in confpub):
                        
                        print ("-> match, conf (acronym)= ",conf[1]," - conf=",confpub,"note= ",conf[2])
                        curUpdatePubC.execute("UPDATE publication set {2}=\"{0}\" where id={1}".format(conf[2],idpub, typeOrganism))
                        match_conf = True  
                        if typeOrganism == "not_core" :
                            count_core_conf+=1
    return match_conf



#######################################
######## SCRIPT
### UPDATE NOTE JOURNAL

curNbPublisJ.execute("select count(*) from publication where journal <>'';")
cptPubliJTotal = curNbPublisJ.fetchone()[0]

curPublisJ.execute("select id, journal, producedDate from publication where journal <>'';")

for publiJ in curPublisJ.fetchall():
    idpub = publiJ[0]
    journalpub = publiJ[1]
    datepub = publiJ[2]
    #print ("id ",idpub," - journal ",journalpub)
    match_conf = False

    # verif matching scimago with date publi
    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)):
        csvscimago = csv.reader(open(S_J_csv2013,"rb"), delimiter=str('|'))
        match_conf=updatePubliJournalNote(csvscimago,journalpub, idpub,"not_scimago",match_conf)

    if ("2013" in str(datepub)) or ("2014" in str(datepub)) :
        csvscimago = csv.reader(open(S_J_csv2014,"rb"), delimiter=str('|'))
        match_conf=updatePubliJournalNote(csvscimago,journalpub, idpub,"not_scimago",match_conf)

    if ("2014" in str(datepub)) or ("2015" in str(datepub)) :
        csvscimago = csv.reader(open(S_J_csv2015,"rb"), delimiter=str('|'))
        match_conf=updatePubliJournalNote(csvscimago,journalpub, idpub,"not_scimago",match_conf)

    if ("2015" in str(datepub)) or ("2016" in str(datepub)) :
        csvscimago = csv.reader(open(S_J_csv2016,"rb"), delimiter=str('|'))
        match_conf=updatePubliJournalNote(csvscimago,journalpub, idpub,"not_scimago",match_conf)

    if ("2016" in str(datepub)) or ("2017" in str(datepub)) or ("2018" in str(datepub)) :
        csvscimago = csv.reader(open(S_J_csv2017,"rb"), delimiter=str('|'))
        match_conf=updatePubliJournalNote(csvscimago,journalpub, idpub,"not_scimago",match_conf)

    match_conf = False

    # verif matching core
    csvcore = csv.reader(open(C_J_csvAll,"rb"), delimiter=str('|'))
    updatePubliJournalNote(csvcore,journalpub, idpub,"not_core",match_conf)



#######################################
### UPDATE NOTE CONF

curNbPublisC.execute("select count(*) from publication where conference <>'';")
cptPubliCTotal = curNbPublisC.fetchone()[0]

curPublisC.execute("select id, conference, producedDate from publication where conference <>'';")

for publiC in curPublisC.fetchall():
    idpub = publiC[0]
    confpub = publiC[1]
    datepub = publiC[2]


    match_conf_core = False

    # verif matching core exact conference with date publi
    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)):
        csvCcore = csv.reader(open(C_C_csv2013,"rb"), delimiter=str('|'))
        match_conf_core = updatePubliConfNote(csvCcore, confpub, idpub, "not_core", False, match_conf_core)

    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)) or ("2014" in str(datepub)):
        csvCcore = csv.reader(open(C_C_csv2014,"rb"), delimiter=str('|'))
        match_conf_core = updatePubliConfNote(csvCcore, confpub, idpub, "not_core", False, match_conf_core)

    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)) or ("2014" in str(datepub)) or ("2015" in str(datepub)) or ("2016" in str(datepub)) or ("2017" in str(datepub)) :
        csvCcore = csv.reader(open(C_C_csv2017,"rb"), delimiter=str('|'))
        match_conf_core = updatePubliConfNote(csvCcore, confpub, idpub, "not_core", False, match_conf_core)

    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)) or ("2014" in str(datepub)) or ("2015" in str(datepub)) or ("2016" in str(datepub)) or ("2017" in str(datepub)) or ("2018" in str(datepub)) or ("2019" in str(datepub))  :
        csvCcore = csv.reader(open(C_C_csv2018,"rb"), delimiter=str('|'))
        match_conf_core = updatePubliConfNote(csvCcore, confpub, idpub, "not_core", False, match_conf_core)

    # verif matching core acronym with date publi
    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)):
        csvCcore = csv.reader(open(C_C_csv2013,"rb"), delimiter=str('|'))
        match_conf_core = updatePubliConfNote(csvCcore, confpub, idpub, "not_core", True, match_conf_core)

    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)) or ("2014" in str(datepub)):
        csvCcore = csv.reader(open(C_C_csv2014,"rb"), delimiter=str('|'))
        match_conf_core = updatePubliConfNote(csvCcore, confpub, idpub, "not_core", True, match_conf_core)

    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)) or ("2014" in str(datepub)) or ("2015" in str(datepub)) or ("2016" in str(datepub)) or ("2017" in str(datepub)) :
        csvCcore = csv.reader(open(C_C_csv2017,"rb"), delimiter=str('|'))
        match_conf_core = updatePubliConfNote(csvCcore, confpub, idpub, "not_core", True, match_conf_core)

    if ("2010" in str(datepub)) or ("2011" in str(datepub)) or ("2012" in str(datepub)) or ("2013" in str(datepub)) or ("2014" in str(datepub)) or ("2015" in str(datepub)) or ("2016" in str(datepub)) or ("2017" in str(datepub)) or ("2018" in str(datepub))  or ("2019" in str(datepub))  :
        csvCcore = csv.reader(open(C_C_csv2018,"rb"), delimiter=str('|'))
        match_conf_core = updatePubliConfNote(csvCcore, confpub, idpub, "not_core", True, match_conf_core)




db.commit()
print ("-------------------------------------------")
print ("RESULTATS")
print ("---------")
print ("nb publis ARTICLE avec journal reference :",int(cptPubliJTotal))
print ("nb publis COMM avec conf reference :",int(cptPubliCTotal))
print ("note scimago journals :",count_scimago_journals)
print ("note core journals :",count_core_journals)
print ("note core conf :",count_core_conf)
print ("---------")
print ("PROBLEMES")
print ("---------")
print ("Problemes dans le nom du titre (titre non pris en compte) :",problems_name_title)
print ("fin")
db.close()



