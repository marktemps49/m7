
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
    leaderboard_data[normalized_name] = (position, name)

# Load entry picks from the repo file directly
entry_file_path = "Masters2025_Entries.xlsx"
df = pd.read_excel(entry_file_path)

# Gather all columns containing rankings
ranking_columns = [
    "Ranking 1-10",
    "Ranking 11-20",
    "Ranking 21-30",
    "Ranking 31-40",
    "Ranking 41-50",
    "Ranking 51-75",
    "Ranking >75"
]

if 'Name' not in df.columns or not all(col in df.columns for col in ranking_columns):
    st.error("The Excel file must include a 'Name' column and the required 'Ranking' columns.")
else:
    # Normalize and score picks
    def get_score(player_name):
        if pd.isna(player_name):
            return 100, "(100)"
        name_only = player_name.split('-')[-1].strip()
        normalized = unidecode(name_only).lower().strip()
        pos, full_name = leaderboard_data.get(normalized, (100, player_name))
        surname = full_name.split()[-1] if full_name else player_name
        return pos, f"{surname} ({pos})"

    display_columns = []
    score_columns = []
    for col in ranking_columns:
        pos_col = f"{col} (Pos)"
        df[[f"{pos_col}_score", pos_col]] = df[col].apply(lambda name: pd.Series(get_score(name)))
        score_columns.append(f"{pos_col}_score")
        display_columns.append(pos_col)

    # Sum the lowest 5 position scores
    df['Total'] = df[score_columns].apply(lambda row: sum(sorted(row)[:5]), axis=1)
    df = df.sort_values(by='Total')

    display_columns = ['Name', 'Total'] + display_columns
    st.dataframe(df[display_columns])
    st.download_button("Download Results", df[display_columns].to_csv(index=False), file_name="scored_picks.csv")
