# Masters 2025 Leaderboard Scoring App
# Streamlit app using Free Live Golf API

import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="Masters 2025 Pool Leaderboard", layout="wide")
st.title("🏌️‍♂️ Masters 2025 Pool Leaderboard")

uploaded_file = st.file_uploader("Upload Excel file with player picks", type=["xlsx"])

@st.cache_data(ttl=300)
def fetch_leaderboard():
    API_KEY = "905eba9f02494df58608deff8541236d"
    try:
        events_url = f"https://use.livegolfapi.com/v1/events?api_key={API_KEY}"
        events_response = requests.get(events_url)
        if events_response.status_code != 200:
            st.error(f"Failed to fetch events: {events_response.status_code}")
            st.text(events_response.text)
            return {}

        if events_response.headers.get("Content-Type") == "application/json":
            events = events_response.json()
            st.subheader("Available Events from API:")
            st.json(events)
        else:
            st.error("Events response not JSON")
            st.text(events_response.text)
            return {}

        masters_event = next((event for event in events if "Masters Tournament" in event["name"]), None)

        if not masters_event:
            st.error("Masters Tournament not found.")
            return {}

        event_id = masters_event["id"]
        leaderboard_url = f"https://use.livegolfapi.com/v1/tournaments/{event_id}/leaderboard?api_key={API_KEY}"
        leaderboard_response = requests.get(leaderboard_url)
        if leaderboard_response.status_code != 200:
            st.error(f"Failed to fetch leaderboard: {leaderboard_response.status_code}")
            st.text(leaderboard_response.text)
            return {}

        leaderboard = leaderboard_response.json()
        st.subheader("Leaderboard Raw Data")
        st.json(leaderboard)

        leaderboard_data = {}
        for player in leaderboard.get("players", []):
            name = player.get("name", "").strip()
            pos = str(player.get("position", "100"))

            if pos.upper() in ["CUT", "WD", "DQ"]:
                rank = 100
            else:
                try:
                    rank = int(pos.replace("T", ""))
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
        pick_scores = []
        for pick in picks:
            stripped_pick = re.sub(r"^\d+\s*-\s*", "", pick).strip()
            score = leaderboard.get(stripped_pick, 100)
            pick_scores.append((pick, score))

        total_score = sum(score for _, score in pick_scores)

        user_result = {"Player": user, "Total Score": total_score}
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

    st.download_button("Download Results as CSV", data=results_df.to_csv(index=False),
                       file_name="masters2025_leaderboard.csv", mime="text/csv")
else:
    st.info("Please upload the Excel file containing picks to begin.")
