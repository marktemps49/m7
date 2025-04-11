# Masters 2025 Leaderboard Scoring App
# Enhanced version with better name matching and error handling

import streamlit as st
import pandas as pd
import re
from unidecode import unidecode
import openpyxl

# Configure the app
st.set_page_config(page_title="Masters 2025 Pool Leaderboard", layout="wide")
st.title("🏌️ Masters 2025 Pool Leaderboard")

# File uploader
uploaded_file = st.file_uploader("Upload Excel file with player picks", type=["xlsx"])

# Settings
USE_MOCK_DATA = True
DEFAULT_SCORE = 100  # Score for players not found in leaderboard

@st.cache_data(ttl=300)
def fetch_leaderboard():
    """Fetch or mock the current tournament leaderboard"""
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
        # Placeholder for live API integration
        # API_KEY = "your_api_key_here"
        # Implement actual API call here
        return {}
    except Exception as e:
        st.error(f"Failed to fetch leaderboard data: {e}")
        return {}

def normalize_name(name):
    """Normalize player names for consistent matching"""
    if pd.isna(name) or not isinstance(name, str):
        return None
    
    # Handle "Player Not Listed" cases
    if "player not listed" in name.lower():
        match = re.search(r"player not listed\s*(?:-\s*)?(.*)", name, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    # Remove ranking prefixes (e.g., "1 - Scottie Scheffler")
    name = re.sub(r"^\d+\s*-\s*", "", name).strip()
    
    # Remove amateur designation and other parentheticals
    name = re.sub(r"\s*\(.*?\)", "", name)
    
    # Normalize special characters and lowercase
    name = unidecode(name).lower().strip()
    
    # Common name corrections
    corrections = {
        "phil mickleson": "phil mickelson",
        "alex noren": "alex noren",
        "joaquin niemann": "joaquin niemann",
        "sergio garcia": "sergio garcia",
        "byoung hun an": "byeong hun an",
        "byung hun an": "byeong hun an",
    }
    
    return corrections.get(name, name)

def process_picks_file(df, leaderboard):
    """Process the picks file and calculate scores"""
    # Normalize leaderboard names for matching
    normalized_lb = {normalize_name(name): pos for name, pos in leaderboard.items()}
    
    # Find name column (case insensitive)
    name_col = next((col for col in df.columns if "name" in col.lower()), None)
    if not name_col:
        st.error("Could not find 'Name' column in the uploaded file")
        return None
    
    # Find pick columns (all columns containing "Ranking")
    pick_columns = [col for col in df.columns if "ranking" in col.lower()]
    if len(pick_columns) != 7:
        st.warning(f"Expected 7 pick columns, found {len(pick_columns)}")
    
    results = []
    seen_users = set()
    
    for _, row in df.iterrows():
        user = row[name_col]
        if pd.isna(user) or user in seen_users:
            continue
        
        seen_users.add(user)
        picks = []
        
        # Process each pick
        for col in pick_columns:
            pick = row[col]
            normalized_pick = normalize_name(pick)
            
            if normalized_pick:
                # Find the best matching player in leaderboard
                score = None
                original_name = pick
                
                # First try exact match
                if normalized_pick in normalized_lb:
                    score = normalized_lb[normalized_pick]
                    original_name = next(k for k in leaderboard if normalize_name(k) == normalized_pick)
                else:
                    # Try partial matching as fallback
                    for lb_name, lb_score in normalized_lb.items():
                        if normalized_pick in lb_name or lb_name in normalized_pick:
                            score = lb_score
                            original_name = next(k for k in leaderboard if normalize_name(k) == lb_name)
                            break
                
                picks.append({
                    "original": original_name,
                    "normalized": normalized_pick,
                    "score": score if score is not None else DEFAULT_SCORE
                })
        
        # Calculate total score
        total_score = sum(pick["score"] for pick in picks) if picks else 0
        
        # Prepare result row
        result_row = {
            "Player": user,
            "Total Score": total_score
        }
        
        # Add individual picks
        for i, pick in enumerate(picks[:7], 1):
            result_row[f"Pick {i}"] = f"{pick['original']} ({pick['score']})"
        
        # Fill missing picks
        for i in range(len(picks) + 1, 8):
            result_row[f"Pick {i}"] = "N/A"
        
        results.append(result_row)
    
    if not results:
        st.error("No valid entries found in the file")
        return None
    
    # Create DataFrame and sort by total score
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("Total Score").reset_index(drop=True)
    results_df.index += 1  # Make ranking start at 1
    
    return results_df

def main():
    if uploaded_file:
        try:
            # Read the Excel file
            with pd.ExcelFile(uploaded_file) as xls:
                # Try to find the sheet with picks data
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    
                    # Check if this sheet has picks data
                    if any("ranking" in col.lower() for col in df.columns):
                        leaderboard = fetch_leaderboard()
                        
                        if not leaderboard:
                            st.error("No leaderboard data available")
                            return
                        
                        results_df = process_picks_file(df, leaderboard)
                        
                        if results_df is not None:
                            st.success("Leaderboard generated successfully!")
                            
                            # Display results
                            st.dataframe(
                                results_df,
                                use_container_width=True,
                                column_config={
                                    "Player": st.column_config.TextColumn(width="medium"),
                                    "Total Score": st.column_config.NumberColumn(width="small"),
                                    **{f"Pick {i}": st.column_config.TextColumn(width="large") 
                                       for i in range(1, 8)}
                                }
                            )
                            
                            # Download button
                            st.download_button(
                                "Download Results as CSV",
                                data=results_df.to_csv(index=False),
                                file_name="masters2025_leaderboard.csv",
                                mime="text/csv"
                            )
                        return
                
                st.error("Could not find a sheet with pick data in the uploaded file")
        
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    else:
        st.info("Please upload the Excel file containing picks to begin.")

if __name__ == "__main__":
    main()
