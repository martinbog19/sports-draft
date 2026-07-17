import pandas as pd


def prob_color(prob):
    if prob >= 25:
        return "green"
    elif prob >= 10:
        return "yellow"
    elif prob >= 5:
        return "orange"
    else:
        return "red"


def create_results_csv(drafts):
    rows = []
    for player, teams in drafts.items():
        for pick, team in enumerate(teams, start=1):
            rows.append({"Drafter": player, "Pick": pick, "Team": team})
    return pd.DataFrame(rows)
