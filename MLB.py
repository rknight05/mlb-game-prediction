import pandas as pd
import numpy as np
import requests
from datetime import date, timedelta
API_KEY = "insert api key here"
team_codes = {
    "Atlanta": "ATL",
    "Arizona": "ARI",
    "Baltimore": "BAL",
    "Boston": "BOS",
    "Chi Cubs": "CHC",
    "Chi Sox": "CWS",
    "Cincinnati": "CIN",
    "Cleveland": "CLE",
    "Colorado": "COL",
    "Detroit": "DET",
    "Houston": "HOU",
    "Kansas City": "KCR",
    "LA Angels": "LAA",
    "LA Dodgers": "LAD",
    "Miami": "MIA",
    "Milwaukee": "MIL",
    "Minnesota": "MIN",
    "NY Mets": "NYM",
    "NY Yankees": "NYY",
    "Sacramento": "ATH",
    "Philadelphia": "PHI",
    "Pittsburgh": "PIT",
    "San Diego": "SDP",
    "Seattle": "SEA",
    "SF Giants": "SFG",
    "St. Louis": "STL",
    "Tampa Bay": "TBR",
    "Texas": "TEX",
    "Toronto": "TOR",
    "Washington": "WSN"
}
odds_team_names = {
    "Atlanta": "Atlanta Braves",
    "Arizona": "Arizona Diamondbacks",
    "Baltimore": "Baltimore Orioles",
    "Boston": "Boston Red Sox",
    "Chi Cubs": "Chicago Cubs",
    "Chi Sox": "Chicago White Sox",
    "Cincinnati": "Cincinnati Reds",
    "Cleveland": "Cleveland Guardians",
    "Colorado": "Colorado Rockies",
    "Detroit": "Detroit Tigers",
    "Houston": "Houston Astros",
    "Kansas City": "Kansas City Royals",
    "LA Angels": "Los Angeles Angels",
    "LA Dodgers": "Los Angeles Dodgers",
    "Miami": "Miami Marlins",
    "Milwaukee": "Milwaukee Brewers",
    "Minnesota": "Minnesota Twins",
    "NY Mets": "New York Mets",
    "NY Yankees": "New York Yankees",
    "Sacramento": "Athletics",
    "Philadelphia": "Philadelphia Phillies",
    "Pittsburgh": "Pittsburgh Pirates",
    "San Diego": "San Diego Padres",
    "Seattle": "Seattle Mariners",
    "SF Giants": "San Francisco Giants",
    "St. Louis": "St. Louis Cardinals",
    "Tampa Bay": "Tampa Bay Rays",
    "Texas": "Texas Rangers",
    "Toronto": "Toronto Blue Jays",
    "Washington": "Washington Nationals"
}
bullpen_codes = {
    "Atlanta": "ATL",
    "Arizona": "AZ",
    "Baltimore": "BAL",
    "Boston": "BOS",
    "Chi Cubs": "CHC",
    "Chi Sox": "CWS",
    "Cincinnati": "CIN",
    "Cleveland": "CLE",
    "Colorado": "COL",
    "Detroit": "DET",
    "Houston": "HOU",
    "Kansas City": "KC",
    "LA Angels": "LAA",
    "LA Dodgers": "LAD",
    "Miami": "MIA",
    "Milwaukee": "MIL",
    "Minnesota": "MIN",
    "NY Mets": "NYM",
    "NY Yankees": "NYY",
    "Sacramento": "ATH",
    "Philadelphia": "PHI",
    "Pittsburgh": "PIT",
    "San Diego": "SD",
    "Seattle": "SEA",
    "SF Giants": "SF",
    "St. Louis": "STL",
    "Tampa Bay": "TB",
    "Texas": "TEX",
    "Toronto": "TOR",
    "Washington": "WSH"
}
#runs per game
url = "https://www.teamrankings.com/mlb/stat/runs-per-game"

tables = pd.read_html(url)
runs = tables[0]

def get_rpg(team):
    result = runs.loc[
        runs["Team"].str.strip().str.lower() == team.strip().lower(),
        "2026"
    ]

    if result.empty:
        print("Team not found in RPG table:", team)
        return None

    return result.iloc[0]

teamA = input("Team A: ")
teamB = input("Team B: ")

rpgA = get_rpg(teamA)
rpgB = get_rpg(teamB)

#last 3 rpg
def get_rpg3(team):
    return runs.loc[
        runs["Team"] == team,
        "Last 3"
    ].iloc[0]
rpgA3 = get_rpg3(teamA)
rpgB3 = get_rpg3(teamB)

today = date.today()

# Go back 30 days.
# This gives us plenty of games to find the last 10
# for every team.
start_date = today - timedelta(days=30)

# MLB Stats API
url = "https://statsapi.mlb.com/api/v1/schedule"

params = {
    "sportId": 1,
    "season": today.year,
    "gameTypes": "R",
    "startDate": start_date.strftime("%Y-%m-%d"),
    "endDate": today.strftime("%Y-%m-%d"),
    "hydrate": "linescore"
}

# --------------------------------------------------
# GET DATA
# --------------------------------------------------



response = requests.get(url, params=params)

if response.status_code != 200:
    print("Error getting data.")
    print("Status code:", response.status_code)
    exit()

data = response.json()

# --------------------------------------------------
# EXTRACT GAMES
# --------------------------------------------------

games = []

for date_data in data.get("dates", []):

    for game in date_data.get("games", []):

        # Only completed games
        if game["status"]["abstractGameState"] != "Final":
            continue

        # Get team names
        away_team = game["teams"]["away"]["team"]["name"]
        home_team = game["teams"]["home"]["team"]["name"]

        # Get scores
        away_score = game["teams"]["away"].get("score")
        home_score = game["teams"]["home"].get("score")

        # If scores aren't included, use linescore
        if away_score is None or home_score is None:

            linescore = game.get("linescore")

            if linescore is None:
                continue

            away_score = linescore["teams"]["away"]["runs"]
            home_score = linescore["teams"]["home"]["runs"]

        # Add away team
        games.append({
            "date": game["officialDate"],
            "gamePk": game["gamePk"],
            "team": away_team,
            "runs": away_score
        })

        # Add home team
        games.append({
            "date": game["officialDate"],
            "gamePk": game["gamePk"],
            "team": home_team,
            "runs": home_score
        })


# --------------------------------------------------
# CREATE DATAFRAME
# --------------------------------------------------

df = pd.DataFrame(games)

if df.empty:
    print("No completed games were found.")
    exit()

# Convert date to datetime
df["date"] = pd.to_datetime(df["date"])

# Sort newest games first
df = df.sort_values(
    ["team", "date"],
    ascending=[True, False]
)

# --------------------------------------------------
# GET LAST 10 GAMES FOR EACH TEAM
# --------------------------------------------------

last10 = df.groupby("team").head(10).copy()

# --------------------------------------------------
# CALCULATE RUNS PER GAME
# --------------------------------------------------

last10_rpg = (
    last10
    .groupby("team")["runs"]
    .mean()
    .round(2)
    .reset_index()
)


#runs allowed per game
url2 = "https://www.teamrankings.com/mlb/stat/opponent-runs-per-game"
tables2 = pd.read_html(url2)
runsallowed = tables2[0]
def get_rag(team):
    return runsallowed.loc[
        runsallowed["Team"] == team,
        "2026"
    ].iloc[0]

ragA = get_rag(teamA)
ragB = get_rag(teamB)

#last 3 rag
def get_rag3(team):
    return runsallowed.loc[
        runsallowed["Team"] == team,
        "Last 3"
    ].iloc[0]
ragA3 = get_rag3(teamA)
ragB3 = get_rag3(teamB)

#pitcher era
url3 = "https://www.baseball-reference.com/leagues/majors/2026-standard-pitching.shtml#all_players_standard_pitching"
tables3 = pd.read_html(url3)
pitching = tables3[1]
def get_era(name):
    result = pitching.loc[
        pitching["Player"].str.replace("*", "", regex=False).str.strip().str.lower()
        == name.strip().lower(),
        ["Player", "Team", "ERA"]
    ]

    if result.empty:
        print("Pitcher not found:", name)
        return None

    # If the pitcher played for multiple teams, use the combined season row
    combined = result[result["Team"].str.contains("TM", na=False)]

    if not combined.empty:
        return combined.iloc[0]["ERA"]

    # Otherwise, use the only row
    return result.iloc[0]["ERA"]

pitcherA = input(f"{teamA} pitcher: ")
pitcherB = input(f"{teamB} pitcher: ")

eraA = float(get_era(pitcherA))
eraB = float(get_era(pitcherB))

#bullpen stuff
url4 = "https://insidethepen.com/bullpen-rankings-season-long.html"
tables4 = pd.read_html(url4)
bullpen = tables4[0]
teamA_code = team_codes[teamA]
teamB_code = team_codes[teamB]
def get_bullpen_era(team_code):
    result = bullpen.loc[
        bullpen["Tm"] == team_code,
        "Season ERA"
    ]

    if result.empty:
        print("Bullpen team not found:", team_code)
        return None

    return result.iloc[0]
bullpen_teamA = bullpen_codes[teamA]
bullpen_teamB = bullpen_codes[teamB]
bullpenA = float(get_bullpen_era(bullpen_teamA))
bullpenB = float(get_bullpen_era(bullpen_teamB))

# pitcher innings/game
def get_ip_per_game(name):
    result = pitching.loc[
        pitching["Player"].str.replace("*", "", regex=False).str.strip().str.lower()
        == name.strip().lower(),
        ["Player", "Team", "IP", "G"]
    ]
    if result.empty:
        print("Pitcher not found:", name)
        return None
    # Use combined season row if pitcher played for multiple teams
    combined = result[result["Team"].str.contains("TM", na=False)]
    if not combined.empty:
        row = combined.iloc[0]
    else:
        row = result.iloc[0]
    ip = row["IP"]
    games = row["G"]
    # Convert Baseball-Reference innings notation to actual innings
    whole = int(ip)
    fraction = round(ip - whole, 1)

    if fraction == 0.1:
        actual_ip = whole + 1/3
    elif fraction == 0.2:
        actual_ip = whole + 2/3
    else:
        actual_ip = whole
    return actual_ip / games

ipgA = get_ip_per_game(pitcherA)
ipgB = get_ip_per_game(pitcherB)
ipgAround = round(ipgA, 2)
ipgBround = round(ipgB, 2)
projected_runs_allowedA = round((ipgAround*eraA/9)+((9-ipgAround)*bullpenA/9),2)
projected_runs_allowedB = round((ipgBround*eraB/9)+((9-ipgBround)*bullpenB/9),2)


# RPG, RPG3, RAG, RAG3, ERAstuff
scoreA = rpgA*0.25 + rpgA3*0.15 + ragB*0.25 + ragB3*0.15 + projected_runs_allowedB*0.20
scoreB = rpgB*0.25 + rpgB3*0.15 + ragA*0.25 + ragA3*0.15 + projected_runs_allowedA*0.20

simulations = 100000
runs_A = np.random.poisson(scoreA, simulations)
runs_B = np.random.poisson(scoreB, simulations)
teamA_wins = np.sum(runs_A > runs_B)
teamB_wins = np.sum(runs_B > runs_A)
ties = np.sum(runs_A == runs_B)
teamA_probability = (teamA_wins + ties / 2) / simulations
teamB_probability = (teamB_wins + ties / 2) / simulations
#print(teamA, "win probability:", teamA_probability)
#print(teamB, "win probability:", teamB_probability)
def probability_to_american(probability):
    if probability >= 0.5:
        odds = round(-(probability / (1 - probability)) * 100)
    else:
        odds = round(((1 - probability) / probability) * 100)
    if odds > 0:
        return "+" + str(odds)
    else:
        return str(odds)
#print("Team A odds:", probability_to_american(teamA_probability))
#print("Team B odds:", probability_to_american(teamB_probability))

odds_teamA = odds_team_names[teamA]
odds_teamB = odds_team_names[teamB]
def get_sportsbook_odds(teamA, teamB):

    url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

    params = {
        "apiKey": API_KEY,
        "regions": "us",
        "markets": "h2h",
        "oddsFormat": "american"
    }

    response = requests.get(url, params=params)

    print("API status:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return

    games = response.json()

    for game in games:

        home = game["home_team"]
        away = game["away_team"]

        if (teamA == home or teamA == away) and \
           (teamB == home or teamB == away):

            for bookmaker in game["bookmakers"]:

                if bookmaker["key"] == "draftkings":

                    for market in bookmaker["markets"]:

                        if market["key"] == "h2h":

                            odds = {}

                            for outcome in market["outcomes"]:
                                odds[outcome["name"]] = outcome["price"]

                            return odds

            print("DraftKings odds not available.")
            return None

    print("Game not found.")
    return None

draftkings_odds = get_sportsbook_odds(odds_teamA, odds_teamB)

#print("DraftKings odds:", draftkings_odds)
def amer_to_prob(odds):
    if odds < 0:
        return -odds / (-odds + 100)
    else:
        return 100 / (odds + 100)
dk_teamA_prob = amer_to_prob(
    draftkings_odds[odds_teamA]
)
dk_teamB_prob = amer_to_prob(
    draftkings_odds[odds_teamB]
)
teamA_edge = round(teamA_probability - dk_teamA_prob,4) 
teamB_edge = round(teamB_probability - dk_teamB_prob,4) 
print(teamA, "edge:", f"{teamA_edge:.2%}")
print(teamB, "edge:", f"{teamB_edge:.2%}")
#print("Remember: + edge is what you're looking for")
print(teamA, "actual odds:", draftkings_odds[odds_teamA])
print(teamB, "actual odds:", draftkings_odds[odds_teamB])
