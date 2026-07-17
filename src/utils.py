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


def prob_color_continuous(prob, max_prob=25.0):
    t = min(prob / max_prob, 1.0)
    hue = int(t * 120)  # 0 = red, 120 = green
    return f"hsl({hue}, 70%, 42%)"


def create_results_csv(drafts):
    rows = []
    for player, teams in drafts.items():
        for pick, team in enumerate(teams, start=1):
            rows.append({"Drafter": player, "Pick": pick, "Team": team})
    return pd.DataFrame(rows)
