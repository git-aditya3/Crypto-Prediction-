import { TrendingUp, TrendingDown, Minus, Zap, Target, Shield, Clock } from 'lucide-react'

export default function SignalCard({ signal, symbol, realtimePrice }) {
  if (!signal) {
    return (
      <div className="rounded-2xl border border-crypto-border/50 bg-crypto-card/30 p-6 backdrop-blur-xl">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-crypto-card border border-crypto-border flex items-center justify-center">
            <Clock size={18} className="text-crypto-muted" />
          </div>
          <div>
            <div className="font-semibold text-white">Trading Signal</div>
            <div className="text-xs text-crypto-muted">Awaiting model prediction</div>
          </div>
        </div>
        <div className="shimmer h-20 rounded-xl"></div>
      </div>
    )
  }

  const isBuy = signal.signal?.includes('BUY')
  const isSell = signal.signal?.includes('SELL')
  const isHold = !isBuy && !isSell

  const signalConfig = {
    BUY: { 
      color: 'from-crypto-bull to-emerald-600', 
      bg: 'bg-crypto-bull/10', 
      border: 'border-crypto-bull/20', 
      text: 'text-crypto-bull',
      icon: TrendingUp,
      label: 'STRONG BUY'
    },
    SELL: { 
      color: 'from-crypto-bear to-red-600', 
      bg: 'bg-crypto-bear/10', 
      border: 'border-crypto-bear/20', 
      text: 'text-crypto-bear',
      icon: TrendingDown,
      label: 'STRONG SELL'
    },
    HOLD: { 
      color: 'from-crypto-muted to-gray-600', 
      bg: 'bg-crypto-muted/10', 
      border: 'border-crypto-border', 
      text: 'text-crypto-muted',
      icon: Minus,
      label: 'HOLD'
    }
  }

  const config = isBuy ? signalConfig.BUY : isSell ? signalConfig.SELL : signalConfig.HOLD
  const Icon = config.icon
  const currentPrice = realtimePrice || signal.current_price || 0
  const predictedPrice = signal.predicted_price || 0
  const changePct = signal.change_pct || ((predictedPrice - currentPrice) / currentPrice * 100) || 0
  const confidence = signal.confidence || 0

  return (
    <div className={`relative rounded-2xl border backdrop-blur-xl overflow-hidden ${config.bg} ${config.border}`}>
      {/* Gradient accent */}
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${config.color}`}></div>
      
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${config.color} flex items-center justify-center shadow-lg`}>
              <Icon size={20} className="text-black" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-lg tracking-tight text-white">{symbol}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-black tracking-widest ${config.bg} ${config.text} border ${config.border}`}>
                  {config.label}
                </span>
              </div>
              <div className="text-xs text-crypto-muted font-medium mt-0.5 flex items-center gap-2">
                <Zap size={10} />
                AI Ensemble • {confidence.toFixed(0)}% confidence
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-[10px] font-bold tracking-widest text-crypto-muted uppercase">Confidence</div>
            <div className={`text-2xl font-black mono ${config.text}`}>{confidence.toFixed(0)}%</div>
          </div>
        </div>

        {/* Price comparison */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="p-4 rounded-xl bg-crypto-bg/50 border border-crypto-border/30">
            <div className="text-[11px] font-bold tracking-widest text-crypto-muted uppercase mb-1">Current</div>
            <div className="mono font-bold text-lg text-white">${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <div className="text-xs text-crypto-muted mt-1 flex items-center gap-1">
              <div className="live-dot !w-1.5 !h-1.5"></div>
              Live Binance
            </div>
          </div>
          <div className="p-4 rounded-xl bg-crypto-bg/50 border border-crypto-border/30">
            <div className="text-[11px] font-bold tracking-widest text-crypto-muted uppercase mb-1">Predicted (7d)</div>
            <div className="mono font-bold text-lg text-white">${predictedPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <div className={`text-xs font-bold mt-1 flex items-center gap-1 ${changePct >= 0 ? 'text-crypto-bull' : 'text-crypto-bear'}`}>
              {changePct >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Reason */}
        <div className="p-4 rounded-xl bg-crypto-bg/30 border border-crypto-border/20">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-crypto-card border border-crypto-border flex items-center justify-center shrink-0 mt-0.5">
              <Target size={14} className="text-crypto-accent" />
            </div>
            <div>
              <div className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-1">AI Reasoning</div>
              <div className="text-sm text-white/80 leading-relaxed">
                {signal.reason || 'Ensemble model analysis based on LSTM, Transformer, XGBoost, and ARIMA predictions with technical indicators and sentiment.'}
              </div>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="grid grid-cols-3 gap-2 mt-6">
          <div className="p-3 rounded-xl bg-crypto-card/50 border border-crypto-border/30 text-center">
            <div className="text-[10px] font-bold tracking-widest text-crypto-muted uppercase">Risk</div>
            <div className="flex items-center justify-center gap-1 mt-1">
              <Shield size={12} className="text-crypto-accent" />
              <span className="text-xs font-bold text-white">{confidence > 80 ? 'Low' : confidence > 60 ? 'Medium' : 'High'}</span>
            </div>
          </div>
          <div className="p-3 rounded-xl bg-crypto-card/50 border border-crypto-border/30 text-center">
            <div className="text-[10px] font-bold tracking-widest text-crypto-muted uppercase">Horizon</div>
            <div className="text-xs font-bold text-white mt-1">7 Days</div>
          </div>
          <div className="p-3 rounded-xl bg-crypto-card/50 border border-crypto-border/30 text-center">
            <div className="text-[10px] font-bold tracking-widest text-crypto-muted uppercase">Model</div>
            <div className="text-xs font-bold text-white mt-1">Ensemble</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export function MiniSignal({ signal }) {
  if (!signal) return null
  const isBuy = signal.signal?.includes('BUY')
  const isSell = signal.signal?.includes('SELL')
  
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold border ${
      isBuy ? 'bg-crypto-bull/10 text-crypto-bull border-crypto-bull/20' :
      isSell ? 'bg-crypto-bear/10 text-crypto-bear border-crypto-bear/20' :
      'bg-crypto-muted/10 text-crypto-muted border-crypto-border'
    }`}>
      {isBuy ? <TrendingUp size={12} /> : isSell ? <TrendingDown size={12} /> : <Minus size={12} />}
      {signal.signal} • {signal.confidence?.toFixed(0)}%
    </div>
  )
}
