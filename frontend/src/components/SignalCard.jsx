export default function SignalCard({ signal, symbol, realtimePrice }) {
  if (!signal) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 gpu-accelerated">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-[var(--text-faint)] animate-pulse" />
          </div>
          <div>
            <div className="font-medium text-[13px] text-[var(--text)]">Signal</div>
            <div className="text-[11px] text-[var(--text-muted)]">Awaiting prediction</div>
          </div>
        </div>
        <div className="skeleton h-20 rounded-lg"></div>
      </div>
    )
  }

  const isBuy = signal.signal?.includes('BUY')
  const isSell = signal.signal?.includes('SELL')

  const currentPrice = realtimePrice || signal.current_price || 0
  const predictedPrice = signal.predicted_price || 0
  const changePct = signal.change_pct || ((predictedPrice - currentPrice) / currentPrice * 100) || 0
  const confidence = signal.confidence || 0

  return (
    <div className="relative rounded-xl border bg-[var(--card)] border-[var(--border)] overflow-hidden gpu-accelerated hover-lift">
      <div className={`absolute top-0 left-0 right-0 h-0.5 ${isBuy ? 'bg-[var(--buy)]' : isSell ? 'bg-[var(--sell)]' : 'bg-[var(--border)]'}`} />
      <div className="p-5">
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-[12px] font-bold gpu-accelerated shadow-sm ${isBuy ? 'bg-[var(--buy)] text-white' : isSell ? 'bg-[var(--sell)] text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border border-[var(--border)]'}`}>
              {isBuy ? '↗' : isSell ? '↘' : '→'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[14px] tracking-tight text-[var(--text)]">{symbol}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${isBuy ? 'bg-[var(--buy)] text-white border-[var(--buy)]' : isSell ? 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]' : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border-[var(--border)]'}`}>
                  {signal.signal}
                </span>
              </div>
              <div className="text-[11px] text-[var(--text-muted)] mt-0.5">
                AI Ensemble • {confidence.toFixed(0)}% confidence
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] font-medium tracking-wide text-[var(--text-muted)] uppercase">Confidence</div>
            <div className="text-[20px] font-semibold mono tracking-tight text-[var(--text)]">{confidence.toFixed(0)}%</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-5">
          <div className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
            <div className="text-[10px] font-medium tracking-wide text-[var(--text-muted)] uppercase">Current</div>
            <div className="mono font-semibold text-[14px] text-[var(--text)] mt-1">${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <div className="text-[11px] text-[var(--text-muted)] mt-1 flex items-center gap-1">
              <div className="live-dot !w-1 !h-1"></div> Live
            </div>
          </div>
          <div className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
            <div className="text-[10px] font-medium tracking-wide text-[var(--text-muted)] uppercase">Predicted 7d</div>
            <div className="mono font-semibold text-[14px] text-[var(--text)] mt-1">${predictedPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <div className={`text-[11px] font-medium mt-1 flex items-center gap-1 mono ${changePct >= 0 ? 'text-[var(--buy)]' : 'text-[var(--sell)]'}`}>
              {changePct >= 0 ? '↗' : '↘'} {changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%
            </div>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
          <div className="text-[10px] font-medium tracking-wide text-[var(--text-muted)] uppercase mb-1">Reasoning</div>
          <div className="text-[12px] text-[var(--text-sec)] leading-relaxed">
            {signal.reason || 'Ensemble analysis: LSTM, Transformer, XGBoost, ARIMA with 200+ features.'}
          </div>
        </div>
      </div>
    </div>
  )
}

export function MiniSignal({ signal }) {
  if (!signal) return null
  const isBuy = signal.signal?.includes('BUY')
  
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border gpu-accelerated ${
      isBuy ? 'bg-[var(--buy)] text-white border-[var(--buy)]' :
      'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]'
    }`}>
      {isBuy ? '↗' : '↘'} {signal.signal} • {signal.confidence?.toFixed(0)}%
    </div>
  )
}
