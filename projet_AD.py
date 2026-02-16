import json
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Charger les fichiers ---
with open("C:/Users/bdaur/Downloads/AD/events/events_England.json", encoding="utf-8") as f:
    events = json.load(f)

with open("C:/Users/bdaur/Downloads/AD/players.json", encoding="utf-8") as f:
    players = json.load(f)

# --- Préparer les données des joueurs ---
players_df = pd.json_normalize(players)
players_df["playerName"] = players_df["firstName"] + " " + players_df["lastName"]
players_df = players_df[["wyId", "playerName"]].rename(columns={"wyId": "playerId"})

# --- Préparer les données des événements ---
events_df = pd.json_normalize(events)
cols_wanted = ["matchId", "eventName", "subEventName", "teamId", "playerId", "eventSec", "positions"]
events_df = events_df[cols_wanted].copy()

# Extraire les coordonnées
events_df["x"] = events_df["positions"].apply(lambda p: p[0]["x"] if isinstance(p, list) and len(p) > 0 else np.nan)
events_df["y"] = events_df["positions"].apply(lambda p: p[0]["y"] if isinstance(p, list) and len(p) > 0 else np.nan)
events_df["end_x"] = events_df["positions"].apply(lambda p: p[1]["x"] if isinstance(p, list) and len(p) > 1 else np.nan)
events_df["end_y"] = events_df["positions"].apply(lambda p: p[1]["y"] if isinstance(p, list) and len(p) > 1 else np.nan)

# Filtrer les passes
passes_df = events_df[events_df["eventName"] == "Pass"].copy()

# Fusionner les noms de joueurs
events_df = events_df.merge(players_df, on="playerId", how="left")
passes_df = passes_df.merge(players_df, on="playerId", how="left")

# --- Choisir le joueur à analyser ---
player_name = "Harry Kane"
max_suivants = 5  # nb d'actions suivantes pour filtrer passes vers tir

# --- Fonction : passes menant à un tir ---
def passes_vers_tir(passes_df, events_df, max_suivants=5):
    passes_filtered = []
    for match_id in passes_df["matchId"].unique():
        match_events = events_df[events_df["matchId"] == match_id].sort_values("eventSec").reset_index(drop=True)
        match_passes = passes_df[passes_df["matchId"] == match_id]
        for _, p in match_passes.iterrows():
            possibles = match_events[
                (match_events["playerId"] == p["playerId"]) &
                (abs(match_events["x"] - p["x"]) < 1e-3) &
                (abs(match_events["y"] - p["y"]) < 1e-3) &
                (match_events["eventName"] == "Pass")
            ]
            if possibles.empty:
                continue
            event_idx = possibles.index[0]
            next_events = match_events.iloc[event_idx+1 : event_idx+1+max_suivants]
            if (next_events["eventName"] == "Shot").any():
                passes_filtered.append(p)
    return pd.DataFrame(passes_filtered)

# --- Fonction : calculer xA approximatif ---
def xa_approx(passes_df, events_df, max_suivants=2):
    xa_list = []
    for match_id in passes_df["matchId"].unique():
        match_events = events_df[events_df["matchId"] == match_id].sort_values("eventSec").reset_index(drop=True)
        match_passes = passes_df[passes_df["matchId"] == match_id]
        for _, p in match_passes.iterrows():
            possibles = match_events[
                (match_events["playerId"] == p["playerId"]) &
                (abs(match_events["x"] - p["x"]) < 1e-3) &
                (abs(match_events["y"] - p["y"]) < 1e-3) &
                (match_events["eventName"] == "Pass")
            ]
            if possibles.empty:
                xa_list.append(0)
                continue
            event_idx = possibles.index[0]
            next_events = match_events.iloc[event_idx+1 : event_idx+1+max_suivants]
            if (next_events["eventName"] == "Shot").any():
                shot_idx = next_events[next_events["eventName"]=="Shot"].index[0]
                xa_score = 1 - (shot_idx - event_idx - 1)*0.3
                xa_list.append(xa_score)
            else:
                xa_list.append(0)
    passes_df["xA"] = xa_list
    return passes_df

# --- Filtrer les passes du joueur ---
player_passes = passes_df[passes_df["playerName"] == player_name].dropna(subset=["x","y","end_x","end_y"])
player_passes = passes_vers_tir(player_passes, events_df, max_suivants=max_suivants)
player_passes = xa_approx(player_passes, events_df, max_suivants=2)

# Calculer distance et garder seulement passes vers l’avant
player_passes["distance"] = ((player_passes["end_x"] - player_passes["x"])**2 +
                             (player_passes["end_y"] - player_passes["y"])**2)**0.5
player_passes = player_passes[(player_passes["end_x"] > player_passes["x"])]
player_passes = player_passes.sort_values(by="distance", ascending=False).head(60)

# Top passes xA pour flèches jaunes
high_xa_passes = player_passes[player_passes["xA"] > 0]
high_xa_passes = high_xa_passes.sort_values(by="xA", ascending=False).head(15)

# Touches du joueur
player_touches = events_df[events_df["playerName"] == player_name].dropna(subset=["x","y"])

# --- Tracer le terrain ---
fig, ax = plt.subplots(figsize=(12,8))
ax.add_patch(patches.Rectangle((0,0),100,100,facecolor="#e6f2e6", edgecolor="black"))
ax.add_patch(patches.Rectangle((0,20),16.5,60,fill=False,edgecolor="white",linewidth=2))
ax.add_patch(patches.Rectangle((100-16.5,20),16.5,60,fill=False,edgecolor="white",linewidth=2))
ax.add_patch(patches.Circle((50,50),9.15,fill=False,edgecolor="white",linewidth=2))

# Heatmap rouge des touches
sns.kdeplot(
    x=player_touches["x"],
    y=player_touches["y"],
    fill=True,
    cmap="Reds",
    alpha=0.8,
    levels=50,
    thresh=0.1,
    ax=ax
)

# Flèches bleues pour passes vers l’avant
for _, row in player_passes.iterrows():
    ax.arrow(
        row["x"], row["y"],
        row["end_x"] - row["x"],
        row["end_y"] - row["y"],
        head_width=1.5, head_length=1.5,
        color="blue", alpha=0.6, linewidth=1,
        length_includes_head=True
    )

# Flèches jaunes pour passes xA approximatif
for _, row in high_xa_passes.iterrows():
    ax.arrow(
        row["x"], row["y"],
        row["end_x"] - row["x"],
        row["end_y"] - row["y"],
        head_width=1.8, head_length=1.8,
        color="yellow", alpha=0.9, linewidth=2,
        length_includes_head=True
    )

# Axes et titre
ax.set_xlim(0,100)
ax.set_ylim(0,100)
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_title(f"Touches (rouge), passes vers l’avant (bleu), passes xA (jaune) de {player_name}")
ax.set_aspect('equal')
plt.show()

metrics = passes_df.groupby("playerName").agg(
    total_passes_forward=("distance", "count"),
    avg_distance=("distance", "mean"),
    total_xA=("xA", "sum"),
    mean_xA=("xA", "mean"),
    passes_toward_shot=("xA", lambda x: (x>0).sum())
).reset_index()

# Trier par total_xA ou passes_toward_shot pour trouver les joueurs les plus influents
top_players = metrics.sort_values(by=["total_xA", "passes_toward_shot"], ascending=False).head(20)

print(top_players)
