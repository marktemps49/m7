
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode
import pandas as pd
import streamlit as st

st.title("Masters Pool Leaderboard")

# Step 1: Scrape leaderboard data
leaderboard_data = {}
url = "https://livegolfapi.com/documentation/tournaments/ae6be747-74ff-4ec0-bf15-52644a0bd19f"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

rows = soup.find_all("tr")
for row in rows:
    cols = row.find_all("td")
    if len(cols) < 2:
        continue
    position = cols[0].text.strip()
    name = cols[1].text.strip()

    if position.startswith("T"):
        position = position[1:]
    try:
        position = int(position)
    except:
        position = 100

    normalized_name = unidecode(name).lower().strip()
    leaderboard_data[normalized_name] = position

# Step 2: Upload and process Excel file
uploaded_file = st.file_uploader("Upload your picks Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    pick_columns = [col for col in df.columns if "Ranking" in col]
    
    def extract_name(entry):
        if pd.isna(entry):
            return ""
        return unidecode(str(entry)).split("-", 1)[-1].strip()

    def get_score(player_name):
        norm = unidecode(player_name).lower().strip()
        return leaderboard_data.get(norm, 100)

    for col in pick_columns:
        df[f"{col} (Pos)"] = df[col].apply(lambda x: get_score(extract_name(x)))

    df["Total"] = df[[f"{col} (Pos)" for col in pick_columns]].sum(axis=1)
    df = df.sort_values("Total")
    
    st.dataframe(df)
    st.download_button("Download Scored Picks", df.to_csv(index=False), file_name="scored_picks.csv")
