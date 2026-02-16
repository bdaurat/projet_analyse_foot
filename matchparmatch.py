import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches


# CONFIGURATION MATPLOTLIB

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


# CHARGEMENT DES DONNÉES

with open("C:/Users/bdaur/Downloads/AD/events/events_Spain.json", encoding="utf-8") as f:
    events = json.load(f)

with open("C:/Users/bdaur/Downloads/AD/players.json", encoding="utf-8") as f:
    players = json.load(f)

with open("C:/Users/bdaur/Downloads/AD/teams.json", encoding="utf-8") as f:
    teams = json.load(f)


teams_df = pd.json_normalize(teams)[["wyId", "name"]].rename(
    columns={"wyId":"teamId","name":"teamName"}
)

players_df = pd.json_normalize(players)
players_df["playerName"] = players_df["lastName"]
def decode_unicode(text):
    if isinstance(text, str):
        try:
            return text.encode("utf-8").decode("unicode_escape")
        except:
            return text
    return text

players_df["playerName"] = players_df["playerName"].apply(decode_unicode)
players_df = players_df[["wyId","playerName"]].rename(columns={"wyId":"playerId"})

events_df = pd.json_normalize(events)
cols = ["matchId","eventName","teamId","playerId","eventSec","positions"]
events_df = events_df[cols]

# x: 0-100 → 0-105 m, y: 0-100 → 0-68 m
events_df["x"] = events_df["positions"].apply(
    lambda p: p[0]["x"]*1.05 if isinstance(p,list) else np.nan
)
events_df["y"] = events_df["positions"].apply(
    lambda p: p[0]["y"]*0.68 if isinstance(p,list) else np.nan
)
events_df["end_x"] = events_df["positions"].apply(
    lambda p: p[1]["x"]*1.05 if isinstance(p,list) and len(p)>1 else np.nan
)
events_df["end_y"] = events_df["positions"].apply(
    lambda p: p[1]["y"]*0.68 if isinstance(p,list) and len(p)>1 else np.nan
)

events_df = events_df.dropna(subset=["x","y"])

TEAM1_NAME = "Real Madrid"
TEAM2_NAME = "Sevilla"

team1_id = teams_df.loc[teams_df["teamName"]==TEAM1_NAME,"teamId"].values[0]
team2_id = teams_df.loc[teams_df["teamName"]==TEAM2_NAME,"teamId"].values[0]

team1_events = events_df[events_df["teamId"]==team1_id]
team2_events = events_df[events_df["teamId"]==team2_id]

match_id = list(set(team1_events["matchId"]) & set(team2_events["matchId"]))[0]

team1_events = team1_events[team1_events["matchId"]==match_id]
team2_events = team2_events[team2_events["matchId"]==match_id]

team1_passes = team1_events[team1_events["eventName"]=="Pass"].copy()
team2_passes = team2_events[team2_events["eventName"]=="Pass"].copy()


def get_starters(passes):
    starters = (
        passes[passes["eventSec"]<=6000]  
        .groupby("playerId").size()
        .sort_values(ascending=False)
        .head(11).index
    )
    return passes[passes["playerId"].isin(starters)]

team1_passes = get_starters(team1_passes)
team2_passes = get_starters(team2_passes)

def passing_network(ax, team_passes, team_name):

    team_passes = team_passes.merge(players_df, on="playerId", how="left")

    # positions moyennes
    player_pos = team_passes.groupby(["playerId","playerName"])[["x","y"]].mean().reset_index()

    # volume de passes par joueur
    pass_count = team_passes.groupby("playerId").size().reset_index(name="n_passes")
    player_pos = player_pos.merge(pass_count, on="playerId")

    # IDENTIFIER LE RECEVEUR (prochain événement dans le temps)
    team_passes = team_passes.sort_values("eventSec").reset_index(drop=True)
    passes = []
    for i, p in team_passes.iterrows():
        next_events = team_passes.iloc[i+1:i+5]
        if next_events.empty:
            continue
        receiver = next_events.iloc[0]["playerId"]
        if receiver != p["playerId"]:
            passes.append({
                "passer": p["playerId"],
                "receiver": receiver
            })

    passes_df = pd.DataFrame(passes)


    network = passes_df.groupby(["passer","receiver"]).size().reset_index(name="n_passes")
    network = network[network["n_passes"]>=2]  # filtrage pour lisibilité
    if network.empty:
        return

    # normalisation pour couleur
    max_passes = network["n_passes"].max()
    network["strength"] = network["n_passes"]/max_passes

    # terrain
    ax.add_patch(patches.Rectangle((0,0),105,68,facecolor="#f8f8f8",edgecolor="black"))
    # surfaces
    ax.add_patch(patches.Rectangle((0,24.85),16.5,18.3,fill=False,edgecolor="black"))  # gauche
    ax.add_patch(patches.Rectangle((105-16.5,24.85),16.5,18.3,fill=False,edgecolor="black"))  # droite
    # rond central
    ax.add_patch(patches.Circle((105/2,68/2),9.15,fill=False,edgecolor="black"))

    # joueurs
    ax.scatter(
        player_pos["x"],
        player_pos["y"],
        s=player_pos["n_passes"]*8,
        color="#f1c232",
        edgecolors="black",
        zorder=3
    )

    for _, p in player_pos.iterrows():
        ax.text(p["x"], p["y"]+1, p["playerName"], ha="center", fontsize=9, weight="bold", fontname="DejaVu Sans")

    # flèches
    for _, row in network.iterrows():
        p1 = player_pos[player_pos["playerId"]==row["passer"]].iloc[0]
        p2 = player_pos[player_pos["playerId"]==row["receiver"]].iloc[0]

        ax.arrow(
            p1["x"], p1["y"],
            p2["x"]-p1["x"], p2["y"]-p1["y"],
            linewidth=0.5 + row["n_passes"],
            color=plt.cm.RdYlGn(row["strength"]),
            alpha=0.9,
            length_includes_head=True,
            head_width=1.2,
            zorder=2
        )

    ax.set_xlim(0,105)
    ax.set_ylim(0,68)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect("equal")
    ax.set_title(team_name, fontsize=14, fontname="DejaVu Sans")


fig, axes = plt.subplots(1,2,figsize=(16,9))

passing_network(axes[0], team1_passes, TEAM1_NAME)
passing_network(axes[1], team2_passes, TEAM2_NAME)

plt.suptitle(f"Passing Network – {TEAM1_NAME} vs {TEAM2_NAME}", fontsize=18, fontname="DejaVu Sans")
plt.tight_layout()
plt.show()
