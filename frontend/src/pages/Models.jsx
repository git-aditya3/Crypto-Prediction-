import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useSettingsStore } from '../store/useSettingsStore'
import GlassCard from '../components/GlassCard'
import { Brain, Zap, BarChart3, TrendingUp, Layers, Cpu, Database, GitBranch, Sparkles, CheckCircle, AlertCircle } from 'lucide-react'

export default function Models() {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const isDark = !isLight
  const [liveModels, setLiveModels] = useState(null)
  const [loading, setLoading] = useState(true)
  const [settings, setSettings] = useState(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [modelsData, settingsData] = await Promise.all([
          api.getModels().catch(() => null),
          api.getSettings().catch(() => null)
        ])
        if (modelsData) setLiveModels(modelsData)
        if (settingsData) setSettings(settingsData)
      } catch (e) {
        console.error('Models fetch failed', e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const models = [
    {
      name: 'LSTM',
      subtitle: 'Long Short-Term Memory',
      icon: Brain,
      color: 'from-zinc-700 to-zinc-900',
      border: 'border-cyan-500/20',
      bg: 'bg-cyan-500/5',
      description: '2-layer bidirectional LSTM (96 hidden) + attention pooling. Captures long-term dependencies in price sequences. Sequence length 60, Huber loss.',
      specs: ['Input: (batch, 60, 60+ features)', '2 layers • 96 hidden • bidirectional • attention', 'Huber loss • Adam • Early stopping', 'Output: next-day close'],
      performance: 'v6 • pretrained',
      files: liveModels?.models?.filter(m => m.includes('lstm'))?.length || 0
    },
    {
      name: 'Transformer',
      subtitle: 'Learnable Positional • NEW',
      icon: Zap,
      color: 'from-zinc-900 to-black',
      border: 'border-violet-500/30',
      bg: 'bg-zinc-100 dark:bg-zinc-800',
      badge: 'RECOMMENDED',
      description: '2 layers, d_model 96, 4 heads, learnable positional encoding + attention pooling. Better long-range dependencies & interpretability.',
      specs: ['PosEnc → TransformerEncoder → Attention Pool → FC', '4 heads • d_model 96 • 2 layers • 192 ff', 'Huber loss • LR 0.001', 'Attention weights for interpretability'],
      performance: 'v6 • pretrained',
      files: liveModels?.models?.filter(m => m.includes('transformer'))?.length || 0
    },
    {
      name: 'XGBoost',
      subtitle: 'Gradient Boosting',
      icon: BarChart3,
      color: 'from-emerald-500 to-green-600',
      border: 'border-black/5 dark:border-white/5',
      bg: 'bg-emerald-500/5',
      description: '400 trees, max_depth 6, early stopping. Flat features (no sequence). Provides feature importance for explainability.',
      specs: ['400 estimators • depth 6 • LR 0.03', 'Subsample 0.8 • Colsample 0.8', 'Feature importance built-in', 'Fast training • CPU friendly'],
      performance: 'v6 • pretrained',
      files: liveModels?.models?.filter(m => m.includes('xgb'))?.length || 0
    },
    {
      name: 'ARIMA',
      subtitle: 'Statistical Baseline',
      icon: TrendingUp,
      color: 'from-zinc-400 to-zinc-600',
      border: 'border-gray-500/20',
      bg: 'bg-gray-500/5',
      description: 'SARIMAX auto order selection with weekly seasonality. Only price series, no features. Fallback to (1,1,0). Ensemble anchor.',
      specs: ['Order auto (SARIMAX) • AIC selection', 'Only Close price • No features', 'Weekly seasonality • Exog support', 'Statistical benchmark'],
      performance: 'v6 • pretrained',
      files: liveModels?.models?.filter(m => m.includes('arima'))?.length || 0
    },
  ]

  return (
    <div className={`min-h-screen relative ${isDark ? 'theme-bg' : 'theme-bg'}`}>
      <div className="relative max-w-[1600px] mx-auto p-4 md:p-6 space-y-6">
        <div>
          <h1 className="text-[24px] font-semibold tracking-tight flex items-center gap-3 text-[var(--text)]">
            <span className="w-9 h-9 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center shadow-[var(--glow)]">
              <Brain size={18} />
            </span>
            Model Zoo
            <span className="px-2.5 py-0.5 rounded-full bg-[var(--card)] border border-[var(--border)] text-[var(--text)] text-[11px] font-medium">4 MODELS + ENSEMBLE</span>
            <span className="px-2.5 py-0.5 rounded-full bg-[var(--buy-soft)] border border-[var(--buy-border)] text-[var(--buy)] text-[10px] font-bold">{liveModels?.count || 0} artifacts</span>
          </h1>
          <p className="text-[13px] mt-2 text-[var(--text-muted)]">End-to-end crypto forecasting pipeline • 300+ features • v6 ULTRA • Real-time • Backtesting • {loading ? 'loading...' : `${liveModels?.count || 0} bundled files`}</p>
        </div>

        <GlassCard className="p-5 border border-[var(--border)]">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2">
              <Database size={14} className="text-[var(--accent)]" /> Live Bundled Models
              {loading && <span className="w-3 h-3 border-2 border-[var(--border)] border-t-[var(--accent)] rounded-full animate-spin ml-2" />}
            </h3>
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${liveModels?.continuous_training ? 'bg-[var(--buy-soft)] border-[var(--buy-border)] text-[var(--buy)]' : 'bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-muted)]'}`}>
                {liveModels?.continuous_training ? '● Training ON' : '○ Training OFF'}
              </span>
              <span className="px-2 py-1 rounded-full bg-[var(--card)] border border-[var(--border)] text-[10px] text-[var(--text-muted)]">v6 ULTRA</span>
            </div>
          </div>

          {liveModels ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                {[
                  { sym: 'BTC-USD', key: 'BTC' },
                  { sym: 'ETH-USD', key: 'ETH' },
                  { sym: 'BNB-USD', key: 'BNB' },
                  { sym: 'XRP-USD', key: 'XRP' },
                  { sym: 'ADA-USD', key: 'ADA' },
                  { sym: 'SOL-USD', key: 'SOL' },
                ].map(({ sym, key }) => {
                  const has = liveModels.models?.some(m => m.startsWith(key) || m.startsWith(key.replace('-','_')))
                  return (
                    <div key={sym} className={`p-2.5 rounded-xl border flex items-center justify-between transition-all ${has ? 'bg-[var(--buy-soft)] border-[var(--buy-border)]' : 'bg-[var(--bg-secondary)] border-[var(--border)]'}`}>
                      <div>
                        <div className={`text-[12px] font-semibold ${has ? 'text-[var(--buy)]' : 'text-[var(--text-muted)]'}`}>{sym}</div>
                        <div className="text-[10px] text-[var(--text-muted)]">{has ? `${liveModels.models.filter(m=>m.startsWith(key)).length} files` : 'not bundled'}</div>
                      </div>
                      {has ? <CheckCircle size={14} className="text-[var(--buy)]" /> : <AlertCircle size={14} className="text-[var(--text-muted)]" />}
                    </div>
                  )
                })}
              </div>
              <details className="group">
                <summary className="cursor-pointer text-[11px] font-medium text-[var(--text-muted)] hover:text-[var(--text)] list-none flex items-center gap-1">
                  <span className="group-open:rotate-90 transition-transform">▶</span> Show all {liveModels.count} artifact files
                </summary>
                <div className="mt-2 max-h-[140px] overflow-y-auto p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] mono text-[var(--text-muted)] leading-relaxed">
                  {liveModels.models?.join(', ')}
                </div>
              </details>
              {settings && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
                  <div className="p-2 rounded-lg bg-[var(--card)] border border-[var(--border)]"><div className="text-[var(--text-muted)]">LSTM hidden</div><div className="font-semibold text-[var(--text)]">{settings.models?.lstm?.hidden_size} • {settings.models?.lstm?.num_layers} layers</div></div>
                  <div className="p-2 rounded-lg bg-[var(--card)] border border-[var(--border)]"><div className="text-[var(--text-muted)]">Transformer</div><div className="font-semibold text-[var(--text)]">d_model {settings.models?.transformer?.d_model} • {settings.models?.transformer?.nhead} heads</div></div>
                  <div className="p-2 rounded-lg bg-[var(--card)] border border-[var(--border)]"><div className="text-[var(--text-muted)]">XGBoost</div><div className="font-semibold text-[var(--text)]">{settings.models?.xgboost?.n_estimators} trees • depth {settings.models?.xgboost?.max_depth}</div></div>
                  <div className="p-2 rounded-lg bg-[var(--card)] border border-[var(--border)]"><div className="text-[var(--text-muted)]">Ensemble</div><div className="font-semibold text-[var(--text)]">{settings.models?.ensemble?.weights}</div></div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-[12px] text-[var(--text-muted)] p-4 text-center border border-dashed border-[var(--border)] rounded-xl">
              {loading ? 'Loading models from /models endpoint...' : 'Failed to load models – is backend running on :8000?'}
            </div>
          )}
        </GlassCard>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {models.map((model) => (
            <GlassCard key={model.name} className={`p-5 border ${model.border} hover:translate-y-[-2px] transition-all duration-200`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${model.color} flex items-center justify-center shadow-sm`}>
                    <model.icon size={18} className="text-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-[var(--text)] text-[14px] tracking-tight">{model.name}</h3>
                      {model.badge && (
                        <span className="px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[9px] font-bold tracking-widest">{model.badge}</span>
                      )}
                      <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-medium border ${model.files > 0 ? 'bg-[var(--buy-soft)] border-[var(--buy-border)] text-[var(--buy)]' : 'bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-muted)]'}`}>{model.files} files</span>
                    </div>
                    <div className="text-[11px] font-medium tracking-wide text-[var(--text-muted)] uppercase">{model.subtitle}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase">Status</div>
                  <div className="text-[11px] font-semibold text-[var(--text)] mono">{model.performance}</div>
                </div>
              </div>
              
              <p className="text-[12px] text-[var(--text-sec)] leading-relaxed mb-4">{model.description}</p>
              
              <div className="space-y-1.5">
                {model.specs.map((spec, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px]">
                    <div className="w-1 h-1 rounded-full bg-[var(--text-muted)]"></div>
                    <span className="mono text-[var(--text-muted)]">{spec}</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          ))}
        </div>

        <GlassCard className="p-6 border border-[var(--border)] bg-gradient-to-br from-[var(--accent-soft)] via-[var(--card)] to-[var(--bg-secondary)]">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center shadow-[var(--glow)]">
              <Layers size={20} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="font-semibold text-[var(--text)] text-[16px] tracking-tight">Ensemble Strategy</h3>
                <span className="px-2.5 py-0.5 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold tracking-widest">PRODUCTION</span>
                <span className="px-2 py-0.5 rounded-full bg-[var(--card)] border border-[var(--border)] text-[10px] text-[var(--text-muted)]">inverse-MAPE weighted</span>
              </div>
              <p className="text-[12px] text-[var(--text-sec)] leading-relaxed mb-5">Dynamic weighting from each symbol's training report: LSTM 35% + Transformer 35% + XGBoost 20% + ARIMA 10% base, then re-weighted by inverse MAPE. Future forecast uses autoregressive approximation for multi-step prediction.</p>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { name: 'Transformer', weight: '35%', color: 'from-zinc-900 to-black', desc: 'attention' },
                  { name: 'LSTM', weight: '35%', color: 'from-zinc-700 to-zinc-900', desc: 'sequence' },
                  { name: 'XGBoost', weight: '20%', color: 'from-emerald-500 to-green-600', desc: 'importance' },
                  { name: 'ARIMA', weight: '10%', color: 'from-zinc-400 to-zinc-600', desc: 'baseline' },
                ].map(m => (
                  <div key={m.name} className="p-3 rounded-xl bg-[var(--card)] border border-[var(--border)] text-center hover:border-[var(--border-strong)] transition">
                    <div className={`w-8 h-8 mx-auto mb-2 rounded-lg bg-gradient-to-br ${m.color} flex items-center justify-center text-white font-bold text-[11px]`}>
                      {m.weight}
                    </div>
                    <div className="text-[12px] font-semibold text-[var(--text)]">{m.name}</div>
                    <div className="text-[10px] text-[var(--text-muted)]">{m.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </GlassCard>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <GlassCard className="p-5">
            <h3 className="font-medium text-[var(--text)] mb-3 flex items-center gap-2 text-[13px]">
              <Sparkles size={14} className="text-[var(--accent)]" />
              Sentiment Integration
            </h3>
            <p className="text-[12px] text-[var(--text-muted)] leading-relaxed mb-3">Lexicon VADER-like + optional FinBERT. Sources: CryptoPanic news, Reddit r/CryptoCurrency, CoinGecko trending. Daily aggregated compound score merged into price DataFrame.</p>
            <div className="space-y-1.5 text-[11px] mono">
              <div className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">Sentiment_Compound: -1 to 1</div>
              <div className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">Sentiment_MA7: 7-day moving avg</div>
              <div className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">Sentiment_Count: mention volume</div>
            </div>
          </GlassCard>

          <GlassCard className="p-5">
            <h3 className="font-medium text-[var(--text)] mb-3 flex items-center gap-2 text-[13px]">
              <Database size={14} className="text-[var(--text)]" />
              Feature Engineering
            </h3>
            <p className="text-[12px] text-[var(--text-muted)] leading-relaxed mb-3">300+ indicators: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, lag features, volume features, volatility, regime. Sequence length 60 for LSTM/Transformer.</p>
            <div className="flex flex-wrap gap-1.5">
              {['SMA 7/14/30/50', 'EMA 12/26/50', 'RSI 14', 'MACD', 'BB 20', 'ATR 14', 'Lag 1/3/7/14', 'Volatility'].map(f => (
                <span key={f} className="px-2 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] text-[var(--text-muted)]">{f}</span>
              ))}
            </div>
          </GlassCard>

          <GlassCard className="p-5">
            <h3 className="font-medium text-[var(--text)] mb-3 flex items-center gap-2 text-[13px]">
              <GitBranch size={14} className="text-[var(--text)]" />
              Training Pipeline
            </h3>
            <p className="text-[12px] text-[var(--text-muted)] leading-relaxed mb-3">TimeSeriesSplit, early stopping, checkpointing. Saves to /models. Supports incremental training with new data. v6 ULTRA improvements.</p>
            <div className="space-y-2">
              <div className="flex justify-between text-[11px] p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
                <span className="text-[var(--text-muted)]">Test Size</span>
                <span className="text-[var(--text)] font-medium">{settings?.data?.test_size || '20%'}</span>
              </div>
              <div className="flex justify-between text-[11px] p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
                <span className="text-[var(--text-muted)]">Val Size</span>
                <span className="text-[var(--text)] font-medium">{settings?.data?.val_size || '10%'}</span>
              </div>
              <div className="flex justify-between text-[11px] p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
                <span className="text-[var(--text-muted)]">Sequence</span>
                <span className="text-[var(--text)] font-medium">{settings?.data?.sequence_length || 60} days</span>
              </div>
            </div>
          </GlassCard>
        </div>

        <GlassCard className="p-5">
          <h3 className="font-medium text-[var(--text)] mb-4 flex items-center gap-2 text-[13px]">
            <Cpu size={14} className="text-[var(--text)]" />
            Realtime & Backtesting
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-[12px] font-semibold text-[var(--text)] mb-2">Binance Realtime</div>
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">WebSocket wss://stream.binance.com:9443/ws/btcusdt@trade + kline_1m. Deque buffer 1000, threading, auto-reconnect 5s. LivePredictor merges live price with model forecast.</p>
              <div className="mt-3 p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] mono text-[11px] text-[var(--text-muted)]">wss://stream.binance.com:9443/stream?streams=btcusdt@ticker/...</div>
            </div>
            <div>
              <div className="text-[12px] font-semibold text-[var(--text)] mb-2">Backtesting</div>
              <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">Long-only simulation: initial capital $10k, commission 0.1%, slippage 0.05%. Strategies: MA crossover (20/50), RSI (30/70), Prediction threshold, Ensemble (pred+sentiment+RSI). Metrics: total return, Sharpe, max DD, win rate, profit factor.</p>
              <div className="mt-3 flex gap-2">
                <span className="px-2 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] text-[var(--text-muted)]">Sharpe</span>
                <span className="px-2 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] text-[var(--text-muted)]">Max DD</span>
                <span className="px-2 py-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[11px] text-[var(--text-muted)]">Win Rate</span>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
