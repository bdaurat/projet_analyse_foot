import json  # Permet de lire des fichiers au format JSON
import pandas as pd  # Permet de manipuler des données sous forme de tableaux (DataFrame)
import matplotlib.pyplot as plt  # Permet de faire des graphiques
from datetime import datetime


with open("C:/Users/bdaur/Downloads/AD/events/events_England.json", encoding="utf-8") as f:
    events = json.load(f)

with open("C:/Users/bdaur/Downloads/AD/players.json", encoding="utf-8") as f:
    players = json.load(f)

# Transformation des données JSON en DataFrame pandas
events_df = pd.json_normalize(events)
players_df = pd.json_normalize(players)


# Récupération des identifiants uniques des joueurs ayant participé à des événements
players_in_england = events_df["playerId"].dropna().unique()

# Sélection uniquement des joueurs présents dans les événements anglais
players_england_df = players_df[
    players_df["wyId"].isin(players_in_england)
]


# Comptage du nombre de joueurs par pays (top 15)
country_counts = (
    players_england_df["passportArea.name"]
    .value_counts()
    .head(15)  
)

# Création du graphique en barres horizontales
plt.figure(figsize=(10, 6))
country_counts.sort_values().plot(kind="barh")

# Création d'une légende du graphique
plt.title("Pays les plus représentés en Premier League en 2019")
plt.xlabel("Nombre de joueurs")
plt.ylabel("Pays")
plt.tight_layout()
plt.show()

# Le graphique montre que la majorité des joueurs évoluant en Premier League en 2019 sont de 
# nationalité anglaise, avec environ 125 joueurs. Les pays de la Grande-Bretagne sont globalement
# bien représentés, suivis par plusieurs pays européens, américains et africains. En revanche, aucun
# pays asiatique n’apparaît parmi les nationalités les plus représentées dans ce classement.
# L’absence de pays asiatiques parmi les nationalités dominantes peut s’expliquer par des différences
# de niveau de compétition, de filières de recrutement ou de préférences économiques et sportives.



# On filtre les joueurs dont le poste est "Forward" 
attackers_england_df = players_england_df[
    players_england_df["role.name"] == "Forward"
]

# Comptage du nombre d'attaquant par pays (top 15)
attacker_country_counts = (
    attackers_england_df["passportArea.name"]
    .value_counts()
    .head(15)
)

# Création du graphique en barres horizontales
plt.figure(figsize=(10, 6))
attacker_country_counts.sort_values().plot(kind="barh")

# Création d'une légende du graphique
plt.title("Pays les plus représentés parmi les attaquants en Premier League")
plt.xlabel("Nombre d'attaquants")
plt.ylabel("Pays")
plt.tight_layout()
plt.show()

# Contrairement au graphique précédent, les écarts entre les pays sont ici beaucoup plus faibles.
# L’Angleterre reste le pays le plus représenté parmi les attaquants avec environ 16 joueurs, suivie
# de l’Espagne avec environ 10 joueurs. On observe également l’apparition de pays qui n’étaient pas
# représentés dans le graphique global, tels que le Congo, la Jamaïque ou encore le Ghana, ce dernier
# se situant parmi les pays les plus représentés. En revanche, comme dans le graphique précédent, aucun
# pays asiatique n’apparaît parmi les nationalités dominantes. Cette répartition met en évidence une plus
# grande diversité des nationalités pour le poste d’attaquant en Premier League.



# Suppression des joueurs ayant des données manquantes
players_df = players_df.dropna(subset=["height", "weight", "birthDate", "role.name"])

# Conversion de la taille et du poids en valeurs numériques
players_df["height"] = players_df["height"].astype(float)
players_df["weight"] = players_df["weight"].astype(float)

# Calcul de l'âge à partir de l'année de naissance
players_df["age"] = players_df["birthDate"].apply(lambda x: datetime.now().year - int(x[:4]))


# limites des axes pour mieux voir les données des joueurs
x_min, x_max = 160, 200
y_min, y_max = 55, 100

# liste des postes
postes = ["Forward", "Midfielder", "Defender", "Goalkeeper"]
colors = ["red", "blue", "green", "purple"]

# Boucle pour créer un graphique par poste
for poste, color in zip(postes, colors):
    subset = players_df[players_df["role.name"] == poste]
    
    plt.figure(figsize=(8, 6))
    plt.scatter(subset["height"], subset["weight"],
                c=color, s=subset["age"]*2, alpha=0.6, edgecolors='k')
    
    plt.title(f"Profil physique des {poste}s en Premier League en 2019")
    plt.xlabel("Taille (cm)")
    plt.ylabel("Poids (kg)")
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)
    plt.grid(True)
    plt.show()
    
# Le profil physique type d’un joueur de football évoluant en Premier League en 2019 se situe globalement
# entre 1,60 m et 2,00 m pour la taille, et entre 55 kg et 100 kg pour le poids. Ces intervalles traduisent
# une grande diversité morphologique au sein du championnat.

# Chez les attaquants, les profils physiques apparaissent très dispersés, avec une large variété de taille
# et de poids. Néanmoins, une tendance générale se dégage : plus les attaquants sont grands, plus leur poids
# est élevé.

# Les milieux de terrain présentent quant à eux des profils légèrement plus petits et plus légers.
# On observe également une corrélation similaire, où les joueurs les plus petits sont en moyenne plus
# maigres, ce qui reflète des exigences de mobilité et d’endurance propres à ce poste.

# À l’inverse, les défenseurs se distinguent par des gabarits plus imposants, étant en moyenne plus grands
# et plus lourds que les milieux et les attaquants. Enfin, les gardiens de but affichent les profils 
# physiques les plus marqués, avec des tailles et des poids nettement supérieurs à la moyenne, soulignant
# les contraintes spécifiques liées à leur rôle.
    
    



