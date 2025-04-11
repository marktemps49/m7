# Masters 2025 Leaderboard Scoring App
# Streamlit app

import streamlit as st
import pandas as pd
import requests
import re
import json

st.set_page_config(page_title="Masters 2025 Pool Leaderboard", layout="wide")
st.title("🏌️‍♂️ Masters 2025 Pool Leaderboard")

uploaded_file = st.file_uploader("Upload Excel file with player picks", type=["xlsx"])

@st.cache_data(ttl=300)
def fetch_leaderboard():
    url = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/leaderboard"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        leaderboard_data = {}
        events = data.get("events", [])
        if not events:
            raise ValueError("No event data available")

        competitions = events[0].get("competitions", [])
        if not competitions:
            raise ValueError("No competition data available")

        players = competitions[0].get("competitors", [])

        for player in players:
            athlete = player.get("athlete", {})
            first_name = athlete.get("firstName", "")
            last_name = athlete.get("lastName", "")
            name = f"{first_name} {last_name}".strip()

            position = player.get("status", {}).get("position", {}).get("id", "60")

            if position.upper() in ["CUT", "WD", "DQ"]:
                rank = 60
            else:
                try:
                    rank = int(position.replace("T", ""))
                except:
                    rank = 60

            leaderboard_data[name] = rank

        return leaderboard_data

    except Exception as e:
        st.error(f"Failed to fetch leaderboard data: {e}")
        return {}


def extract_player_name(entry):
    if pd.isna(entry):
        return None
    match = re.match(r"\d+\s*-\s*(.*)", str(entry).strip())
    return match.group(1) if match else entry.strip()


def process_file(df, leaderboard):
    name_col = "Name"
    pick_columns = [col for col in df.columns if "Ranking" in col]

    user_scores = []

    seen_users = set()
    for _, row in df.iterrows():
        user = row[name_col]
        if user in seen_users:
            continue  # Skip duplicate user entries
        seen_users.add(user)

        picks = [extract_player_name(row[col]) for col in pick_columns if extract_player_name(row[col])]
        pick_scores = [(pick, leaderboard.get(pick, 60)) for pick in picks]
        total_score = sum(score for _, score in pick_scores)

        user_result = {"Player": user, "Total Score": total_score}
        for i, (pick, score) in enumerate(pick_scores, 1):
            user_result[f"Pick {i}"] = f"{pick} ({score})"

        user_scores.append(user_result)

    return pd.DataFrame(user_scores).sort_values("Total Score").reset_index(drop=True)


if uploaded_file:
    df = pd.read_excel(uploaded_file)
    leaderboard = fetch_leaderboard()
    results_df = process_file(df, leaderboard)

    st.success("Leaderboard generated successfully!")
    st.dataframe(results_df, use_container_width=True)

    st.download_button("Download Results as CSV", data=results_df.to_csv(index=False),
                       file_name="masters2025_leaderboard.csv", mime="text/csv")
else:
    st.info("Please upload the Excel file containing picks to begin.")
