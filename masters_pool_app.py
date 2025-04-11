# Masters 2025 Leaderboard Scoring App
# Streamlit app using Free Live Golf API

import streamlit as st
import pandas as pd
import re
from unidecode import unidecode
import re

st.set_page_config(page_title="Masters 2025 Pool Leaderboard", layout="wide")
st.title("🏉️ Masters 2025 Pool Leaderboard")

uploaded_file = st.file_uploader("Upload Excel file with player picks", type=["xlsx"])

USE_MOCK_DATA = True

@st.cache_data(ttl=300)  # Toggle this to use simulated leaderboard data

def fetch_leaderboard():
    API_KEY = "905eba9f02494df58608deff8541236d"
    if USE_MOCK_DATA:
        st.info("Using mock leaderboard data.")
        leaderboard_data = {
            "Justin Rose": 1,
            "Scottie Scheffler": 2,
            "Ludvig Åberg": 2,
            "Corey Conners": 2,
            "Bryson DeChambeau": 5,
            "Tyrrell Hatton": 5,
            "Jason Day": 7,
            "Akshay Bhatia": 7,
            "Aaron Rai": 7,
            "Harris English": 7,
            "Denny McCarthy": 11,
            "Fred Couples": 11,
            "Davis Thompson": 11,
            "Brian Harman": 11,
            "Patrick Reed": 11,
            "Viktor Hovland": 11,
            "Matt McCarty": 11,
            "Sungjae Im": 11,
            "Cameron Smith": 11,
            "Matt Fitzpatrick": 11,
            "Min Woo Lee": 11,
            "Daniel Berger": 11,
            "Max Greyserman": 11,
            "Shane Lowry": 11,
            "Michael Kim": 11,
            "Bubba Watson": 11,
            "Sahith Theegala": 27,
            "Cameron Young": 27,
            "Maverick McNealy": 27,
            "Sergio Garcia": 27,
            "Brian Campbell": 27,
            "Stephan Jaeger": 27,
            "Rory McIlroy": 27,
            "Zach Johnson": 27,
            "Collin Morikawa": 27,
            "Joaquin Niemann": 27,
            "Tom Hoge": 27,
            "Hiroshi Tai (a)": 38,
            "Nick Taylor": 38,
            "Rasmus Højgaard": 38,
            "Nico Echavarria": 38,
            "Adam Schenk": 38,
            "Sam Burns": 38,
            "Justin Thomas": 38,
            "Jordan Spieth": 38,
            "Tom Kim": 38,
            "Tommy Fleetwood": 38,
            "Hideki Matsuyama": 38,
            "Xander Schauffele": 38,
            "Davis Riley": 38,
            "Charl Schwartzel": 51,
            "Bernhard Langer": 51,
            "Will Zalatoris": 51,
            "Byeong Hun An": 51,
            "Keegan Bradley": 51,
            "Cam Davis": 51,
            "Max Homa": 51,
            "J.J. Spaun": 51,
            "Dustin Johnson": 51,
            "Patrick Cantlay": 51,
            "Brooks Koepka": 51,
            "J.T. Poston": 51,
            "Mike Weir": 63,
            "Jhonattan Vegas": 63,
            "Ángel Cabrera": 63,
            "Rafael Campos": 63,
            "Jon Rahm": 63,
            "Tony Finau": 63,
            "Phil Mickelson": 63,
            "Danny Willett": 63,
            "Robert MacIntyre": 63,
            "Chris Kirk": 63,
            "Nicolai Højgaard": 73,
            "Jose Luis Ballester Barrio (a)": 73,
            "Wyndham Clark": 73,
            "Joe Highsmith": 73,
            "Christiaan Bezuidenhout": 73,
            "Justin Hastings (a)": 73,
            "Kevin Yu": 73,
            "Austin Eckroat": 73,
            "Laurie Canter": 81,
            "Evan Beck (a)": 81,
            "José María Olazábal": 81,
            "Taylor Pendrith": 81,
            "Billy Horschel": 81,
            "Adam Scott": 81,
            "Sepp Straka": 87,
            "Matthieu Pavon": 87,
            "Lucas Glover": 87,
            "Noah Kent (a)": 90,
            "Thomas Detry": 90,
            "Thriston Lawrence": 90,
            "Russell Henley": 90,
            "Patton Kizzire": 90,
            "Nick Dunlap": 95
        }
        return leaderboard_data

    try:
        pass  # Live API logic would go here
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

    # Normalize leaderboard
    normalized_lb = {unidecode(name).lower().strip(): pos for name, pos in leaderboard.items()}

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
            normalized_name = unidecode(stripped_pick).lower().strip()
            st.write(f"Looking up: '{normalized_name}'")
            st.write(f"Found in leaderboard: {normalized_name in normalized_lb}")
            st.write(f"Normalized leaderboard keys: {list(normalized_lb.keys())[:10]}")
            score = normalized_lb.get(normalized_name, 100)
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
