"""
Streamlit Dashboard for Crypto Prediction v2
- Includes Sentiment, Transformer, Realtime, Backtesting
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from crypto_prediction.config import get_config
from crypto_prediction.data.fetcher import CryptoDataFetcher
from crypto_prediction.features.technical import FeatureEngineer
from crypto_prediction.features.sentiment import SentimentFeatureEngineer
from crypto_prediction.prediction.predictor import CryptoPredictor
from crypto_prediction.utils.viz import plot_price_history
from crypto_prediction.backtesting.engine import BacktestEngine
from crypto_prediction.backtesting.strategies import MovingAverageStrategy, RSIStrategy, EnsembleSignalStrategy
from crypto_prediction.data.realtime import BinanceRealtimeFetcher

config = get_config()

st.set_page_config(page_title="Crypto Prediction v2", layout="wide", page_icon="₿")

st.title("₿ Crypto Prediction v2")
st.markdown("**LSTM + Transformer (TFT) + XGBoost + ARIMA Ensemble + Sentiment + Realtime Binance + Backtesting + React Frontend**")

# Sidebar
with st.sidebar:
    st.header("Settings")
    symbol = st.selectbox("Select Symbol", config.data.supported_symbols, index=0)
    period = st.selectbox("Data Period", ["6mo", "1y", "2y", "5y"], index=1)
    interval = st.selectbox("Interval", ["1d", "1h"], index=0)
    steps = st.slider("Forecast Steps (days)", 1, 30, 7)
    use_sentiment = st.checkbox("Use Sentiment", value=True)
    st.divider()
    st.markdown("**Model Weights (v2)**")
    w_lstm = st.slider("LSTM", 0.0, 1.0, 0.35)
    w_trans = st.slider("Transformer", 0.0, 1.0, 0.35)
    w_xgb = st.slider("XGBoost", 0.0, 1.0, 0.2)
    w_arima = st.slider("ARIMA", 0.0, 1.0, 0.1)
    st.divider()
    if st.button("Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()

@st.cache_data(ttl=600)
def load_data(symbol, period, interval, use_sentiment):
    fetcher = CryptoDataFetcher(symbol=symbol)
    fetcher.period = period
    fetcher.interval = interval
    df = fetcher.load_or_fetch(symbol=symbol, force_refresh=False)
    engineer = FeatureEngineer()
    feat_df = engineer.engineer(df)
    if use_sentiment:
        try:
            senti = SentimentFeatureEngineer()
            feat_df = senti.enrich_price_df(feat_df, symbol=symbol)
        except Exception as e:
            st.warning(f"Sentiment enrichment failed: {e}")
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

@st.cache_data(ttl=60)
def get_realtime_price(symbol):
    try:
        fetcher = BinanceRealtimeFetcher(symbol=symbol)
        price = fetcher.get_current_price()
        ticker = fetcher.fetch_ticker_rest()
        return price, ticker, None
    except Exception as e:
        return None, None, str(e)

@st.cache_data(ttl=300)
def get_sentiment(symbol):
    try:
        eng = SentimentFeatureEngineer()
        df = eng.get_daily_sentiment(symbol=symbol, days=14)
        return df, None
    except Exception as e:
        return None, str(e)

# Load data
with st.spinner(f"Loading {symbol} data..."):
    try:
        raw_df, feat_df = load_data(symbol, period, interval, use_sentiment)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

# Metrics row
col1, col2, col3, col4, col5 = st.columns(5)
current_price = raw_df['Close'].iloc[-1]
prev_price = raw_df['Close'].iloc[-2]
change_pct = (current_price - prev_price) / prev_price * 100

col1.metric(f"{symbol} Price", f"${current_price:,.2f}", f"{change_pct:+.2f}%")
col2.metric("Volume", f"{raw_df['Volume'].iloc[-1]:,.0f}")
col3.metric("RSI (14)", f"{feat_df['RSI'].iloc[-1]:.1f}" if 'RSI' in feat_df else "N/A")
col4.metric("Volatility", f"{feat_df['Volatility'].iloc[-1]*100:.2f}%" if 'Volatility' in feat_df else "N/A")
if 'Sentiment_Compound' in feat_df.columns:
    col5.metric("Sentiment", f"{feat_df['Sentiment_Compound'].iloc[-1]:.2f}", f"MA7 {feat_df['Sentiment_MA7'].iloc[-1]:.2f}" if 'Sentiment_MA7' in feat_df else "")
else:
    col5.metric("Features", f"{len(feat_df.columns)}")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Price Chart", "🔮 Forecast", "💬 Sentiment", "📡 Realtime", "📊 Backtest", "📋 Features"])

with tab1:
    st.subheader(f"{symbol} Price History")
    fig = plot_price_history(feat_df.tail(200), symbol=symbol)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=feat_df.index, y=feat_df['RSI'], name='RSI'))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(title="RSI", template="plotly_dark", height=300)
        st.plotly_chart(fig_rsi, use_container_width=True)
        if 'Sentiment_Compound' in feat_df.columns:
            fig_sent = go.Figure()
            fig_sent.add_trace(go.Scatter(x=feat_df.index, y=feat_df['Sentiment_Compound'], name='Sentiment'))
            fig_sent.add_trace(go.Scatter(x=feat_df.index, y=feat_df['Sentiment_MA7'], name='MA7'))
            fig_sent.update_layout(title="Sentiment", template="plotly_dark", height=300)
            st.plotly_chart(fig_sent, use_container_width=True)
    with col_b:
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=feat_df.index, y=feat_df['MACD'], name='MACD'))
        fig_macd.add_trace(go.Scatter(x=feat_df.index, y=feat_df['MACD_Signal'], name='Signal'))
        fig_macd.add_trace(go.Bar(x=feat_df.index, y=feat_df['MACD_Hist'], name='Hist'))
        fig_macd.update_layout(title="MACD", template="plotly_dark", height=300)
        st.plotly_chart(fig_macd, use_container_width=True)

with tab2:
    st.subheader(f"Forecast next {steps} days (v2: LSTM + Transformer)")
    fc, signal, err = get_forecast(symbol, steps, period)

    if err:
        st.warning(f"Models not trained yet or error: {err}")
        st.info(f"Run `python scripts/train.py --symbol {symbol} --period 2y`")
    else:
        if signal:
            color_map = {"STRONG_BUY": "green", "BUY": "lightgreen", "HOLD": "gray", "SELL": "orange", "STRONG_SELL": "red"}
            st.markdown(f"""
            <div style="padding:15px; border-radius:10px; background-color:{color_map.get(signal['signal'],'gray')}; color:white">
                <h3 style="margin:0">Signal: {signal['signal']} (Confidence: {signal['confidence']}%)</h3>
                <p style="margin:5px 0 0 0">Current: ${signal['current_price']:.2f} → Predicted: ${signal['predicted_price']:.2f} ({signal['change_pct']:+.2f}%)<br>{signal['reason']}</p>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        if fc and 'dates' in fc:
            fig_fc = go.Figure()
            hist = raw_df.tail(60)
            fig_fc.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Historical', line=dict(color='white')))

            future_dates = pd.to_datetime(fc['dates'])
            for model_name in ['lstm', 'transformer', 'xgboost', 'arima', 'ensemble']:
                if model_name in fc and fc[model_name]:
                    fig_fc.add_trace(go.Scatter(
                        x=future_dates, y=fc[model_name],
                        name=f"{model_name.upper()}",
                        line=dict(dash='dash' if model_name!='ensemble' else 'solid', width=3 if model_name=='ensemble' else 2)
                    ))

            fig_fc.update_layout(title=f"{symbol} Forecast v2", template="plotly_dark", height=500)
            st.plotly_chart(fig_fc, use_container_width=True)

            df_fc = pd.DataFrame({
                "Date": fc['dates'],
                **{k.upper(): v for k, v in fc.items() if k in ['lstm','transformer','xgboost','arima','ensemble']}
            })
            st.dataframe(df_fc, use_container_width=True)

with tab3:
    st.subheader("Sentiment Analysis")
    senti_df, senti_err = get_sentiment(symbol)
    if senti_err:
        st.error(senti_err)
    elif senti_df is not None and not senti_df.empty:
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=senti_df.index, y=senti_df['sentiment_compound'], name='Compound', line=dict(color='#00d395')))
        fig_s.add_trace(go.Scatter(x=senti_df.index, y=senti_df['sentiment_pos'], name='Positive', line=dict(color='green', dash='dot')))
        fig_s.add_trace(go.Scatter(x=senti_df.index, y=senti_df['sentiment_neg'], name='Negative', line=dict(color='red', dash='dot')))
        fig_s.update_layout(title=f"{symbol} Sentiment (14d)", template="plotly_dark", height=400)
        st.plotly_chart(fig_s, use_container_width=True)
        st.dataframe(senti_df.tail(14), use_container_width=True)

        st.markdown("**Analyze Custom Text**")
        txt = st.text_area("Enter text to analyze sentiment", "Bitcoin is extremely bullish, going to the moon! Strong buy signal.")
        if st.button("Analyze Sentiment"):
            from crypto_prediction.features.sentiment import SentimentAnalyzer
            analyzer = SentimentAnalyzer()
            res = analyzer.analyze(txt)
            st.json(res)
    else:
        st.info("No sentiment data available")

with tab4:
    st.subheader("Realtime Binance Feed")
    price, ticker, rt_err = get_realtime_price(symbol)
    if rt_err:
        st.error(rt_err)
    else:
        col1, col2 = st.columns(2)
        col1.metric("Live Binance Price", f"${float(price or ticker.get('lastPrice',0)):,.2f}")
        if ticker:
            col2.metric("24h Change", f"{ticker.get('priceChangePercent','0')}%", f"Vol {float(ticker.get('volume',0)):,.0f}")
            st.json(ticker)
        if st.button("Refresh Realtime"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("""
        **Realtime Architecture**
        - WebSocket: `wss://stream.binance.com:9443/ws/btcusdt@trade`
        - REST fallback: `/api/v3/ticker/24hr`
        - Buffer: deque 1000 trades, callbacks
        - LivePredictor merges live price with model forecast
        """)

with tab5:
    st.subheader("Backtesting Engine")
    strat_name = st.selectbox("Strategy", ["MA 20/50", "RSI 30/70", "Ensemble"])
    if st.button("Run Backtest"):
        with st.spinner("Running backtest..."):
            try:
                if strat_name == "MA 20/50":
                    strat = MovingAverageStrategy(20, 50)
                elif strat_name == "RSI 30/70":
                    strat = RSIStrategy(30, 70)
                else:
                    strat = EnsembleSignalStrategy()

                engine = BacktestEngine(initial_capital=10000)
                result = engine.run(feat_df, strat)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Return", f"{result.metrics['total_return_pct']:.2f}%")
                col2.metric("Sharpe", f"{result.metrics['sharpe_ratio']:.2f}")
                col3.metric("Max DD", f"{result.metrics['max_drawdown_pct']:.2f}%")
                col4.metric("Win Rate", f"{result.metrics['win_rate_pct']:.1f}%")

                fig_eq = go.Figure()
                fig_eq.add_trace(go.Scatter(x=result.equity_curve.index, y=result.equity_curve.values, name='Equity'))
                fig_eq.update_layout(title=f"Equity Curve - {strat.name}", template="plotly_dark", height=400)
                st.plotly_chart(fig_eq, use_container_width=True)

                st.dataframe(result.trades.tail(20), use_container_width=True)

            except Exception as e:
                st.error(f"Backtest failed: {e}")

with tab6:
    st.subheader("Feature Overview v2")
    st.write(f"Total features: {len(feat_df.columns)}")
    st.write(f"Includes sentiment: {'Sentiment_Compound' in feat_df.columns}")
    imp_path = config.project_root / "models" / f"{symbol.replace('-','_')}_feature_importance.csv"
    if imp_path.exists():
        imp_df = pd.read_csv(imp_path)
        fig_imp = go.Figure(go.Bar(x=imp_df.head(15)['importance'], y=imp_df.head(15)['feature'], orientation='h'))
        fig_imp.update_layout(template="plotly_dark", height=500, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_imp, use_container_width=True)
    st.dataframe(feat_df.tail(20), use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("Built with ❤️ | Crypto Prediction v2.0 | Transformer + Sentiment + Realtime + Backtest + React")
