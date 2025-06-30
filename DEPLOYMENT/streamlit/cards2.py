import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import streamlit as st
from pymongo import MongoClient
import altair as alt
from datetime import datetime, timezone

# Load env and connect
#load_dotenv()
dbconn = st.secrets["MongoLink"]
client = MongoClient(dbconn)
db = client['virtualgenesis']

# UI elements
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    h1 {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

#PAGE HEADING
st.markdown(f"<h1 style='color: white;'>SUCCESSFULLY LAUNCHED GENESIS TOKENS</h1>", unsafe_allow_html=True)

#-----PAGE DESIGN-----
st.markdown("""
    <style>
    html, body { overflow-x: hidden !important;
        .stApp{
            width: 100vw;
            box-sizing: border-box;
            background-image: url('https://images.pexels.com/photos/5011647/pexels-photo-5011647.jpeg');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
    }}
    </style>
""", unsafe_allow_html=True)

# Fetch list of symbols
#tokens = [doc["symbol"] for doc in db["New Persona"].find({}, {'symbol':1, '_id':0})]
tokens = ["TEST"]
#CSS
st.markdown("""
<style>
.card {
    backdrop-filter: blur(12px);
    background: rgba(120, 120, 120, 0.3);
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    min-height: 200px;
}
.card:hover {
    transform: translateY(-4px);
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
# Display them in chunks of 4
num_cols = 5
for i in range(0, len(tokens), num_cols):
    chunk = tokens[i:i+num_cols]
    with st.container():
        cols = st.columns(num_cols, vertical_alignment="center")
        for j, token in enumerate(chunk):
            with cols[j]:
                # Fetch all names for this token
                names_html = "".join(
                    f"<p>{doc['name']}</p>"
                    for doc in db["New Persona"].find(
                        {"symbol": token}, {"name":1, "_id":0}
                    )
                )
                # Card content
                card_html = f"""
                <div class="card">
                    <h1>{token}</h1>
                    {names_html}
                    <a href="/tokendatatest?token={token}" target="_blank">See TXNs</a>
                </div>"""
                st.markdown(card_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
