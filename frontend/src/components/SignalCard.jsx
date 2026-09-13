import { useSettingsStore } from '../store/useSettingsStore'

export default function SignalCard({ signal, symbol, realtimePrice }) {
  const theme = useSettingsStore(s => s.theme)
  const isLight = theme === 'light' || theme === 'mono'
  
  if (!signal) {
    return (
      <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5 gpu-accelerated">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-zinc-400 animate-pulse" />
          </div>
          <div>
            <div className="font-medium text-[13px] text-zinc-900 dark:text-white">Signal</div>
            <div className="text-[11px] text-zinc-500">Awaiting prediction</div>
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
    <div className="relative rounded-xl border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 overflow-hidden gpu-accelerated hover-lift">
      <div className="p-5">
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-center gap-2.5">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center text-[12px] font-medium gpu-accelerated ${isBuy ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' : isSell ? 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700' : 'bg-zinc-50 dark:bg-zinc-800 text-zinc-500 border border-zinc-200 dark:border-zinc-700'}`}>
              {isBuy ? '↗' : isSell ? '↘' : '→'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[14px] tracking-tight text-zinc-900 dark:text-white">{symbol}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${isBuy ? 'bg-zinc-900 text-white border-zinc-900 dark:bg-white dark:text-black' : 'bg-zinc-50 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700'}`}>
                  {signal.signal}
                </span>
              </div>
              <div className="text-[11px] text-zinc-500 mt-0.5">
                AI Ensemble • {confidence.toFixed(0)}% confidence
              </div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] font-medium tracking-wide text-zinc-500 uppercase">Confidence</div>
            <div className="text-[20px] font-semibold mono tracking-tight text-zinc-900 dark:text-white">{confidence.toFixed(0)}%</div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-5">
          <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800">
            <div className="text-[10px] font-medium tracking-wide text-zinc-500 uppercase">Current</div>
            <div className="mono font-semibold text-[14px] text-zinc-900 dark:text-white mt-1">${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <div className="text-[11px] text-zinc-500 mt-1 flex items-center gap-1">
              <div className="live-dot !w-1 !h-1"></div> Live
            </div>
          </div>
          <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800">
            <div className="text-[10px] font-medium tracking-wide text-zinc-500 uppercase">Predicted 7d</div>
            <div className="mono font-semibold text-[14px] text-zinc-900 dark:text-white mt-1">${predictedPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <div className={`text-[11px] font-medium mt-1 flex items-center gap-1 mono ${changePct >= 0 ? 'text-zinc-900 dark:text-white' : 'text-zinc-500'}`}>
              {changePct >= 0 ? '↗' : '↘'} {changePct >= 0 ? '+' : ''}{changePct.toFixed(2)}%
            </div>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/30 border border-zinc-200 dark:border-zinc-800">
          <div className="text-[10px] font-medium tracking-wide text-zinc-500 uppercase mb-1">Reasoning</div>
          <div className="text-[12px] text-zinc-600 dark:text-zinc-300 leading-relaxed">
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
      isBuy ? 'bg-zinc-900 text-white border-zinc-900 dark:bg-white dark:text-black' :
      'bg-zinc-50 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700'
    }`}>
      {isBuy ? '↗' : '↘'} {signal.signal} • {signal.confidence?.toFixed(0)}%
    </div>
  )
}
