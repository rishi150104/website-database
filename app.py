import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
# Replace this with the ID from your Google Sheet URL
# Example: https://docs.google.com/spreadsheets/d/1AbC_123/edit -> ID is '1AbC_123'
SHEET_ID = "1mZRmzqJj2JQ7ustMp61GQkkabQPoyX2gE9pHZYNo1Ng/edit?gid=0#gid=0"
SHEET_NAME = "Sheet1" # Change if your tab is named differently
PASSWORD = "GuestPost2024" # Set your desired password here

# --- PAGE SETUP ---
st.set_page_config(page_title="Guest Post Database", layout="wide")

# --- PASSWORD GATE ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔐 Database Access")
    pwd_input = st.text_input("Enter Password", type="password")
    if st.button("Unlock"):
        if pwd_input == PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# --- DATA LOADING ---
@st.cache_data(ttl=600) # Refreshes data every 10 minutes
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    df = pd.read_csv(url)
    # Clean up column names (remove any extra spaces)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Could not connect to Google Sheets. Check your Sheet ID and Permissions.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Sites")

# Niche Filter (Multi-select)
all_niches = sorted(df['Niche'].dropna().unique().tolist())
selected_niches = st.sidebar.multiselect("Select Niches", all_niches, default=all_niches)

# Metrics Filters (Text Input boxes as requested)
col1, col2 = st.sidebar.columns(2)
with col1:
    min_dr = st.text_input("Min DR", value="0")
    min_da = st.text_input("Min DA", value="0")
with col2:
    min_traffic = st.text_input("Min Traffic", value="0")
    max_cost = st.text_input("Max Cost ($)", value="5000")

# --- FILTERING LOGIC ---
# Convert inputs to integers safely
try:
    f_dr = int(min_dr)
    f_da = int(min_da)
    f_traffic = int(min_traffic)
    f_cost = int(max_cost)
except ValueError:
    st.warning("Please enter valid numbers in the filter boxes.")
    st.stop()

mask = (
    (df['Main Niche'].isin(selected_niches)) &
    (df['DR'] >= f_dr) &
    (df['DA'] >= f_da) &
    (df['Ahrefs Traffic'] >= f_traffic) &
    (df['Cost (USD)'] <= f_cost)
)

filtered_df = df[mask]

# --- DISPLAY ---
st.title("🌐 Guest Post Inventory")
st.write(f"Showing **{len(filtered_df)}** matching websites.")

# SELECTING COLUMNS TO SHOW (Hide Vendor info and internal data)
display_cols = [
    'Site', 'DA', 'DR', 'Ahrefs Traffic', 
    'Cost (USD)', 'Cost CBD (USD)', 'Niche', 
    'Main Niche', 'Guidelines'
]

# Display the table
st.dataframe(
    filtered_df[display_cols], 
    use_container_width=True, 
    hide_index=True
)

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()
