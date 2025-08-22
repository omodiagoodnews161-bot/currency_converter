import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# --- Page setup ---
st.set_page_config(page_title="💱 Currency Converter", layout="wide")
st.title("💱 Currency Converter")
st.write("Convert currencies in real-time, view trends, and see multiple conversions at once.")

# --- Currency list with emoji flags ---
currencies = {
    "USD 🇺🇸": "USD",
    "EUR 🇪🇺": "EUR",
    "GBP 🇬🇧": "GBP",
    "NGN 🇳🇬": "NGN",
    "JPY 🇯🇵": "JPY",
    "CAD 🇨🇦": "CAD",
    "AUD 🇦🇺": "AUD"
}

# --- Sidebar for input ---
st.sidebar.header("Conversion Settings")
from_currency_name = st.sidebar.selectbox("From Currency", list(currencies.keys()))
to_currency_names = st.sidebar.multiselect(
    "To Currency", 
    list(currencies.keys()), 
    default=["USD 🇺🇸", "EUR 🇪🇺"]
)
amount = st.sidebar.number_input("Amount", min_value=0.0, value=1.0, step=1.0)

from_currency = currencies[from_currency_name]
to_currencies = [currencies[name] for name in to_currency_names]

# Swap button
if st.sidebar.button("🔄 Swap"):
    if to_currency_names:
        temp = from_currency_name
        from_currency_name = to_currency_names[0]
        to_currency_names[0] = temp
        from_currency = currencies[from_currency_name]
        to_currencies = [currencies[name] for name in to_currency_names]

# --- Fetch live rates from ER API ---
try:
    url = f"https://open.er-api.com/v6/latest/{from_currency}"
    response = requests.get(url).json()
    
    if response["result"] != "success":
        st.error(f"❌ Could not fetch rates. API response: {response}")
        st.stop()
    
    all_rates = response["rates"]
    rates = {cur: all_rates[cur] for cur in to_currencies if cur in all_rates}
    
    # Handle missing currencies
    missing = [cur for cur in to_currencies if cur not in all_rates]
    if missing:
        st.warning(f"⚠️ Some currencies not found: {', '.join(missing)}")
except Exception as e:
    st.error(f"❌ Failed to fetch rates: {e}")
    st.stop()

# --- Display conversion cards ---
st.subheader("💳 Conversion Results")
if not to_currencies:
    st.warning("Select at least one target currency to convert to.")
else:
    cols = st.columns(len(to_currencies))
    for i, to_cur in enumerate(to_currencies):
        if to_cur in rates:
            converted = amount * rates[to_cur]
            cols[i].metric(
                label=f"{amount} {from_currency} → {to_cur}",
                value=f"{converted:.2f}",
                delta=f"1 {from_currency} = {rates[to_cur]:.4f} {to_cur}"
            )

# --- Historical trend for first selected currency ---
if to_currencies and to_currencies[0] in rates:
    st.subheader(f"📈 Last 30 Days: {from_currency} → {to_currencies[0]}")
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    
    # ER API provides historical rates by date
    historical_rates = []
    dates_list = []
    for i in range(31):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        hist_url = f"https://open.er-api.com/v6/{date}/{from_currency}"
        try:
            hist_resp = requests.get(hist_url).json()
            if hist_resp["result"] == "success":
                if to_currencies[0] in hist_resp["rates"]:
                    historical_rates.append(hist_resp["rates"][to_currencies[0]])
                    dates_list.append(date)
        except:
            continue
    
    if historical_rates:
        df = pd.DataFrame({"Date": pd.to_datetime(dates_list), "Rate": historical_rates})
        chart = alt.Chart(df).mark_line(point=True, color="#1f77b4").encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Rate:Q", title=f"Rate ({from_currency} → {to_currencies[0]})"),
            tooltip=["Date:T", "Rate:Q"]
        ).interactive().properties(width=800, height=400)
        st.altair_chart(chart, use_container_width=True)

# --- Historical rates table for multiple currencies ---
if len(to_currencies) > 1:
    st.subheader("📊 Last 30 Days: All Selected Currencies")
    table_data = {}
    for cur in to_currencies:
        cur_rates = []
        cur_dates = []
        for i in range(31):
            date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            hist_url = f"https://open.er-api.com/v6/{date}/{from_currency}"
            try:
                hist_resp = requests.get(hist_url).json()
                if hist_resp["result"] == "success" and cur in hist_resp["rates"]:
                    cur_rates.append(hist_resp["rates"][cur])
                    cur_dates.append(date)
            except:
                continue
        table_data[cur] = pd.Series(cur_rates, index=pd.to_datetime(cur_dates))
    if table_data:
        df_multi = pd.DataFrame(table_data)
        st.dataframe(df_multi.style.format("{:.4f}"))
