# projet_analyse_foot
Ce projet analyse des données d'événements de matchs de football afin d'extraire des insights tactiques et statistiques à l’échelle d’une saison et d’un match individuel.

L’objectif est d’explorer les dynamiques collectives (triangles de passes, longs ballons, réseaux de passes) ainsi que les profils types des joueurs à partir d’un dataset d’événements détaillé.

Le dataset utilisé est disponible ici :
🔗 https://figshare.com/collections/Soccer_match_event_dataset/4415000

(Source : figshare)

1) Analyse saisonnière – Heatmaps & Dynamiques collectives
Script : projet_ADD.py
- Génération de heatmaps
- Détection des triangles de passes
  
- Identification des équipes avec :
  - le plus grand nombre de triangles de passes
  - le plus grand nombre de longs ballons
  - Analyse comparative sur une saison complète d’un championnat

2) Analyse des profils joueurs
Script : profil_joueur.py
Extraction des caractéristiques principales des joueurs
Identification de profils types 

3) Pass Network – Analyse d’un match
Script : matchparmatch.py
Construction du réseau de passes d’une équipe
Visualisation des connexions entre joueurs
Mise en évidence des joueurs centraux (hubs)
Lecture tactique de l’organisation collective

Le dataset complet (≈160MB) n’est pas inclus dans ce repository.

Téléchargement
Le dataset est disponible ici :
https://figshare.com/collections/Soccer_match_event_dataset/4415000

Après téléchargement :
  - Extraire les fichiers
  - Placer les données dans un dossier :

Librairies :
Python
pandas
numpy
matplotlib
seaborn
