import json  # Permet de lire des fichiers au format JSON
import pandas as pd  # Permet de manipuler des données sous forme de tableaux (DataFrame)
import numpy as np  # Permet de faire des calculs mathématiques
import seaborn as sns  # Permet de faire des graphiques type heatmap
import matplotlib.pyplot as plt  # Permet de faire des graphiques
import matplotlib.patches as patches  # Permet de dessiner des formes (rectangles, cercles) sur les graphiques

# Configurer matplotlib pour que les polices et les symboles s'affichent correctement
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


# CHARGER LES FICHIERS JSON
# Chaque fichier contient des informations sur les événements, joueurs et équipes

with open("C:/Users/bdaur/Downloads/AD/events/events_England.json", encoding="utf-8") as f:
    events = json.load(f)  # Charger tous les événements (passes, tirs, etc.)

with open("C:/Users/bdaur/Downloads/AD/players.json", encoding="utf-8") as f:
    players = json.load(f)  # Charger la liste des joueurs

with open("C:/Users/bdaur/Downloads/AD/teams.json", encoding="utf-8") as f:
    teams = json.load(f)  # Charger la liste des équipes

# Transformer les équipes en data frame
# On ne garde que l'identifiant unique (wyId) et le nom
teams_df = pd.json_normalize(teams)[["wyId", "name"]].rename(columns={"wyId": "teamId", "name": "teamName"})


# PRÉPARER LES DONNÉES DES JOUEURS
players_df = pd.json_normalize(players)  # Transformer la liste en DataFrame
# Créer une colonne avec le nom complet du joueur
players_df["playerName"] = players_df["firstName"] + " " + players_df["lastName"]
# Corriger les caractères spéciaux
players_df["playerName"] = players_df["playerName"].apply(lambda x: x.encode("utf-8").decode("unicode_escape"))
# garde que l'identifiant du joueur et son nom complet
players_df = players_df[["wyId", "playerName"]].rename(columns={"wyId": "playerId"})


# PRÉPARER LES DONNÉES DES ÉVÉNEMENTS
events_df = pd.json_normalize(events)  # Transformer la liste d'événements en DataFrame
# Choisir seulement les colonnes importantes
cols_wanted = ["matchId", "eventName", "subEventName", "teamId", "playerId", "eventSec", "positions", "tags"]
events_df = events_df[cols_wanted].copy()

# Extraire les coordonnées x et y de départ et d'arrivée pour chaque événement
# Si les coordonnées sont manquantes, mettre np.nan
events_df["x"] = events_df["positions"].apply(lambda p: p[0]["x"] if isinstance(p, list) and len(p) > 0 else np.nan)
events_df["y"] = events_df["positions"].apply(lambda p: p[0]["y"] if isinstance(p, list) and len(p) > 0 else np.nan)
events_df["end_x"] = events_df["positions"].apply(lambda p: p[1]["x"] if isinstance(p, list) and len(p) > 1 else np.nan)
events_df["end_y"] = events_df["positions"].apply(lambda p: p[1]["y"] if isinstance(p, list) and len(p) > 1 else np.nan)

# Filtrer pour ne garder que les passes
passes_df = events_df[events_df["eventName"] == "Pass"].copy()

# Ajouter le nom des joueurs aux DataFrames
events_df = events_df.merge(players_df, on="playerId", how="left")
passes_df = passes_df.merge(players_df, on="playerId", how="left")


# FILTRER LES PASSES QUI MÈNENT À UN TIR
def passes_vers_tir(passes_df, events_df, max_suivants=5):
    """
    Garder seulement les passes après lesquelles il y a un tir dans les 5 actions suivantes
    """
    passes_filtered = []  # Liste vide pour stocker les bonne passes
    for match_id in passes_df["matchId"].unique():  # Boucle sur chaque match
        # Trier les événements par ordre chronologique
        match_events = events_df[events_df["matchId"] == match_id].sort_values("eventSec").reset_index(drop=True)
        match_passes = passes_df[passes_df["matchId"] == match_id]
        for _, p in match_passes.iterrows():  # Boucle sur chaque passe
            # Trouver les événements du joueur au même endroit
            possibles = match_events[
                (match_events["playerId"] == p["playerId"]) &
                (abs(match_events["x"] - p["x"]) < 1e-3) &
                (abs(match_events["y"] - p["y"]) < 1e-3) &
                (match_events["eventName"] == "Pass")]
            if possibles.empty:
                continue  # Si aucune passe trouvée, passer à la suivante
            event_idx = possibles.index[0]
            # Prendre les prochaines actions (max_suivants) après cette passe
            next_events = match_events.iloc[event_idx+1:event_idx+1+max_suivants]
            if (next_events["eventName"] == "Shot").any():  # Si un tir a lieu
                passes_filtered.append(p)  # Garde cette passe
    return pd.DataFrame(passes_filtered)

passes_filtered = passes_vers_tir(passes_df, events_df, max_suivants=5)

# Calculer la progression horizontale (x final - x départ)
passes_filtered["progression"] = passes_filtered["end_x"] - passes_filtered["x"]

# Fonction pour filtrer les passes progressives
def est_progressive(row):
    if row["x"] < 80:
        return row["progression"] > 4  # Avance de +4 unités minimum
    else:
        return row["progression"] > -2  # En zone offensive, tolérer un léger recul

passes_filtered = passes_filtered[passes_filtered.apply(est_progressive, axis=1)]


# TOP 10 JOUEURS EN FONCTION DES PASSES PROGRESSIVES
player_scores = passes_filtered.groupby("playerName")["progression"].sum().reset_index()
top_players = player_scores.sort_values(by="progression", ascending=False).head(10)["playerName"].tolist()


# GÉNÉRER LES CARTES POUR CHAQUE JOUEUR
for player_name in top_players:
    player_passes = passes_filtered[passes_filtered["playerName"] == player_name].copy()
    player_passes = player_passes.sort_values(by="progression", ascending=False).head(50)
    player_touches = events_df[events_df["playerName"] == player_name].dropna(subset=["x","y"])  # Touches du joueur
    
    fig, ax = plt.subplots(figsize=(12,8))  # Créer une figure

    # Dessiner le terrain
    ax.add_patch(patches.Rectangle((0,0),100,100,facecolor="#e6f2e6", edgecolor="black"))
    ax.add_patch(patches.Rectangle((0,20),16.5,60,fill=False,edgecolor="white",linewidth=2))
    ax.add_patch(patches.Rectangle((100-16.5,20),16.5,60,fill=False,edgecolor="white",linewidth=2))
    centre_circle = patches.Circle((50,50),9.15,fill=False,edgecolor="white",linewidth=2)
    ax.add_patch(centre_circle)
    
    # Heatmap des touches rouges
    sns.kdeplot(
        x=player_touches["x"],
        y=player_touches["y"],
        fill=True,
        cmap="Reds",
        alpha=0.8,
        levels=50,
        thresh=0.1,
        ax=ax)
    
    # Flèches bleues pour les passes progressives
    for _, row in player_passes.iterrows():
        ax.arrow(
            row["x"], row["y"],
            row["end_x"] - row["x"],
            row["end_y"] - row["y"],
            head_width=1.5,
            head_length=1.5,
            color="blue",
            alpha=0.7,
            linewidth=1,
            length_includes_head=True)
    
    ax.set_xlim(0,100)
    ax.set_ylim(0,100)
    ax.set_xticks([])  
    ax.set_yticks([])  
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(f"Touches (rouge) et passes progressives (jaune) de {player_name}")
    ax.set_aspect('equal')
    plt.show()

# TRIANGLES DE PASSES PAR ÉQUIPE

def trouver_triangles_par_joueur(events_df, max_suivantes=5):
    """
    Trouver tous les triangles de passes :
    une passe va à B, B à C, C revient à A
    """
    triangles = []  # Liste vide pour stocker les triangles

    for match_id in events_df["matchId"].unique():  # Pour chaque match
        match_events = events_df[events_df["matchId"] == match_id].sort_values("eventSec").reset_index(drop=True)
        passes = match_events[match_events["eventName"] == "Pass"]  # Sélectionner seulement les passes

        for i, p1 in passes.iterrows():  # Boucle sur chaque passe p1
            joueur_a = p1["playerId"]  # Joueur A
            team_a = p1["teamId"]  # Son équipe

            next_events = passes.loc[i+1:i+max_suivantes]  # Prochaines passes
            for j, p2 in next_events.iterrows():
                joueur_b = p2["playerId"]  # Joueur B
                if joueur_b == joueur_a:
                    continue  # Ignorer si même joueur
                for k, p3 in next_events.loc[j+1:].iterrows():
                    joueur_c = p3["playerId"]  # Joueur C
                    if joueur_c == joueur_a:  # Triangle fermé si revient à A
                        triangles.append({
                            "matchId": match_id,
                            "teamId": team_a,
                            "players": [joueur_a, joueur_b, joueur_c]})
                        break
                break

    return pd.DataFrame(triangles)


# Calcul des triangles
triangles_df = trouver_triangles_par_joueur(events_df)

# Nombre de triangles par équipe
triangles_team = triangles_df.groupby("teamId").size().reset_index(name="triangles")

# Ajouter les noms des équipes
triangles_team = triangles_team.merge(teams_df, on="teamId", how="left")

# Trier par nombre de triangles
triangles_team = triangles_team[["teamName", "triangles"]].sort_values("triangles", ascending=False)
print("\nClassement des équipes par nombre de triangles de passes")
print(triangles_team)

# PASSES LONGUES PAR ÉQUIPE

def est_passe_longue(row):
    """
    Vérifie si une passe est très longue (>30 unités)
    """
    distance = np.sqrt((row["end_x"] - row["x"])**2 + (row["end_y"] - row["y"])**2)
    return distance > 30

# Sélectionner seulement les passes longues
passes_longues = events_df[
    (events_df["eventName"] == "Pass") &
    (events_df["subEventName"] == "High pass") &
    (events_df.apply(est_passe_longue, axis=1))]

# Compter les passes longues par équipe
long_balls_per_team = passes_longues.groupby("teamId").size().reset_index(name="long_balls")
# Ajouter noms des équipes
long_balls_per_team = long_balls_per_team.merge(teams_df, on="teamId", how="left")
# Trier du plus vertical au moins vertical
long_balls_per_team = long_balls_per_team[["teamName", "long_balls"]].sort_values("long_balls", ascending=False)
print("\nClassement des équipes par PASSES LONGUES (relances / longs ballons)")
print(long_balls_per_team)

# Renommer la colonne pour pouvoir faire un merge
long_balls_per_team = long_balls_per_team.rename(columns={"long_balls": "long_passes"})

# Fusionner triangles et passes longues pour compraison
comparatif = triangles_team.merge(long_balls_per_team, on="teamName", how="inner")
comparatif = comparatif.sort_values("triangles", ascending=False)

# Scatter pour comparer style de jeu
plt.figure(figsize=(10,7))
plt.scatter(comparatif["triangles"], comparatif["long_passes"])
for i, row in comparatif.iterrows():
    plt.text(row["triangles"], row["long_passes"], row["teamName"], fontsize=9)

plt.xlabel("Triangles de passes (construction)")
plt.ylabel("Passes longues (jeu direct)")
plt.title("Comparaison du style de jeu des équipes\nTriangles vs Passes Longues")
plt.grid(alpha=0.3)
plt.show()
