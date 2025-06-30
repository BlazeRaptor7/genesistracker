# tokendata.py
import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from pymongo import MongoClient
import streamlit.components.v1 as components
st.set_page_config(layout="wide")

# Global CSS for white headers and tighter spacing in radio buttons
st.markdown("""
    <style>
    /* Make radio button labels white */
    div[role="radiogroup"] label span {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)


# Load env and connect
load_dotenv()
dbconn = os.environ.get("MongoLink")
client = MongoClient(dbconn)
db = client['virtualgenesis']
query_params = st.query_params  # direct access
token = query_params.get('token', '').lower().strip()

if not token:
    st.error("No token specified. Please navigate back and choose a token.")
    st.stop()
st.markdown("""
    <style>
    h1 {
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

#PAGE HEADING
st.markdown(f"<h1 style='color: white;'>{'TRANSACTION TABLE FOR ' + token.upper()}</h1>", unsafe_allow_html=True)

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
# Compute dynamic columns
token_in_col = f"{token.upper()}_IN"
token_out_col = f"{token.upper()}_OUT"
virtual_in_col = "Virtual_IN"
virtual_out_col = "Virtual_OUT"
collection_name = f"{token}_swap"

# Fetch data dynamically
data = list(
    db[collection_name].find(
        {},
        {
            "blockNumber": 1,
            "txHash": 1,
            "maker": 1,
            "swapType": 1,
            "label":1,
            "timestampReadable": 1,
            token_in_col: 1,
            token_out_col: 1,
            virtual_in_col: 1,
            virtual_out_col: 1,
            "genesis_usdc_price": 1,
            "genesis_virtual_price": 1,
            "virtual_usdc_price": 1,
        }
    )
)

tabdf = pd.DataFrame(data)

# Extract amount columns
def extract_amount(row):
    if row.get("swapType") == "buy":
        return pd.Series([row.get(token_out_col), row.get(virtual_in_col)])
    elif row.get("swapType") == "sell":
        return pd.Series([row.get(token_in_col), row.get(virtual_out_col)])
    return pd.Series([None, None])

tabdf[["TokenAmount", "Virtual"]] = tabdf.apply(extract_amount, axis=1)

# Round numeric columns
tabdf["TokenAmount"] = pd.to_numeric(tabdf["TokenAmount"]).round(4)
tabdf["Virtual"] = pd.to_numeric(tabdf["Virtual"]).round(4)

# Rename TokenAmount column to token capitalized
tabdf.rename(columns={"TokenAmount": token.capitalize()}, inplace=True)

# Replace txHash with link
tabdf["txHash"] = tabdf["txHash"].apply(
    lambda tx: f"<a href='https://basescan.org/tx/{tx}' target='_blank'>Link to txn</a>"
)

# Color the swapType column
tabdf["swapType"] = tabdf["swapType"].apply(
    lambda x: f"<span style='color: {'green' if x == 'buy' else 'red'}; font-weight:bold'>{x}</span>"
)

tabdf = tabdf[["blockNumber", "txHash", "maker", "swapType","label", "timestampReadable", token.capitalize(), "Virtual", "genesis_usdc_price", "genesis_virtual_price", "virtual_usdc_price",]]
tabdf.rename(columns={ "blockNumber":"BLOCK", "txHash":"TX HASH", "maker":"MAKER", "swapType":"TX TYPE", "label":"SWAP TYPE", "timestampReadable":"TIME", token.capitalize(): token.upper(), "Virtual":"VIRTUAL", "genesis_usdc_price":"GENESIS \nPRICE ($)", "genesis_virtual_price":"GENESIS PRICE \n($VIRTUAL)", "virtual_usdc_price":"VIRTUAL \nPRICE ($)",}, inplace=True)
tabdf["MAKER"] = tabdf["MAKER"].apply( lambda addr: f"<span title='{addr}'>{addr[:10]}...</span>" if isinstance(addr, str) else addr)
tabdf["TIME_PARSED"] = pd.to_datetime(tabdf["TIME"], errors='coerce')
tabdf["TX_TYPE_RAW"] = tabdf["TX TYPE"].str.extract(r">(\w+)<")
#CREATING A COPY DF
filtered_df = tabdf.copy()
# ───── CON1: TX TYPE + SWAP CATEGORY + DATE RANGE ─────
with st.container():
    col1, col2, col3, col4, col5, col10 = st.columns([1, 1, 1, 1, 1, 1])

    with col1:
        st.markdown("<div style='color: white; font-weight: 500; margin-bottom: 0px;'>Transaction Type</div>", unsafe_allow_html=True)
        swap_filter = st.segmented_control(
            label="",
            options=["all", "buy", "sell"],
            default="all",
            format_func=lambda x: x.capitalize(),
            key="swap_filter"
        )

    with col2:
        st.markdown("<div style='color: white; font-weight: 500; margin-bottom: 0px;'>Swap Type</div>", unsafe_allow_html=True)
        label_options = ["All"] + sorted(tabdf["SWAP TYPE"].dropna().unique().tolist())
        label_filter = st.selectbox("", label_options)

    with col3:
        st.markdown("<div style='color: white; font-weight: 500; margin-bottom: 0px;'>Date Range</div>", unsafe_allow_html=True)
        min_date = tabdf["TIME_PARSED"].min()
        max_date = tabdf["TIME_PARSED"].max()
        date_range = st.date_input(
            label="",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    with col4:
        st.markdown("<div style='color: white; font-weight: 500; margin-bottom: 0px;'>Sort by</div>", unsafe_allow_html=True)
        sort_col = st.selectbox("", filtered_df.columns.tolist())

    with col5:
        st.markdown("<div style='color: white; font-weight: 500; margin-bottom: 0px;'>Order</div>", unsafe_allow_html=True)
        sort_dir = st.radio(
            label="",
            options=["Ascending", "Descending"],
            horizontal=True,
            key="sort_order",
            label_visibility="collapsed"
        )


    with col10:
        st.markdown("<div style='color: white; font-weight: 500; margin-bottom: 0px;'>Search BLOCK or MAKER</div>", unsafe_allow_html=True)
        search_query = st.text_input("")
        if search_query:
            search_query = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["BLOCK"].astype(str).str.contains(search_query) |
                filtered_df["MAKER"].str.lower().str.contains(search_query)
            ]

# Filter logic after CON1
if swap_filter != "all":
    filtered_df = filtered_df[filtered_df["TX_TYPE_RAW"].str.lower() == swap_filter.lower()]
if label_filter != "All":
    filtered_df = filtered_df[filtered_df["SWAP TYPE"] == label_filter]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["TIME_PARSED"] >= pd.to_datetime(start_date)) &
        (filtered_df["TIME_PARSED"] <= pd.to_datetime(end_date))
    ]

# ───── CON2: NUMERIC FILTER + SLIDER ─────
with st.container():
    col6, col7 = st.columns([1, 4])

    with col6:
        st.markdown("<div style='color: white; font-weight: 500; margin-bottom: 0px;'>Filter by</div>", unsafe_allow_html=True)
        numeric_columns = [
            token.upper(),
            "VIRTUAL",
            "GENESIS \nPRICE ($)",
            "GENESIS PRICE \n($VIRTUAL)",
            "VIRTUAL \nPRICE ($)"
        ]
        selected_col = st.selectbox("", numeric_columns)

    with col7:
        if selected_col not in filtered_df.columns or filtered_df[selected_col].dropna().empty:
            st.warning(f"No valid range available for {selected_col}")
        else:
            col_min = filtered_df[selected_col].min()
            col_max = filtered_df[selected_col].max()
            if pd.notnull(col_min) and pd.notnull(col_max) and col_min != col_max:
                st.markdown(f"<div style='color: white; font-weight: 500; margin-bottom: 0px;'>Range for {selected_col}</div>", unsafe_allow_html=True)
                value_range = st.slider(
                    label="",
                    min_value=float(col_min),
                    max_value=float(col_max),
                    value=(float(col_min), float(col_max)),
                    step=0.000001,
                    format="%.6f"
                )
                filtered_df = filtered_df[
                    (filtered_df[selected_col] >= value_range[0]) &
                    (filtered_df[selected_col] <= value_range[1])
                ]
            else:
                st.warning(f"No valid range available for {selected_col}")

# ───── FINAL: SORTING + CLEANUP ─────
filtered_df = filtered_df.sort_values(
    by=sort_col,
    ascending=(sort_dir == "Ascending")
)

filtered_df = filtered_df.drop(columns=["TX_TYPE_RAW", "TIME_PARSED"], errors="ignore")
html_table = filtered_df.to_html(escape=False, index=False)

# CSS
scrollable_style = """
<style>
.scrollable {max-height:600px; overflow-y:auto; overflow-x:auto;  width: 78vw;  margin-right:2w;  box-sizing: border-box;  display:flex;  justify-content : flex-start; font-family: 'Epilogue', sans-serif; font-size: 14px; color: #222;}
.scrollable table {  backdrop-filter: blur(10px); background: rgba(255, 255, 255, 0.8);     width:100%;  border-collapse: collapse; border-spacing:0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-left:0;  margin-right:0;  margin: 0 auto 0 0;  table-layout: auto;  text-align:center;}
.scrollable th, .scrollable td { padding:12px 16px;  border-bottom: 1px solid #ddd; text-align: center; min-width: 120px; border:1px solid #ccc;   min-width:120px;  font-size:16px; font-weight:400;}
.scrollable th { position: sticky; top:0; background:#1c3f4f; color:#fff; text-transform:uppercase; text-align:center; font-weight:600;}
</style>
"""
# TOGGLE FOR HTML TABLE

with st.container():
    st.markdown(scrollable_style, unsafe_allow_html=True)
    st.markdown(f"<div class='scrollable'>{html_table}</div>", unsafe_allow_html=True)