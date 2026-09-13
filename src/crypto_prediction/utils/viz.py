"""
Visualization utilities using Plotly
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

def plot_price_history(df: pd.DataFrame, symbol: str = "BTC-USD", save_path: Optional[str] = None):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.7, 0.3],
                        subplot_titles=(f'{symbol} Price', 'Volume'))
    
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="OHLC"
    ), row=1, col=1)

    if 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], name='SMA 20', line=dict(color='orange')), row=1, col=1)
    if 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', line=dict(color='blue')), row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='lightblue'), row=2, col=1)

    fig.update_layout(
        title=f"{symbol} - Price History with Indicators",
        xaxis_rangeslider_visible=False,
        height=800,
        template="plotly_dark"
    )
    if save_path:
        fig.write_html(save_path)
    return fig

def plot_prediction(actual: pd.Series, predicted: pd.Series, future: Optional[pd.Series] = None, symbol: str = "BTC-USD"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=actual.index, y=actual.values, name="Actual", line=dict(color='white')))
    fig.add_trace(go.Scatter(x=predicted.index, y=predicted.values, name="Predicted (Test)", line=dict(color='cyan', dash='dash')))
    
    if future is not None:
        fig.add_trace(go.Scatter(x=future.index, y=future.values, name="Future Forecast", line=dict(color='yellow')))
    
    fig.update_layout(
        title=f"{symbol} - Actual vs Predicted",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=500
    )
    return fig

def plot_feature_importance(importance_df: pd.DataFrame):
    fig = go.Figure(go.Bar(
        x=importance_df['importance'],
        y=importance_df['feature'],
        orientation='h',
        marker_color='teal'
    ))
    fig.update_layout(
        title="Feature Importance",
        template="plotly_dark",
        height=600,
        yaxis={'categoryorder':'total ascending'}
    )
    return fig
