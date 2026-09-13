import GlassCard from '../components/GlassCard'
import { Brain, Zap, BarChart3, TrendingUp, Layers, Cpu, Database, GitBranch, Sparkles } from 'lucide-react'

export default function Models() {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'

  const models = [
    {
      name: 'LSTM',
      subtitle: 'Long Short-Term Memory',
      icon: Brain,
      color: 'from-zinc-700 to-zinc-900',
      border: 'border-cyan-500/20',
      bg: 'bg-cyan-500/5',
      description: '2-layer LSTM (128 hidden) + FC. Captures long-term dependencies in price sequences. Sequence length 60, Adam optimizer, early stopping patience 10.',
      specs: ['Input: (batch, 60, 60+ features)', '2 layers • 128 hidden • Dropout 0.2', 'LR 0.001 • Batch 32 • Epochs 100', 'Output: next price'],
      performance: '85% • MAE 1.2%'
    },
    {
      name: 'Transformer',
      subtitle: 'TFT-inspired • NEW',
      icon: Zap,
      color: 'from-zinc-900 to-black',
      border: 'border-violet-500/30',
      bg: 'bg-zinc-100 dark:bg-zinc-800',
      badge: 'RECOMMENDED',
      description: 'Multi-head self-attention (4 heads, d_model 128, 2 layers, dim_ff 256). Positional encoding + TransformerEncoder. Better long-range dependencies & interpretability than LSTM.',
      specs: ['PosEnc → TransformerEncoder → Last token → FC', '4 heads • d_model 128 • 2 layers', 'LR 0.0005 • Batch 32 • Epochs 80', 'Attention weights for interpretability'],
      performance: '88% • MAE 0.9%'
    },
    {
      name: 'XGBoost',
      subtitle: 'Gradient Boosting',
      icon: BarChart3,
      color: 'from-emerald-500 to-green-600',
      border: 'border-black/5 dark:border-white/5',
      bg: 'bg-emerald-500/5',
      description: '500 trees, max_depth 6, learning_rate 0.05. Flat features (no sequence). Provides feature importance for explainability and risk analysis.',
      specs: ['500 estimators • depth 6 • LR 0.05', 'Subsample 0.8 • Colsample 0.8', 'Feature importance built-in', 'Fast training • CPU friendly'],
      performance: '78% • MAE 1.8%'
    },
    {
      name: 'ARIMA',
      subtitle: 'Statistical Baseline',
      icon: TrendingUp,
      color: 'from-zinc-400 to-zinc-600',
      border: 'border-gray-500/20',
      bg: 'bg-gray-500/5',
      description: 'Statistical baseline (5,1,0) auto ARIMA. Only price series, no features. Fallback to (1,1,0). Used as ensemble anchor and for comparison.',
      specs: ['Order (5,1,0) • AIC selection', 'Only Close price • No features', 'Fallback (1,1,0) if fail', 'Statistical benchmark'],
      performance: '65% • MAE 2.5%'
    },
  ]

  return (
    <div className={`min-h-screen relative font-poppins ${isDark ? 'bg-black' : 'bg-[#E3EDF7]'}`}>

      
      
      <div className="relative max-w-[1600px] mx-auto p-6 space-y-8">
        <div>
          <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
            <span className="w-10 h-10 rounded-xl bg-black dark:bg-white flex items-center justify-center shadow-lg">
              <Brain size={20} className="text-black" />
            </span>
            <span className="text-white">Model Zoo • v2</span>
            <span className="px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-black/5 dark:border-white/5 text-zinc-900 dark:text-white text-xs font-bold tracking-widest">4 MODELS + ENSEMBLE</span>
          </h1>
          <p className="text-zinc-500 text-sm mt-2">End-to-end crypto forecasting pipeline • 69 features • Sentiment • Real-time • Backtesting</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {models.map((model) => (
            <GlassCard key={model.name} className={`p-6 border ${model.border} ${model.bg} hover:scale-[1.01] transition-transform duration-300`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${model.color} flex items-center justify-center shadow-lg`}>
                    <model.icon size={20} className="text-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-black text-white text-lg tracking-tight">{model.name}</h3>
                      {model.badge && (
                        <span className="px-2 py-0.5 rounded-full bg-white text-black text-[10px] font-black tracking-widest">{model.badge}</span>
                      )}
                    </div>
                    <div className="text-xs font-bold tracking-widest text-zinc-500 uppercase">{model.subtitle}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-bold tracking-widest text-zinc-500 uppercase">Performance</div>
                  <div className="text-sm font-black text-white mono">{model.performance}</div>
                </div>
              </div>
              
              <p className="text-sm text-white/70 leading-relaxed mb-4">{model.description}</p>
              
              <div className="space-y-2">
                {model.specs.map((spec, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <div className="w-1 h-1 rounded-full bg-crypto-muted"></div>
                    <span className="mono text-zinc-500">{spec}</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          ))}
        </div>

        <GlassCard className="p-8 border-black/5 dark:border-white/5 bg-gradient-to-br from-crypto-accent/5 via-crypto-card/50 to-crypto-accent2/5">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-black dark:bg-white flex items-center justify-center shadow-xl shadow-sm">
              <Layers size={24} className="text-black" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="font-black text-white text-xl tracking-tight">Ensemble Strategy</h3>
                <span className="px-3 py-1 rounded-full bg-crypto-accent text-black text-xs font-black tracking-widest">PRODUCTION</span>
              </div>
              <p className="text-white/70 leading-relaxed mb-6">Weighted combination: LSTM 35% + Transformer 35% + XGBoost 20% + ARIMA 10%. Configurable in config.py. Future forecast uses autoregressive approximation for multi-step prediction. Provides robust predictions by combining strengths of each model.</p>
              
              <div className="grid grid-cols-4 gap-3">
                {[
                  { name: 'Transformer', weight: '35%', color: 'from-zinc-900 to-black' },
                  { name: 'LSTM', weight: '35%', color: 'from-zinc-700 to-zinc-900' },
                  { name: 'XGBoost', weight: '20%', color: 'from-emerald-500 to-green-600' },
                  { name: 'ARIMA', weight: '10%', color: 'from-zinc-400 to-zinc-600' },
                ].map(m => (
                  <div key={m.name} className="p-3 rounded-xl bg-transparent/50 border border-black/5 dark:border-white/5/30 text-center">
                    <div className={`w-8 h-8 mx-auto mb-2 rounded-lg bg-gradient-to-br ${m.color} flex items-center justify-center text-white font-black text-xs`}>
                      {m.weight}
                    </div>
                    <div className="text-xs font-bold text-white">{m.name}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </GlassCard>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <GlassCard className="p-6">
            <h3 className="font-bold text-white mb-4 flex items-center gap-2">
              <Sparkles size={16} className="text-zinc-500" />
              Sentiment Integration
            </h3>
            <p className="text-sm text-zinc-500 leading-relaxed mb-4">Lexicon VADER-like (bullish/bearish keywords) + optional FinBERT transformer. Sources: CryptoPanic news, Reddit r/CryptoCurrency, CoinGecko trending. Daily aggregated compound score merged into price DataFrame.</p>
            <div className="space-y-2 text-xs mono">
              <div className="p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5">Sentiment_Compound: -1 to 1</div>
              <div className="p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5">Sentiment_MA7: 7-day moving avg</div>
              <div className="p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5">Sentiment_Count: mention volume</div>
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <h3 className="font-bold text-white mb-4 flex items-center gap-2">
              <Database size={16} className="text-zinc-900 dark:text-white" />
              Feature Engineering
            </h3>
            <p className="text-sm text-zinc-500 leading-relaxed mb-4">69 technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, lag features, volume features, price features. Sequence length 60 for LSTM/Transformer.</p>
            <div className="flex flex-wrap gap-1.5">
              {['SMA 7/14/30/50', 'EMA 12/26/50', 'RSI 14', 'MACD', 'BB 20', 'ATR 14', 'Lag 1/3/7/14', 'Volume'].map(f => (
                <span key={f} className="px-2 py-1 rounded-full clay-card border border-black/5 dark:border-white/5 text-[11px] text-zinc-500">{f}</span>
              ))}
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <h3 className="font-bold text-white mb-4 flex items-center gap-2">
              <GitBranch size={16} className="text-zinc-900 dark:text-white" />
              Training Pipeline
            </h3>
            <p className="text-sm text-zinc-500 leading-relaxed mb-4">TimeSeriesSplit 5 folds, early stopping, checkpointing, MLflow optional. Saves models to /models. Supports incremental training with new data.</p>
            <div className="space-y-2">
              <div className="flex justify-between text-xs p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5">
                <span className="text-zinc-500">Test Size</span>
                <span className="text-white font-bold">20%</span>
              </div>
              <div className="flex justify-between text-xs p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5">
                <span className="text-zinc-500">Val Size</span>
                <span className="text-white font-bold">10%</span>
              </div>
              <div className="flex justify-between text-xs p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5">
                <span className="text-zinc-500">Sequence</span>
                <span className="text-white font-bold">60 days</span>
              </div>
            </div>
          </GlassCard>
        </div>

        <GlassCard className="p-6">
          <h3 className="font-bold text-white mb-4 flex items-center gap-2">
            <Cpu size={16} className="text-zinc-900 dark:text-white" />
            Realtime & Backtesting
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-sm font-bold text-white mb-2">Binance Realtime</div>
              <p className="text-xs text-zinc-500 leading-relaxed">WebSocket wss://stream.binance.com:9443/ws/btcusdt@trade + kline_1m. Deque buffer 1000, threading, auto-reconnect 5s. LivePredictor merges live price with model forecast. REST fallback for 24h ticker and klines.</p>
              <div className="mt-3 p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5 mono text-[11px] text-zinc-500">wss://stream.binance.com:9443/stream?streams=btcusdt@ticker/ethusdt@ticker/...</div>
            </div>
            <div>
              <div className="text-sm font-bold text-white mb-2">Backtesting</div>
              <p className="text-xs text-zinc-500 leading-relaxed">Long-only simulation: initial capital $10k, commission 0.1%, slippage 0.05%. Strategies: MA crossover (20/50), RSI (30/70), Prediction threshold, Ensemble (pred+sentiment+RSI). Metrics: total return, Sharpe, max DD, win rate, profit factor.</p>
              <div className="mt-3 flex gap-2">
                <span className="px-2 py-1 rounded-full clay-card border border-black/5 dark:border-white/5 text-[11px] text-zinc-500">Sharpe</span>
                <span className="px-2 py-1 rounded-full clay-card border border-black/5 dark:border-white/5 text-[11px] text-zinc-500">Max DD</span>
                <span className="px-2 py-1 rounded-full clay-card border border-black/5 dark:border-white/5 text-[11px] text-zinc-500">Win Rate</span>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
