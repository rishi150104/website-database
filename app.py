import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
SHEET_ID = "1mZRmzqJj2JQ7ustMp61GQkkabQPoyX2gE9pHZYNo1Ng"
SHEET_NAME = "Sheet1" 
PASSWORD = "123" 

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
@st.cache_data(ttl=600) 
def load_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx:out:csv&sheet={SHEET_NAME}"
    df = pd.read_csv(url)
    
    # Clean up column names (removes hidden spaces)
    df.columns = df.columns.str.strip()
    
    # SAFETY: Force standard names on the first 5 columns just in case Google gets weird
    if len(df.columns) >= 5:
        df.columns.values[0] = 'Site'
        df.columns.values[1] = 'DA'
        df.columns.values[2] = 'DR'
        df.columns.values[3] = 'Ahrefs Traffic'
        df.columns.values[4] = 'Cost (USD)'
        
    # Drop rows with no URL
    df = df.dropna(subset=['Site'])
    
    # Convert metrics to numbers
    for col in ['DA', 'DR', 'Ahrefs Traffic', 'Cost (USD)']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # FEATURE 2: Turn text into a clickable link!
    # If the site doesn't start with http, we add it so it's a valid link
    def make_clickable(site):
        site_str = str(site).strip()
        if not site_str.startswith('http'):
            link = f"https://{site_str}"
        else:
            link = site_str
        return link

    df['Site Link'] = df['Site'].apply(make_clickable)
            
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not connect to Google Sheets. Error: {e}")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Sites")

# FEATURE 1: Niche Filter
# We look for a column named 'Niche'. If it doesn't exist, we don't show the filter.
if 'Niche' in df.columns:
    all_niches = sorted(df['Niche'].dropna().unique().tolist())
    selected_niches = st.sidebar.multiselect("Select Niches", all_niches, default=all_niches)
else:
    selected_niches = []

# Metrics Filters
col1, col2 = st.sidebar.columns(2)
with col1:
    min_dr = st.text_input("Min DR", value="0")
    min_da = st.text_input("Min DA", value="0")
with col2:
    min_traffic = st.text_input("Min Traffic", value="0")
    max_cost = st.text_input("Max Cost ($)", value="5000")

# --- FILTERING LOGIC ---
try:
    f_dr = int(min_dr)
    f_da = int(min_da)
    f_traffic = int(min_traffic)
    f_cost = int(max_cost)
except ValueError:
    st.warning("⚠️ Please enter valid numbers in the filter boxes.")
    st.stop()

mask = (
    (df['DR'] >= f_dr) &
    (df['DA'] >= f_da) &
    (df['Ahrefs Traffic'] >= f_traffic) &
    (df['Cost (USD)'] <= f_cost)
)

# Apply niche filter if column exists and user made selections
if 'Niche' in df.columns and selected_niches:
    mask = mask & (df['Niche'].isin(selected_niches))

filtered_df = df[mask]

# --- DISPLAY ---
st.title("🌐 Guest Post Inventory")
st.write(f"Showing **{len(filtered_df)}** matching websites out of {len(df)} total.")

# Safe columns to show - added 'Niche' to the list
display_cols = ['Site Link', 'DA', 'DR', 'Ahrefs Traffic', 'Cost (USD)']
if 'Niche' in df.columns:
    display_cols.append('Niche')

# Display the table with interactive links
st.dataframe(
    filtered_df[display_cols], 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Site Link": st.column_config.LinkColumn(
            "Site", 
            help="Click to open the domain",
            display_text="Open Website" # This makes it clean so it doesn't show the massive URL
        )
    }
)

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()
