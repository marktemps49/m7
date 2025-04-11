
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode
import pandas as pd
import streamlit as st

st.title("Masters Pool Leaderboard")

# Dictionary to store leaderboard data
leaderboard_data = {}

# Fetch the page from the livegolfapi documentation (HTML content only)
url = "https://livegolfapi.com/documentation/tournaments/ae6be747-74ff-4ec0-bf15-52644a0bd19f"
headers = {
    "User-Agent": "Mozilla/5.0"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

# Attempt to extract any table rows from the documentation page
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

# Streamlit file upload
uploaded_file = st.file_uploader("Upload your picks Excel file", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Ensure the dataframe includes required columns
    if 'Name' not in df.columns or not any(col.startswith("Pick") for col in df.columns):
        st.error("The Excel file must include a 'Name' column and at least one 'Pick' column.")
    else:
        pick_columns = [col for col in df.columns if col.startswith("Pick")]

        # Normalize and score picks
        def get_score(player_name):
            normalized = unidecode(player_name).lower().strip()
            return leaderboard_data.get(normalized, 100)

        for col in pick_columns:
            df[f"{col} (Pos)"] = df[col].apply(get_score)

        df['Total'] = df[[f"{col} (Pos)" for col in pick_columns]].sum(axis=1)
        df = df.sort_values(by='Total')

        st.dataframe(df)
        st.download_button("Download Results", df.to_csv(index=False), file_name="scored_picks.csv")
