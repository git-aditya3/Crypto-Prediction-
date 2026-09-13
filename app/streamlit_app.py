"""
Streamlit Dashboard for Crypto Prediction
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from crypto_prediction.config import get_config
from crypto_prediction.data.fetcher import CryptoDataFetcher
from crypto_prediction.features.technical import FeatureEngineer
from crypto_prediction.prediction.predictor import CryptoPredictor
from crypto_prediction.utils.viz import plot_price_history, plot_prediction

config = get_config()

st.set_page_config(page_title="Crypto Prediction", layout="wide", page_icon="₿")

st.title("₿ Crypto Prediction Dashboard")
st.markdown("End-to-end cryptocurrency forecasting with **LSTM + XGBoost + ARIMA Ensemble**")

# Sidebar
with st.sidebar:
    st.header("Settings")
    symbol = st.selectbox("Select Symbol", config.data.supported_symbols, index=0)
    period = st.selectbox("Data Period", ["6mo", "1y", "2y", "5y"], index=1)
    interval = st.selectbox("Interval", ["1d", "1h"], index=0)
    steps = st.slider("Forecast Steps (days)", 1, 30, 7)
    st.divider()
    st.markdown("**Model Weights**")
    w_lstm = st.slider("LSTM", 0.0, 1.0, 0.5)
    w_xgb = st.slider("XGBoost", 0.0, 1.0, 0.3)
    w_arima = st.slider("ARIMA", 0.0, 1.0, 0.2)
    st.divider()
    if st.button("Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()

@st.cache_data(ttl=600)
def load_data(symbol, period, interval):
    fetcher = CryptoDataFetcher(symbol=symbol)
    fetcher.period = period
    fetcher.interval = interval
    df = fetcher.load_or_fetch(symbol=symbol, force_refresh=False)
    engineer = FeatureEngineer()
    feat_df = engineer.engineer(df)
    return df, feat_df

@st.cache_data(ttl=300)
def get_forecast(symbol, steps, period):
    try:
        predictor = CryptoPredictor(symbol=symbol)
        fc = predictor.forecast(steps=steps, period=period)
        signal = predictor.get_trading_signal(fc)
        return fc, signal, None
    except Exception as e:
        return None, None, str(e)

# Load data
with st.spinner(f"Loading {symbol} data..."):
    try:
        raw_df, feat_df = load_data(symbol, period, interval)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

# Metrics row
col1, col2, col3, col4 = st.columns(4)
current_price = raw_df['Close'].iloc[-1]
prev_price = raw_df['Close'].iloc[-2]
change = current_price - prev_price
change_pct = change / prev_price * 100

col1.metric(f"{symbol} Price", f"${current_price:,.2f}", f"{change_pct:+.2f}%")
col2.metric("Volume", f"{raw_df['Volume'].iloc[-1]:,.0f}")
col3.metric("RSI (14)", f"{feat_df['RSI'].iloc[-1]:.1f}" if 'RSI' in feat_df else "N/A")
col4.metric("Volatility (20d)", f"{feat_df['Volatility'].iloc[-1]*100:.2f}%" if 'Volatility' in feat_df else "N/A")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Price Chart", "🔮 Forecast", "📊 Features", "📋 Data"])

with tab1:
    st.subheader(f"{symbol} Price History with Indicators")
    fig = plot_price_history(feat_df.tail(200), symbol=symbol)
    st.plotly_chart(fig, use_container_width=True)

    # Additional indicators
    col_a, col_b = st.columns(2)
    with col_a:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=feat_df.index, y=feat_df['RSI'], name='RSI'))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(title="RSI", template="plotly_dark", height=300)
        st.plotly_chart(fig_rsi, use_container_width=True)
    with col_b:
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=feat_df.index, y=feat_df['MACD'], name='MACD'))
        fig_macd.add_trace(go.Scatter(x=feat_df.index, y=feat_df['MACD_Signal'], name='Signal'))
        fig_macd.add_trace(go.Bar(x=feat_df.index, y=feat_df['MACD_Hist'], name='Hist'))
        fig_macd.update_layout(title="MACD", template="plotly_dark", height=300)
        st.plotly_chart(fig_macd, use_container_width=True)

with tab2:
    st.subheader(f"Forecast next {steps} days")
    fc, signal, err = get_forecast(symbol, steps, period)

    if err:
        st.warning(f"Models not trained yet or error: {err}")
        st.info("Run `python scripts/train.py --symbol {} --period 2y` to train models".format(symbol))
    else:
        # Signal card
        if signal:
            color_map = {"STRONG_BUY": "green", "BUY": "lightgreen", "HOLD": "gray", "SELL": "orange", "STRONG_SELL": "red"}
            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background-color:{color_map.get(signal['signal'],'gray')}; color:white">
                <h3 style="margin:0">Signal: {signal['signal']} (Confidence: {signal['confidence']}%)</h3>
                <p style="margin:5px 0 0 0">Current: ${signal['current_price']:.2f} → Predicted: ${signal['predicted_price']:.2f} ({signal['change_pct']:+.2f}%)<br>{signal['reason']}</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # Forecast chart
        if fc and 'dates' in fc:
            fig_fc = go.Figure()
            # Historical last 60 days
            hist = raw_df.tail(60)
            fig_fc.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Historical', line=dict(color='white')))

            future_dates = pd.to_datetime(fc['dates'])
            for model_name in ['lstm', 'xgboost', 'arima', 'ensemble']:
                if model_name in fc and fc[model_name]:
                    fig_fc.add_trace(go.Scatter(
                        x=future_dates, y=fc[model_name],
                        name=f"Forecast {model_name.upper()}",
                        line=dict(dash='dash' if model_name!='ensemble' else 'solid', width=3 if model_name=='ensemble' else 2)
                    ))

            fig_fc.update_layout(title=f"{symbol} Forecast", template="plotly_dark", height=500,
                                 xaxis_title="Date", yaxis_title="Price USD")
            st.plotly_chart(fig_fc, use_container_width=True)

            # Table
            df_fc = pd.DataFrame({
                "Date": fc['dates'],
                **{k.upper(): v for k, v in fc.items() if k in ['lstm','xgboost','arima','ensemble']}
            })
            st.dataframe(df_fc, use_container_width=True)

with tab3:
    st.subheader("Feature Overview")
    st.write(f"Total features engineered: {len(feat_df.columns)}")
    # Show feature importance if exists
    imp_path = config.project_root / "models" / f"{symbol.replace('-','_')}_feature_importance.csv"
    if imp_path.exists():
        imp_df = pd.read_csv(imp_path)
        st.write("Feature Importance (XGBoost)")
        fig_imp = go.Figure(go.Bar(x=imp_df.head(15)['importance'], y=imp_df.head(15)['feature'], orientation='h'))
        fig_imp.update_layout(template="plotly_dark", height=500, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_imp, use_container_width=True)
    else:
        st.info("No feature importance found. Train XGBoost to generate.")

    st.dataframe(feat_df.tail(20), use_container_width=True)

with tab4:
    st.subheader("Raw Data")
    st.dataframe(raw_df.tail(100), use_container_width=True)
    csv = raw_df.to_csv().encode('utf-8')
    st.download_button("Download CSV", csv, f"{symbol}_data.csv", "text/csv")

st.sidebar.markdown("---")
st.sidebar.markdown("Built with ❤️ | Crypto Prediction Core v0.1.0")
