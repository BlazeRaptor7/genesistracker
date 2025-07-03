#--IMPORTING AND GENERAL SETUP
import os
from dotenv import load_dotenv
import streamlit as st
from pymongo import MongoClient

#--STREAMLIT CONFIGURATION
st.set_page_config(layout="wide")

#--ENVIRONMENT LOADING AND DB CONNECTION
load_dotenv()
dbconn = os.getenv("MongoLink")
client = MongoClient(dbconn)
db = client['virtualgenesis']

# UI elements
# --GLOBAL CSS
st.markdown("""
<style>
header[data-testid="stHeader"] {
    background: transparent;
    visibility: visible;
}
[data-testid="stSidebarNav"] {
    display: none;
}
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.35);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
}
section[data-testid="stSidebar"] .markdown-text-container {
    color: white !important;
}
h1 {
    color: white !important;
}
html, body {
    overflow-x: hidden !important;
}
.stApp {
    width: 100vw;
    box-sizing: border-box;
    background: #013155;
    background-size: cover;
    background-attachment: fixed;
    background-position: center;
}
.card {
    backdrop-filter: blur(12px);
    background: rgba(255, 255, 255, 0.25);
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    min-height: 200px;
}
.card:hover {
    transform: translateY(-7px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    color:white;
}
.card h1 {
    margin-top: 0;
    font-size: 2rem;
    color: white;
    font-weight: bold;
    margin-bottom: 8px;
}
.card p {
    color: white;
    font-weight: semibold;
    margin: 2px 0;
}
.card a {
    display: inline-block;
    padding: 6px 12px;
    background: rgba(255, 255, 255, 0.2);
    color: white;
    font-weight: semibold;
    text-decoration: none;
    border-radius: 6px;
    margin-top: 8px;
    font-size: 1rem;
    font-weight: 500;
    backdrop-filter: blur(5px);
    transition: background 0.2s ease;
}
.card a:hover {
    background: rgba(255, 255, 255, 0.25);
    color: #173d5f;
}
</style>
""", unsafe_allow_html=True)

#--SIDEBAR
def render_sidebar():
    """Render the custom sidebar with navigation and branding."""
    with st.sidebar:
        st.markdown("## Navigation")
        #HERE, WE CHECK WHICH PAGE WE ARE ON AND LATER USE IT TO HIGHLIGHT THE CURRENT PAGE
        current_script = os.path.basename(__file__).lower()
        routes = [
            ("Token Transactions", "/cards2", "cards2.py"),
            ("Token Analytics", "/tokenanalytics", "tokenanalytics.py")
        ]
        for label, path, filename in routes:
            is_active = filename.lower() == current_script
            bg = "#124961" if is_active else "transparent"
            st.markdown(
                f"""
                <a href="{path}" style="
                    display: block;
                    padding: 0.5rem 1rem;
                    margin-bottom: 0.5rem;
                    font-weight: bold;
                    border-radius: 6px;
                    color: white;
                    background-color: {bg};
                    text-decoration: none;
                ">{label}</a>
                """,
                unsafe_allow_html=True
            )
        st.markdown("---")
        st.markdown("Made for Genesis Analytics.")


#--THE PAGE HEADER
st.markdown("<h1 style='color: white;'>SUCCESSFULLY LAUNCHED GENESIS TOKENS</h1>", unsafe_allow_html=True)

#--MODULARIZATION
#--DATA FETCHING
def get_token_list(db):
    return [doc["symbol"] for doc in db["New Persona"].find({}, {'symbol': 1, '_id': 0}).sort("symbol", 1)]

#--TOKEN NAME FETCHER
def get_names_for_token(db, token):
    return "".join(
        f"<p>{doc['name']}</p>"
        for doc in db["New Persona"].find({"symbol": token}, {"name": 1, "_id": 0})
    )

#--RENDERING TOKEN CARDS
def render_token_cards(db, tokens, num_cols=5):
    for i in range(0, len(tokens), num_cols):
        chunk = tokens[i:i + num_cols]
        with st.container():
            cols = st.columns(num_cols, vertical_alignment="center")
            for j, token in enumerate(chunk):
                with cols[j]:
                    names_html = get_names_for_token(db, token)
                    card_html = f"""
                    <div class="card">
                        <h1>{token}</h1>
                        {names_html}
                        <a href="/tokendatatestcopy?token={token}" target="_blank">See TXNs</a>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

#CALLING HELPER FUNCTIONS
render_sidebar()
tokens = get_token_list(db)
render_token_cards(db, tokens)