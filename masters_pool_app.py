# Masters 2025 Leaderboard Scoring App
# Streamlit app

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Masters 2025 Pool Leaderboard", layout="wide")
st.title("🏌️‍♂️ Masters 2025 Pool Leaderboard")

uploaded_file = st.file_uploader("Upload Excel file with player picks", type=["xlsx"])

@st.cache_data(ttl=300)
def fetch_leaderboard():
    url = "https://www.masters.com/en_US/scores/index.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "lxml")

    leaderboard_data = {}
    script_tags = soup.find_all("script")

    for script in script_tags:
        if "masters.scoringData" in script.text:
            try:
                raw_json = re.search(r'masters\.scoringData\s*=\s*(\{.*?\});', script.text, re.DOTALL)
                if raw_json:
                    import json
                    data = json.loads(raw_json.group(1))
                    players = data.get("players", [])
                    for idx, player in enumerate(sorted(players, key=lambda x: (x.get("posNum", 999), x.get("lastName", "")))):
                        name = f"{player['firstName']} {player['lastName']}"
                        position = player.get("posNum", 60)
                        leaderboard_data[name] = idx + 1
            except Exception as e:
                st.error("Error parsing leaderboard data: " + str(e))
            break

    return leaderboard_data


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
