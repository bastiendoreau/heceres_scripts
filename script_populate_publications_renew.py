#!/usr/bin/python
#-*- coding: utf-8 -*-

######################################################################################################################
# Script python : script_populate_publications_renew.py
# Objectif : Remplit les tables publications, limos_publications_author, limos_keywordpublis et limos_domainpublis
# a partir des resultats de HAL
# Script lance toutes les nuits
#
# Etape 1 : On recupere par une requete sur l'API toutes les publis du LIMOS dans HAL -> liste 'publilist'
#           on recupere les valeurs halId (identifiant HAL), authFullName (nom et prenom des auteurs), title, URL
#           docType (type de document, article, these,...), keywords et producedDate (date de publication),
#           le domaine d'application ainsi que les journaux ou confs si ils existent
#           Pour le domaine d'application, une correspondance est faite pour une meilleure comprehension
# Etape 2 : On supprime ce qui existe en base dans mtm_publiauthor, mtm_publitheme, publication et domainpublis
#           id max de la table publication -> cptPubli=0
# Etape 3 : On recupere les champs id, authHalId, first_name, last_name,  de la table person -> list 'listPerson'
# Etape 4 : On compare les halId des 2 listes, si une publi ne se trouve pas dans la table, on l insere 
# Etape 5 : Si la publi est inseree, on compare les authIdHal recuperes de HAL et les authIdHal de la table Person de la base
#           En cas de correspondance, on insere une relation entre l'auteur et la publi et en tre le theme de l'auteur et la publi
#           -> tables mtm_publiauthor, mtm_publitheme
#           Sinon, on  compare les valeurs authFullName recuperes de HAL (formes auteurs) et les authFullName construits de la table Person de la base
#           En cas de correspondance, on insere une relation entre l'auteur et la publi et en tre le theme de l'auteur et la publi
#           -> tables mtm_publiauthor, mtm_publitheme
# Etape 6 : Enregistrement des resultats et problemes eventuels dans des logs
# 
# @author bastien.doreau@isima.fr - 07/2018
#
#######################################################################################################################

from __future__ import unicode_literals
import requests
import MySQLdb
import datetime

print "begin script "

cnt_idHal_match = 0
cnt_authfullname_match = 0

# connection database silimos

db = MySQLdb.connect(host='localhost',
                     user='*****',
                     passwd='*****',
                     db='*****',
		             use_unicode=True,
		             charset='utf8')



# Requete HAL ramenant toutes les publis du LIMOS, (uri,halId,authFullName, authIdHal, title,docType,keyword,producedDate, domain, journalTitle, conferenceTitle)
print "request HAL"
url = 'https://api.archives-ouvertes.fr/search/LIMOS/?q=*:*&start=0&rows=5000&sort=producedDate_s%20desc&fl=uri_s,halId_s,authFullName_s,authIdHal_s,title_s,docType_s,keyword_s,producedDate_s,domain_s,journalTitle_s,conferenceTitle_s'
req = requests.get(url)

print req.status_code
print req.headers['content-type']

json = req.json()
publilist = []

# recup en json et on se place dans response puis docs
tous_docs = json['response']['docs']

# pour chaque element de 'docs', on recupere les elements de la publi que l'on place dans publilist
cptpub=0
for doc in tous_docs:
	#print "lecture reponse"
	cptpub+=1
	list_authors = []
	list_authIdHal = []
	list_domains = []
	list_keywords =[]

	#recup halId
	recup_halId = doc["halId_s"]
	halid = '\"{0}\"'.format(recup_halId)

	# recup url
	uri = doc["uri_s"]
	uri = '\"{0}\"'.format(uri)

	#recup doctype
	doctype = doc["docType_s"]
	doctype = '\"{0}\"'.format(doctype)

	#recup title
	title = doc["title_s"]
	title[0].encode("utf-8")
	title[0] = title[0].replace("\""," ")

	# recup authors
	try :
		tous_authors = doc["authFullName_s"]
		for auth in tous_authors:
			list_authors.append((auth))
	except KeyError, e :
		list_authors = ""

    # recup authIdHal
	try :
		tous_authIdHal = doc["authIdHal_s"]
		for authIH in tous_authIdHal:
			list_authIdHal.append((authIH))
	except KeyError, e :
		list_authIdHal = ""    

	# recup producedDate
	producedDate = doc["producedDate_s"]

	# recup keywords
	# on recupere tous les keywords
	# Un 'try' est necessaire car pas forcement renseigne dans HAL
	# Certains mots cles peuvent contenir des elements speciaux comme π
	# on fait alors le remplacement
	try :
		tous_keywords = doc["keyword_s"]
		for k in tous_keywords :
			if "π" in k :
				k = k.replace("π","pi")
			list_keywords.append((k))
			k=k.encode("utf-8")

	except KeyError, e:
		keyw = ""

	# recup journal
	# Un 'try' est necessaire car pas forcement rensigne dans HAL
	try :
		journal = doc["journalTitle_s"]	
		journal = journal.replace("\""," ")
	except :
		journal = ""

	# recup conf
	# Un 'try' est necessaire car pas forcement rensigne dans HAL
	try :
		conf = doc["conferenceTitle_s"]	
		conf = conf.replace("\""," ")
	except :
		conf = ""

	# recup domain
	# Un 'try' est necessaire car pas forcement rensigne dans HAL
	try :
		tous_domains = doc["domain_s"]
		for domain in tous_domains :
			if "0.math" in domain:
				list_domains.append(("Maths"))
			if "0.spi" in domain:
				list_domains.append(("Sciences de l'ingenieur"))
			if "0.sdv" in domain:
				list_domains.append(("Sciences du vivant"))
			if "0.sde" in domain:
				list_domains.append(("Sciences de l'environnement"))
			if "0.phys" in domain:
				list_domains.append(("Physique"))
			if "0.shs" in domain:
				list_domains.append(("Sciences de l'homme et de la societe"))
			if "0.sdu" in domain:
				list_domains.append(("Planetes et univers"))
			if "0.stat" in domain:
				list_domains.append(("Statistiques"))
			if "1.info.eiah" in domain :
				list_domains.append(("Informatique Environnements Informatiques pour l'Apprentissage Humain"))
			if "1.info.info-ai" in domain :
				list_domains.append(("Informatique/Intelligence artificielle"))
			if "1.info.info-ao" in domain :
				list_domains.append(("Informatique/Arithmétique des ordinateurs"))
			if "1.info.info-ar" in domain :
				list_domains.append(("Informatique/Architectures Matérielles"))
			if "1.info.info-au" in domain :
				list_domains.append(("Informatique/Automatique"))
			if "1.info.info-bi" in domain :
				list_domains.append(("Informatique/Bio-informatique"))
			if "1.info.info-bt" in domain :
				list_domains.append(("Informatique/Biotechnologie"))
			if "1.info.info-cc" in domain :
				list_domains.append(("Informatique/Complexité"))
			if "1.info.info-ce" in domain :
				list_domains.append(("Informatique/Ingénierie, finance et science"))
			if "1.info.info-cg" in domain :
				list_domains.append(("Informatique/Géométrie algorithmique"))
			if "1.info.info-cl" in domain :
				list_domains.append(("Informatique/Informatique et langage"))
			if "1.info.info-cr" in domain :
				list_domains.append(("Informatique/Cryptographie et sécurité"))
			if "1.info.info-cv" in domain :
				list_domains.append(("Informatique/Vision par ordinateur et reconnaissance de formes"))
			if "1.info.info-cy" in domain :
				list_domains.append(("Informatique/Ordinateur et société"))
			if "1.info.info-db" in domain :
				list_domains.append(("Informatique/Base de données"))
			if "1.info.info-dc" in domain :
				list_domains.append(("Informatique/Calcul parallèle, distribué et partagé"))
			if "1.info.info-dl" in domain :
				list_domains.append(("Informatique/Bibliothèque électronique"))
			if "1.info.info-dm" in domain :
				list_domains.append(("Informatique/Mathématique discrète"))
			if "1.info.info-ds" in domain :
				list_domains.append(("Informatique/Algorithme et structure de données"))
			if "1.info.info-es" in domain :
				list_domains.append(("Informatique/Systèmes embarqués"))
			if "1.info.info-et" in domain :
				list_domains.append(("Informatique/Technologies Émergeantes"))
			if "1.info.info-fl" in domain :
				list_domains.append(("Informatique/Théorie et langage formel"))
			if "1.info.info-gl" in domain :
				list_domains.append(("Informatique/Littérature générale"))
			if "1.info.info-gr" in domain :
				list_domains.append(("Informatique/Synthèse d'image et réalité virtuelle"))
			if "1.info.info-gt" in domain :
				list_domains.append(("Informatique/Informatique et théorie des jeux"))
			if "1.info.info-hc" in domain :
				list_domains.append(("Informatique/Interface homme-machine"))
			if "1.info.info-ia" in domain :
				list_domains.append(("Informatique/Ingénierie assistée par ordinateur"))
			if "1.info.info-im" in domain :
				list_domains.append(("Informatique/Imagerie médicale"))
			if "1.info.info-ir" in domain :
				list_domains.append(("Informatique/Recherche d'information"))
			if "1.info.info-it" in domain :
				list_domains.append(("Informatique/Théorie de l'information"))
			if "1.info.info-iu" in domain :
				list_domains.append(("Informatique/Informatique ubiquitaire"))
			if "1.info.info-lg" in domain :
				list_domains.append(("Informatique/Apprentissage"))
			if "1.info.info-lo" in domain :
				list_domains.append(("Informatique/Logique en informatique"))
			if "1.info.info-ma" in domain :
				list_domains.append(("Informatique/Système multi-agents"))
			if "1.info.info-mc" in domain :
				list_domains.append(("Informatique/Informatique mobile"))
			if "1.info.info-mm" in domain :
				list_domains.append(("Informatique/Multimédia"))
			if "1.info.info-mo" in domain :
				list_domains.append(("Informatique/Modélisation et simulation"))
			if "1.info.info-ms" in domain :
				list_domains.append(("Informatique/Logiciel mathématique"))
			if "1.info.info-na" in domain :
				list_domains.append(("Informatique/Analyse numérique"))
			if "1.info.info-ne" in domain :
				list_domains.append(("Informatique/Réseau de neurones"))
			if "1.info.info-ni" in domain :
				list_domains.append(("Informatique/Réseaux et télécommunications"))
			if "1.info.info-oh" in domain :
				list_domains.append(("Informatique/Autre"))
			if "1.info.info-os" in domain :
				list_domains.append(("Informatique/Système d'exploitation"))
			if "1.info.info-pf" in domain :
				list_domains.append(("Informatique/Performance et fiabilité"))
			if "1.info.info-pl" in domain :
				list_domains.append(("Informatique/Langage de programmation"))
			if "1.info.info-rb" in domain :
				list_domains.append(("Informatique/Robotique"))
			if "1.info.info-ro" in domain :
				list_domains.append(("Informatique/Recherche opérationnelle"))
			if "1.info.info-sc" in domain :
				list_domains.append(("Informatique/Calcul formel"))
			if "1.info.info-sd" in domain :
				list_domains.append(("Informatique/Son"))
			if "1.info.info-se" in domain :
				list_domains.append(("Informatique/Génie logiciel"))
			if "1.info.info-si" in domain :
				list_domains.append(("Informatique/Réseaux sociaux et d'information"))
			if "1.info.info-sy" in domain :
				list_domains.append(("Informatique/Systèmes et contrôle"))
			if "1.info.info-ti" in domain :
				list_domains.append(("Informatique/Traitement des images"))
			if "1.info.info-ts" in domain :
				list_domains.append(("Informatique/Traitement du signal et de l'image"))
			if "1.info.info-tt" in domain :
				list_domains.append(("Informatique/Traitement du texte et du document"))
			if "1.info.info-wb" in domain :
				list_domains.append(("Informatique/Web"))

	except KeyError, e:
		list_domains.append((""))

	# Suppression des doublons 
	list_domains = list(set(list_domains))

	#print "nb domaine ",len(list_domains)
	#if len(list_domains)>0 :
	#	print "domaine ", list_domains[0]
	#	if len(list_domains)>0 :

	publilist.append((halid,uri,title[0],doctype,list_authors, list_keywords, producedDate, list_domains, journal, conf, list_authIdHal))



##################################
# on supprime de la base les champs des tables publication, research_mtm_publiauthor, research_mtm_publitheme
# ID max de la table =0
print "delete from research_mtm_publiauthor, research_mtm_publitheme , publication"
curPubli1 = db.cursor()
curPubli1.execute("DELETE FROM research_mtm_publiauthor;")
curPubli1.execute("DELETE FROM research_mtm_publitheme;")
curPubli1.execute("DELETE FROM publication;")
curPubli1.execute("DELETE FROM domainpublis;")

cptPubli=0



############################

# recuperation dans table Persons (id et champ first_name, last_name, et authIdHal)  pour matcher avec liste des auteurs recuperes
# une 2e requete est faite pour recuperer le theme associe a la personne
curAuthor = db.cursor()
curAuthor.execute("SELECT id, first_name, last_name, authIdHal FROM person;")

curAuthorTheme = db.cursor()
themeid = 0

listPerson = []


for person in curAuthor.fetchall():
	iduser = int(person[0])
	authfullname = person[1]
	authfullname = person[1].capitalize() +" "+person[2].capitalize()
	authIdHal = person[3]
	curAuthorTheme.execute("SELECT theme_id FROM person_mtm_persontheme WHERE person_id={0};".format(iduser))
	thid = 	curAuthorTheme.fetchone()
	print thid
	try :
		themeid = int(thid[0])
    # si le theme n'est pas trouve, -> theme non affilie
	except TypeError :
		themeid = 6
	listPerson.append((iduser, authfullname, themeid, authIdHal))


########################################
# dernier id domainpublis = 0 
cptdomainpublis = 0


############################

# un booleen 'match' est a False, il ne sert pas car les publis sont supprimees auparavant, possibilite de faire une comparaison avec une base existante


cptnewpublis = 0 # pour compter les nouvelles publis

cur2 = db.cursor()
cur2.execute("SET NAMES 'utf8'")

phraseerror=''

for publi in publilist :
	match = False

	# Pas de test -> 'match' == false donc on insere la publi
	if match == False :

		print (cptPubli+1, " - ",publi[1])

		cptPubli+=1
		cptdomainpublis+=1

		# les domaines sont recuperes de list_domain
		# si il n'existe pas, il vaut ""
		list_domain = publi[7]
		try :
			domain1 = list_domain[0]
		except IndexError, e:
			domain1 = ""
		try :
			domain2 = list_domain[1]
		except IndexError, e:
			domain2 = ""
		try :
			domain3 = list_domain[2]
		except IndexError, e:
			domain3 = ""
		try :
			domain4 = list_domain[3]
		except IndexError, e:
			domain4 = ""
		try :
			domain5 = list_domain[4]
		except IndexError, e:
			domain5 = ""
		try :
			domain6 = list_domain[5]
		except IndexError, e:
			domain6 = ""


		# Insertion des domaines dans la base (table limos_domainpublis)
		cur2.execute("INSERT INTO domainpublis (id, domain1, domain2, domain3, domain4, domain5, domain6) VALUES({0},\"{1}\",\"{2}\",\"{3}\",\"{4}\",\"{5}\",\"{6}\");".format(cptdomainpublis,domain1, domain2, domain3, domain4, domain5, domain6))
	
		# on retravaille la date recuperee car elle peut ne comporter que l'annee ou le mois et l'annee
		# pour plus de coherence dans la base, on complete avec -01-01 ou -01 selon ce qu'il manque
		datep=2000-01-01
		datep = publi[6]
		if len(datep) < 6 :
			datep  = str(datep)+"-01-01"
		elif len(datep) < 8 :
			datep  = str(datep)+"-01"
		#print "date publi ",datep
		
		# la liste des coauteurs est concatenee avec une virgule
        	coauthors = ', '.join(publi[4])

		# insertion de la publi en base (table publication)
		try :
			cur2.execute("INSERT INTO publication (id, halId, urlPub, title, doctype, producedDate, coauthors, domain_id, journal, conference, not_scimago, not_core) VALUES ({0},{1},{2},\"{3}\",{4},\"{5}\", \"{6}\",{7}, \"{8}\", \"{9}\",\"\",\"\");".format(cptPubli ,publi[0], publi[1], publi[2], publi[3], datep, coauthors, cptdomainpublis, publi[8], publi[9]))
			authors = publi[4]     # liste des formes auteurs
			authIdHals = publi[10] #liste des authIdHal
			cptnewpublis+=1

			# On met en parallele les liste des personnes du limos (dans listPerson) et des coauteurs de la publi
			# si correspondance, on insere en base (table limos_publication_author) l'ID de la personne et l'ID de la publi
			for person in listPerson :
				global cnt_idHal_match, cnt_authfullname_match
				match_user = False

				authHalBase = person[3]
				for authIdHal in authIdHals :
					if authIdHal == authHalBase :
						print ("Match user IDHAL ",authIdHal)
						cur2.execute("INSERT INTO research_mtm_publiauthor (person_id, publication_id) VALUES({0},{1});".format(person[0],cptPubli))
						# On associe l'id du theme de la personne a la publi
						cur2.execute("INSERT INTO research_mtm_publitheme (theme_id, publication_id) VALUES({0},{1});".format(person[2],cptPubli))
						cnt_idHal_match+=1
						match_user = True
                
				if match_user == False :
					authfn = person[1]
                
					for auth in authors:
					#print auth, authfn
						if auth ==  authfn:
							cnt_authfullname_match+=1
							cur2.execute("INSERT INTO research_mtm_publiauthor (person_id, publication_id) VALUES({0},{1});".format(person[0],cptPubli))
							# On associe l'id du theme de la personne a la publi
							cur2.execute("INSERT INTO research_mtm_publitheme (theme_id, publication_id) VALUES({0},{1});".format(person[2],cptPubli))


		except :
			print "Erreur ",cptPubli
			phraseerror+="Error HalId : {0} ".format(publi[0])

db.commit()

# On ecrit dans logpublis.txt le resultat du script
with open('/home/bastien/limenv/silimos/logpublis.txt','a') as logfile :
	logfile.write("\n")
	now = datetime.datetime.now()
	date_string = now.strftime('%Y-%m-%d') 
	phrase = ('Execution du script script_populate_publications_total.py du {0} \n'.format(date_string))
	#print type(phrase)
	logfile.write(phrase)
	phrase2 = ('Nouvelles publis integrees : {0} \n'.format(cptnewpublis))
	logfile.write(phrase2)
	phrase3 = ('Association users idHal : {0} - Association users authFullName : {1}\n'.format(cnt_idHal_match,cnt_authfullname_match))
	logfile.write(phrase3)
	logfile.write('Erreurs :')
	logfile.write(phraseerror)
	logfile.write("---------------------------------\n")
	logfile.close()


print ("cnt_idHal_match :", cnt_idHal_match)
print "fin"
db.close()
