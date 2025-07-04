import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from datetime import timedelta

# ───── Streamlit Setup ─────
st.set_page_config(layout="wide")

# ───── Global Styling ─────
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
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
    }
    section[data-testid="stSidebar"] .markdown-text-container,
    div[role="radiogroup"] label span,
    h1 {
        color: white !important;
    }
    html, body {
        overflow-x: hidden !important;
    }
    .stApp {
        width: 100vw;
        box-sizing: border-box;
        background: radial-gradient(circle, rgba(18, 73, 97, 1) 0%, rgba(5, 27, 64, 1) 100%);
    }
    </style>
""", unsafe_allow_html=True)

# ───── Sidebar ─────
with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("You can add filters or controls here.")
    st.markdown("---")
    st.markdown("Made for Genesis Analytics.")

# ───── Load DB Connection ─────
load_dotenv()
client = MongoClient(os.environ.get("MongoLink"))
db = client['virtualgenesis']

# ───── Token Parameter ─────
query_params = st.query_params
token = query_params.get('token', '').lower().strip()
if not token:
    st.error("No token specified. Please navigate back and choose a token.")
    st.stop()

st.markdown(f"<h1 style='color: white;'>TRANSACTION TABLE FOR {token.upper()}</h1>", unsafe_allow_html=True)

# ───── Collection Naming ─────
token_in_col = f"{token.upper()}_IN"
token_out_col = f"{token.upper()}_OUT"
virtual_in_col = "Virtual_IN"
virtual_out_col = "Virtual_OUT"
collection_name = f"{token}_swap"

# ───── Fetch Data ─────
data = list(db[collection_name].find({}, {
    "blockNumber": 1, "txHash": 1, "maker": 1, "swapType": 1, "label": 1, "timestampReadable": 1,
    token_in_col: 1, token_out_col: 1, virtual_in_col: 1, virtual_out_col: 1,
    "genesis_usdc_price": 1, "genesis_virtual_price": 1, "virtual_usdc_price": 1
}))
tabdf = pd.DataFrame(data)

# ───── Process Data ─────
def extract_amount(row):
    if row.get("swapType") == "buy":
        return pd.Series([row.get(token_out_col), row.get(virtual_in_col)])
    elif row.get("swapType") == "sell":
        return pd.Series([row.get(token_in_col), row.get(virtual_out_col)])
    return pd.Series([None, None])

tabdf[["TokenAmount", "Virtual"]] = tabdf.apply(extract_amount, axis=1)
tabdf["TokenAmount"] = pd.to_numeric(tabdf["TokenAmount"]).round(4)
tabdf["Virtual"] = pd.to_numeric(tabdf["Virtual"]).round(4)
tabdf.rename(columns={"TokenAmount": token.upper()}, inplace=True)

tabdf["txHash"] = tabdf["txHash"].apply(lambda tx: f"<a href='https://basescan.org/tx/{tx}' target='_blank'>Link to txn</a>")
tabdf["swapType"] = tabdf["swapType"].apply(lambda x: f"<span style='color: {'green' if x == 'buy' else 'red'}; font-weight:bold'>{x}</span>")

tabdf = tabdf[[
    "blockNumber", "txHash", "maker", "swapType", "label", "timestampReadable",
    token.upper(), "Virtual", "genesis_usdc_price", "genesis_virtual_price", "virtual_usdc_price"
]].rename(columns={
    "blockNumber": "BLOCK", "txHash": "TX HASH", "maker": "MAKER",
    "swapType": "TX TYPE", "label": "SWAP TYPE", "timestampReadable": "TIME",
    "Virtual": "VIRTUAL",
    "genesis_usdc_price": "GENESIS \nPRICE ($)",
    "genesis_virtual_price": "GENESIS PRICE \n($VIRTUAL)",
    "virtual_usdc_price": "VIRTUAL \nPRICE ($)"
})
tabdf["MAKER"] = tabdf["MAKER"].apply(lambda addr: f"<span title='{addr}'>{addr[:10]}...</span>" if isinstance(addr, str) else addr)
tabdf["TIME_PARSED"] = pd.to_datetime(tabdf["TIME"], errors='coerce')
tabdf["TX_TYPE_RAW"] = tabdf["TX TYPE"].str.extract(r">(\w+)<")
tabdf["TRANSACTION VALUE ($)"] = (tabdf[token.upper()] * tabdf["GENESIS \nPRICE ($)"]).round(4)
filtered_df = tabdf.copy()

# ───── Filters: Panel 1 ─────
with st.container():
    col1, col2, col3, col4, col5, col10 = st.columns(6)

    with col1:
        st.markdown("<div style='color: white; font-weight: 500;'>Transaction Type</div>", unsafe_allow_html=True)
        swap_filter = st.segmented_control("", options=["all", "buy", "sell"], default="all")

    with col2:
        st.markdown("<div style='color: white; font-weight: 500;'>Swap Type</div>", unsafe_allow_html=True)
        label_options = ["All"] + sorted(tabdf["SWAP TYPE"].dropna().unique())
        label_filter = st.selectbox("", label_options)

    with col3:
        st.markdown("<div style='color: white; font-weight: 500;'>Date Range</div>", unsafe_allow_html=True)
        date_range = st.date_input("", value=(tabdf["TIME_PARSED"].min(), tabdf["TIME_PARSED"].max()))

    with col4:
        st.markdown("<div style='color: white; font-weight: 500;'>Sort by</div>", unsafe_allow_html=True)
        sort_col = st.selectbox("", filtered_df.columns.tolist())

    with col5:
        st.markdown("<div style='color: white; font-weight: 500;'>Order</div>", unsafe_allow_html=True)
        sort_dir = st.radio("", options=["Ascending", "Descending"], horizontal=True)

    with col10:
        st.markdown("<div style='color: white; font-weight: 500;'>Search BLOCK or MAKER</div>", unsafe_allow_html=True)
        search_query = st.text_input("")
        if search_query:
            q = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["BLOCK"].astype(str).str.contains(q) |
                filtered_df["MAKER"].str.lower().str.contains(q)
            ]

# ───── Apply Filters ─────
if swap_filter != "all":
    filtered_df = filtered_df[filtered_df["TX_TYPE_RAW"].str.lower() == swap_filter.lower()]
if label_filter != "All":
    filtered_df = filtered_df[filtered_df["SWAP TYPE"] == label_filter]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1]) + timedelta(days=1)
    filtered_df = filtered_df[(filtered_df["TIME_PARSED"] >= start_date) & (filtered_df["TIME_PARSED"] <= end_date)]

# ───── Filters: Panel 2 (Numeric Range) ─────
with st.container():
    col6, col7 = st.columns([1, 4])
    with col6:
        st.markdown("<div style='color: white; font-weight: 500;'>Filter by</div>", unsafe_allow_html=True)
        numeric_columns = [token.upper(), "VIRTUAL", "GENESIS \nPRICE ($)", "USD VALUE (GENESIS)", "GENESIS PRICE \n($VIRTUAL)", "VIRTUAL \nPRICE ($)"]
        selected_col = st.selectbox("", numeric_columns)

    with col7:
        if selected_col in filtered_df.columns and not filtered_df[selected_col].dropna().empty:
            col_min, col_max = filtered_df[selected_col].min(), filtered_df[selected_col].max()
            if pd.notnull(col_min) and pd.notnull(col_max) and col_min != col_max:
                st.markdown(f"<div style='color: white; font-weight: 500;'>Range for {selected_col}</div>", unsafe_allow_html=True)
                value_range = st.slider(
                    "", float(col_min), float(col_max), (float(col_min), float(col_max)),
                    step=0.000001, format="%.6f"
                )
                filtered_df = filtered_df[
                    (filtered_df[selected_col] >= value_range[0]) &
                    (filtered_df[selected_col] <= value_range[1])
                ]

#--TABLE RENDERING
filtered_df = filtered_df.sort_values(by=sort_col, ascending=(sort_dir == "Ascending"))
filtered_df = filtered_df.drop(columns=["TX_TYPE_RAW", "TIME_PARSED"], errors="ignore")
#ordering columns
ordered_cols = [
    "BLOCK", "TX HASH", "MAKER", "TX TYPE", "SWAP TYPE", "TIME",
    token.upper(), "VIRTUAL", "GENESIS \nPRICE ($)", "USD VALUE (GENESIS)",
    "GENESIS PRICE \n($VIRTUAL)", "VIRTUAL \nPRICE ($)"
]
filtered_df = filtered_df[[col for col in ordered_cols if col in filtered_df.columns]]

html_table = filtered_df.to_html(escape=False, index=False)
#-- CSS FOR THE TABLE
scrollable_style = """
<style>
.scrollable {
    max-height:600px; overflow-y:auto; overflow-x:auto; width: 78vw;
    box-sizing: border-box; display:flex; justify-content: flex-start;
    font-family: 'Epilogue', sans-serif; font-size: 14px; color: #222;
}
.scrollable table {
    backdrop-filter: blur(10px); background: rgba(255, 255, 255, 0.8);
    width:100vw; border-collapse: collapse;
    border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin: 0 auto 0 0; table-layout: auto; text-align:center;
}
.scrollable th, .scrollable td {
    padding:12px 16px; border:1px solid #ccc;
    text-align: center; min-width: 120px; font-size:16px; font-weight:400;
}
.scrollable th {
    position: static; top:0; background:rgba(255,255,255,0.1); color:#fff;
    text-transform:uppercase; font-weight:600;
}
</style>
"""

with st.container():
    st.markdown(scrollable_style, unsafe_allow_html=True)
    st.markdown(f"<div class='scrollable'>{html_table}</div>", unsafe_allow_html=True)
