import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
# Replace this with the ID from your Google Sheet URL
SHEET_ID = "1mZRmzqJj2JQ7ustMp61GQkkabQPoyX2gE9pHZYNo1Ng/edit?gid=0#gid=0"
SHEET_NAME = "Sheet1" # Set to the exact name of your main tab
PASSWORD = "123" # Set your desired password here

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
    
    # 1. Clean up column names (removes hidden spaces like 'Niche ')
    df.columns = df.columns.str.strip()
    
    # 2. Drop empty rows and columns that Google sometimes adds at the end
    df = df.dropna(subset=['Site']) # Ensures we don't load rows with no website
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # 3. Fill empty niche rows with "General" so they don't break the filters
    if 'Niche' in df.columns:
        df['Niche'] = df['Niche'].fillna('General')
    
    # 4. Ensure metrics are numbers and not read as text
    numeric_cols = ['DR', 'DA', 'Ahrefs Traffic', 'Cost (USD)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not connect to Google Sheets. Error: {e}")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Sites")

# Check if Niche column exists, if not use a generic backup
if 'Niche' in df.columns:
    all_niches = sorted(df['Niche'].dropna().unique().tolist())
    selected_niches = st.sidebar.multiselect("Select Niches", all_niches, default=all_niches)
else:
    selected_niches = []

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
    st.warning("⚠️ Please enter valid numbers (no letters or symbols) in the filter boxes.")
    st.stop()

# Start with keeping everything
mask = (
    (df['DR'] >= f_dr) &
    (df['DA'] >= f_da) &
    (df['Ahrefs Traffic'] >= f_traffic) &
    (df['Cost (USD)'] <= f_cost)
)

# Apply niche filter only if user made selections
if 'Niche' in df.columns and selected_niches:
    mask = mask & (df['Niche'].isin(selected_niches))

filtered_df = df[mask]

# --- DISPLAY ---
st.title("🌐 Guest Post Inventory")
st.write(f"Showing **{len(filtered_df)}** matching websites out of {len(df)} total.")

# SELECTING COLUMNS TO SHOW (Protects your vendor names and internal notes)
possible_display_cols = [
    'Site', 'DA', 'DR', 'Ahrefs Traffic', 
    'Cost (USD)', 'Cost CBD (USD)', 'Niche', 'Guidelines'
]
# Only show the columns that actually exist in your sheet
display_cols = [col for col in possible_display_cols if col in df.columns]

# Display the table
st.dataframe(
    filtered_df[display_cols], 
    use_container_width=True, 
    hide_index=True
)

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()
