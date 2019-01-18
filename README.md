## Scripts HCERES

Ces scripts ont été réalisés en Juillet 2018 et Janvier 2019

Ils permettent de récupérer à partir de HAL, les publications d'une collection et de les rentrer dans une base puis de leur attribuer une note à partir d'organismes de ranking.

Les organismes de ranking que l'on utilise

SJR, généraliste, ranke les articles : [https://www.scimagojr.com/](https://www.scimagojr.com/)

CORE, domaine informatique, ranke les conférences : [http://portal.core.edu.au/conf-ranks/](http://portal.core.edu.au/conf-ranks/)

Ces scripts sont lancés chaque nuit dans cet ordre :

* __script_populate_publications_renew.py__ -> supprime toutes les publis de la base et les réimporte à partir de HAL
* __script_create_csv_scimago_core.py__ -> récupère les bases de données de scimago et Core et crée des fichiers CSV ad hoc
* __script_note_publications.py__ -> compare les infos entre les CSV et les journaux et conférences des publis enregistrées en base et leur attribue une note quand c'est possible

bastien.doreau@isima.fr  18/01/2019
