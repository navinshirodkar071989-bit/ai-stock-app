import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="AI ELITE SCANNER", layout="wide")

st.title("🚀 AI ELITE SCANNER (High Accuracy Mode)")

# -----------------------------
# AUTO REFRESH
# -----------------------------
st_autorefresh(interval=300000)

# -----------------------------
# ALERT FUNCTION
# -----------------------------
def alert_popup(stock, price, score):
    st.toast(f"🚀 {stock} | Price: {price} | Confidence: {score}", icon="🔥")

# -----------------------------
# TIME
# -----------------------------
ist = pytz.timezone('Asia/Kolkata')
now = datetime.datetime.now(ist)
st.write("⏰ Time:", now.strftime("%Y-%m-%d %H:%M"))

# -----------------------------
# STOCK LIST
# -----------------------------
nifty100 = [
"RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
"HINDUNILVR.NS","ITC.NS","SBIN.NS","BHARTIARTL.NS","KOTAKBANK.NS",
"LT.NS","AXISBANK.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
"TITAN.NS","ULTRACEMCO.NS","NESTLEIND.NS","BAJFINANCE.NS","BAJAJFINSV.NS",
"WIPRO.NS","HCLTECH.NS","POWERGRID.NS","NTPC.NS","ONGC.NS",
"TATASTEEL.NS","JSWSTEEL.NS","COALINDIA.NS","INDUSINDBK.NS",
"ADANIPORTS.NS","GRASIM.NS","CIPLA.NS","DRREDDY.NS","EICHERMOT.NS",
"HEROMOTOCO.NS","APOLLOHOSP.NS","BRITANNIA.NS","DIVISLAB.NS",
"SBILIFE.NS","HDFCLIFE.NS","ICICIPRULI.NS","TATAMOTORS.NS",
"UPL.NS","BPCL.NS","SHREECEM.NS","TECHM.NS","HINDALCO.NS","M&M.NS"
]

extra = [
"HAL.NS","BEL.NS","BDL.NS","MAZDOCK.NS","COCHINSHIP.NS",
"ADANIGREEN.NS","TATAPOWER.NS","NHPC.NS","SJVN.NS","SUZLON.NS",
"IRCTC.NS","RVNL.NS","IREDA.NS","NBCC.NS"
]

stocks = list(set(nifty100 + extra))
st.write(f"📊 Tracking {len(stocks)} stocks")

# -----------------------------
# FETCH DATA
# -----------------------------
@st.cache_data(ttl=180)
def fetch_data(stocks):
    return yf.download(
        stocks,
        period="2mo",
        interval="1d",
        group_by='ticker',
        threads=True,
        progress=False
    )

data = fetch_data(stocks)

# -----------------------------
# MARKET FILTER (NIFTY)
# -----------------------------
nifty = yf.download("^NSEI", period="5d", interval="1d", progress=False)
market_up = nifty['Close'].iloc[-1] > nifty['Close'].iloc[-2]

if market_up:
    st.success("📈 Market Trend: Bullish")
else:
    st.error("📉 Market Trend: Weak")

# -----------------------------
# RSI FUNCTION
# -----------------------------
def rsi(df, window=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# -----------------------------
# SESSION STATE (NO DUPLICATE ALERTS)
# -----------------------------
if "alerted" not in st.session_state:
    st.session_state.alerted = set()

# -----------------------------
# ANALYSIS
# -----------------------------
results = []

for stock in stocks:
    try:
        df = data[stock].dropna()
        if len(df) < 50:
            continue

        df['RSI'] = rsi(df)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100

        # -----------------------------
        # IMPROVED LOGIC
        # -----------------------------
        high_20 = df['High'].rolling(20).max().iloc[-2]
        breakout = latest['Close'] > high_20 * 1.01

        volume_avg = df['Volume'].rolling(20).mean().iloc[-2]
        volume_spike = latest['Volume'] > 2 * volume_avg

        sma_50 = df['Close'].rolling(50).mean().iloc[-1]
        trend_up = latest['Close'] > sma_50

        rsi_val = latest['RSI']
        good_rsi = 55 < rsi_val < 70

        strong_move = change > 2.5

        # -----------------------------
        # CONFIDENCE SCORE
        # -----------------------------
        score = 0
        if breakout: score += 30
        if volume_spike: score += 25
        if trend_up: score += 20
        if strong_move: score += 15
        if good_rsi: score += 10

        # -----------------------------
        # SIGNAL
        # -----------------------------
        signal = "HOLD"
        entry = 0
        sl = 0
        tgt = 0

        if score >= 75 and market_up:
            signal = "🟢 STRONG BUY"
            entry = latest['Close']
            sl = entry * 0.97
            tgt = entry * 1.06

            if stock not in st.session_state.alerted:
                alert_popup(stock, round(entry, 2), score)
                st.session_state.alerted.add(stock)

        elif score >= 55:
            signal = "🟡 WATCH"

        elif rsi_val > 75:
            signal = "🔴 SELL"

        results.append({
            "Stock": stock,
            "Price": round(latest['Close'], 2),
            "Change %": round(change, 2),
            "RSI": round(rsi_val, 2),
            "Confidence": score,
            "Signal": signal,
            "Entry": round(entry, 2),
            "Stop Loss": round(sl, 2),
            "Target": round(tgt, 2)
        })

    except:
        continue

df_all = pd.DataFrame(results)

# -----------------------------
# DISPLAY
# -----------------------------
if df_all.empty:
    st.error("No data")
else:
    st.subheader("📊 Market Scan")
    st.dataframe(df_all.sort_values(by="Confidence", ascending=False))

    st.subheader("🔥 High Probability Trades")
    high = df_all[df_all["Signal"] == "🟢 STRONG BUY"]

    if not high.empty:
        st.dataframe(high.sort_values(by="Confidence", ascending=False))
    else:
        st.info("No strong trades now")

st.caption("⚠️ High accuracy system. Fewer but better trades.")
