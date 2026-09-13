export default function Models() {
  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Models v2</h1>

      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold text-crypto-accent">LSTM</h3>
          <p className="text-sm text-gray-400 mt-2">2-layer LSTM (128 hidden) + FC. Captures long-term dependencies. Sequence length 60. Trained with Adam, early stopping.</p>
          <div className="mt-3 text-xs mono bg-crypto-bg p-2 rounded">Input: (batch, 60, 60+ features) → Output: price</div>
        </div>
        <div className="card border-amber-500/30">
          <h3 className="font-semibold text-amber-400">Transformer (TFT-inspired) NEW</h3>
          <p className="text-sm text-gray-400 mt-2">Multi-head self-attention (4 heads, d_model 128, 2 layers). Positional encoding + TransformerEncoder. Better long-range & interpretability.</p>
          <div className="mt-3 text-xs mono bg-crypto-bg p-2 rounded">PosEnc → TransformerEncoder → Last token → FC → price</div>
        </div>
        <div className="card">
          <h3 className="font-semibold text-purple-400">XGBoost</h3>
          <p className="text-sm text-gray-400 mt-2">500 trees, max_depth 6. Flat features. Provides feature importance for explainability.</p>
        </div>
        <div className="card">
          <h3 className="font-semibold text-gray-300">ARIMA</h3>
          <p className="text-sm text-gray-400 mt-2">Statistical baseline (5,1,0). Only price series. Fallback to (1,1,0).</p>
        </div>
        <div className="card col-span-2 border-crypto-accent/30">
          <h3 className="font-semibold text-crypto-accent">Ensemble</h3>
          <p className="text-sm text-gray-400 mt-2">Weighted: LSTM 35% + Transformer 35% + XGB 20% + ARIMA 10%. Configurable in config.py. Future forecast uses autoregressive approximation.</p>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-3">Sentiment Integration</h3>
        <p className="text-sm text-gray-400">Lexicon VADER-like (bullish/bearish keywords) + optional FinBERT. Sources: CryptoPanic news, Reddit r/CryptoCurrency, CoinGecko trending. Daily aggregated compound score merged into price DataFrame as Sentiment_Compound, Sentiment_MA7, Sentiment_Diff.</p>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-3">Realtime Binance</h3>
        <p className="text-sm text-gray-400">WebSocket wss://stream.binance.com:9443/ws/btcusdt@trade + kline_1m. Deque buffer 1000, threading, auto-reconnect. LivePredictor merges live price with model forecast. REST fallback for 24h ticker.</p>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-3">Backtesting</h3>
        <p className="text-sm text-gray-400">Long-only simulation: initial capital $10k, commission 0.1%, slippage 0.05%. Strategies: MA crossover, RSI, Prediction threshold, Ensemble (pred+sentiment+RSI). Metrics: total return, Sharpe, max DD, win rate, profit factor.</p>
      </div>
    </div>
  )
}
