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
st.write("SUCCESSFUL")
