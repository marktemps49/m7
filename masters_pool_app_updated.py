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
    url = "https://www.espn.com/golf/leaderboard"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "lxml")
    table = soup.find("table")

    golfer_positions = []
    if not table:
        return golfer_positions

    seen_golfers = set()

    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 3:
            continue
        pos = cols[0].text.strip()
        name = cols[2].text.strip()

        if name in seen_golfers:
            continue
        seen_golfers.add(name)

        # Normalize T ties (e.g., T2 -> 2)
        if "T" in pos:
            pos = pos.replace("T", "")
        try:
            rank = int(pos)
        except:
            rank = 60  # default for CUT, WD, etc.

        golfer_positions.append((name, rank))

    # Resolve ties by sorting alphabetically on name within same position
    golfer_positions.sort(key=lambda x: (x[1], x[0].split()[-1]))

    # Assign unique ranks
    final_positions = {}
    for idx, (name, _) in enumerate(golfer_positions):
        final_positions[name] = idx + 1

    return final_positions


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
