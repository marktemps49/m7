
# Masters 2025 Leaderboard Scoring App
# Streamlit app using Free Live Golf API

import streamlit as st
import pandas as pd
import re
from unidecode import unidecode
import requests

st.set_page_config(page_title="Masters 2025 Pool Leaderboard", layout="wide")
st.title("🏉️ Masters 2025 Pool Leaderboard")

uploaded_file = st.file_uploader("Upload Excel file with player picks", type=["xlsx"])

USE_MOCK_DATA = False

@st.cache_data(ttl=300)
def fetch_leaderboard():
    if USE_MOCK_DATA:
        st.info("Using mock leaderboard data.")
        leaderboard_data = {
            "justin rose": 1,
            "scottie scheffler": 2,
            "ludvig aberg": 2,
            # ... continue mock data ...
        }
        return leaderboard_data
    else:
        try:
            url = "https://livegolfapi.com/api/v1/tournaments/ae6be747-74ff-4ec0-bf15-52644a0bd19f/leaderboard"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            leaderboard_data = {}
            for player in data.get("players", []):
                name = player.get("name", "")
                position = player.get("position", "100")
                if isinstance(position, str) and position.startswith("T"):
                    position = position[1:]
                try:
                    position = int(position)
                except:
                    position = 100
                normalized_name = unidecode(name).lower().strip()
                leaderboard_data[normalized_name] = position

            return leaderboard_data
        except Exception as e:
            st.warning(f"Failed to fetch live leaderboard: {e}")
            return {}

def extract_player_name(entry):
    if pd.isna(entry):
        return None
    match = re.match(r"\d+\s*-\s*(.*)", str(entry).strip())
    return match.group(1) if match else entry.strip()

def process_file(df, leaderboard):
    name_col = "Name"
    pick_columns = [col for col in df.columns if "Ranking" in col]

    normalized_lb = {
        unidecode(name).lower().strip(): score for name, score in leaderboard.items()
    }

    user_scores = []
    seen_users = set()
    for _, row in df.iterrows():
        user = row[name_col]
        if user in seen_users:
            continue
        seen_users.add(user)

        picks = [extract_player_name(row[col]) for col in pick_columns if extract_player_name(row[col])]
        pick_scores = []
        unmatched = []
        for pick in picks:
            normalized_name = unidecode(pick).lower().strip()
            score = normalized_lb.get(normalized_name)
            if score is None:
                unmatched.append(pick)
                score = 100
            pick_scores.append((pick, score))

        total_score = sum(score for _, score in pick_scores)

        user_result = {"Player": user, "Total Score": total_score, "Unmatched Picks": ", ".join(unmatched)}
        for i, (pick, score) in enumerate(pick_scores, 1):
            user_result[f"Pick {i}"] = f"{pick} ({score})"

        user_scores.append(user_result)

    df_result = pd.DataFrame(user_scores).sort_values("Total Score").reset_index(drop=True)
    df_result.index += 1
    return df_result

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    leaderboard = fetch_leaderboard()
    results_df = process_file(df, leaderboard)

    st.success("Leaderboard generated successfully!")
    st.dataframe(results_df, use_container_width=True)

    csv_data = results_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Results as CSV", data=csv_data,
                       file_name="masters2025_leaderboard.csv", mime="text/csv")
else:
    st.info("Please upload the Excel file containing picks to begin.")
