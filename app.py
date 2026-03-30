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
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    
    # Force read data, treating the very first row as data so we can map it by positions
    df = pd.read_csv(url, header=0)
    
    # 🚨 OVERRIDE HEADERS: Force name mapped to the exact position of columns in your sheet
    if len(df.columns) >= 5:
        df.columns.values[0] = 'Site'
        df.columns.values[1] = 'DA'
        df.columns.values[2] = 'DR'
        df.columns.values[3] = 'Ahrefs Traffic'
        df.columns.values[4] = 'Cost (USD)'
        
    # Remove any empty rows where no website exists
    df = df.dropna(subset=['Site'])
    
    # Convert metric columns to numbers safely (eliminating text issues)
    for col in ['DA', 'DR', 'Ahrefs Traffic', 'Cost (USD)']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not connect to Google Sheets. Error: {e}")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Sites")

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
    st.warning("⚠️ Please enter valid numbers (no letters or symbols) in the filter boxes.")
    st.stop()

# Start with keeping everything based on numeric columns
mask = (
    (df['DR'] >= f_dr) &
    (df['DA'] >= f_da) &
    (df['Ahrefs Traffic'] >= f_traffic) &
    (df['Cost (USD)'] <= f_cost)
)

filtered_df = df[mask]

# --- DISPLAY ---
st.title("🌐 Guest Post Inventory")
st.write(f"Showing **{len(filtered_df)}** matching websites out of {len(df)} total.")

# Safe columns to show
display_cols = ['Site', 'DA', 'DR', 'Ahrefs Traffic', 'Cost (USD)']

# Display the table
st.dataframe(
    filtered_df[display_cols], 
    use_container_width=True, 
    hide_index=True
)

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()
