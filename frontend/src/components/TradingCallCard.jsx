import { useSettingsStore } from '../store/useSettingsStore'

const safeFixed = (v, d=2) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toFixed(d) }
const safeLocale = (v) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toLocaleString(undefined, { maximumFractionDigits: 2 }) }

export default function TradingCallCard({ call, onSelect, isSelected = false }) {
  const theme = useSettingsStore(s => s.theme)
  const isLight = theme === 'light' || theme === 'mono'
  if (!call) return null

  const isBuy = call.signal?.includes('BUY')
  const isSell = call.signal?.includes('SELL')

  const entry = call.entry_price ?? 0
  const sl = call.stop_loss ?? 0
  const tp1 = call.take_profits?.tp1 ?? 0
  const tp2 = call.take_profits?.tp2 ?? 0
  const tp3 = call.take_profits?.tp3 ?? 0
  const rr1 = call.risk_reward?.tp1 ?? 1
  const confidence = call.confidence ?? 0
  const isHighConf = confidence >= 80

  return (
    <div
      onClick={() => onSelect && onSelect(call)}
      className={`group relative rounded-xl overflow-hidden cursor-pointer border gpu-accelerated hover-lift ${
        isSelected 
          ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white shadow-md scale-[1.01]' 
          : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700'
      }`}
      style={{ willChange: 'transform, border-color' }}
    >
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[11px] font-semibold gpu-accelerated transition-transform duration-200 group-hover:scale-105 ${
              isSelected 
                ? 'bg-white/20 text-white dark:bg-black/10 dark:text-black' 
                : isBuy ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' 
                : 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700'
            }`}>
              {isBuy ? '↗' : isSell ? '↘' : '→'}
            </div>
            <div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className={`font-semibold text-[13px] tracking-tight ${isSelected ? 'text-white dark:text-black' : 'text-zinc-900 dark:text-white'}`}>{call.symbol}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                  isBuy ? 'bg-zinc-900 text-white border-zinc-900 dark:bg-white dark:text-black' 
                  : isSell ? 'bg-transparent text-zinc-500 border-zinc-300 dark:border-zinc-600' 
                  : 'bg-zinc-100 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700'
                }`}>
                  {call.signal}
                </span>
                {isHighConf && <span className="px-1.5 py-0.5 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black text-[9px] font-medium">HIGH</span>}
              </div>
              <div className={`text-[11px] mt-1 flex items-center gap-1.5 ${isSelected ? 'text-white/60 dark:text-black/60' : 'text-zinc-500'}`}>
                <span>{call.action}</span>
                <span className="w-0.5 h-0.5 rounded-full bg-zinc-400" />
                <span className="font-medium mono">{safeFixed(confidence,0)}%</span>
                <span className="w-0.5 h-0.5 rounded-full bg-zinc-400" />
                <span>{call.timeframe || '1d'}</span>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <div className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${isSelected ? 'bg-white/20 text-white border-white/20 dark:bg-black/10 dark:text-black dark:border-black/10' : 'bg-zinc-50 text-zinc-600 border-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:border-zinc-700'}`}>
              {call.risk_level || 'MEDIUM'}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-2.5">
          <div className={`p-2.5 rounded-lg border ${isLight ? 'bg-zinc-50 border-zinc-200' : 'bg-zinc-800/50 border-zinc-700/50'} ${isSelected ? '!bg-white/10 !border-white/20 dark:!bg-black/5 dark:!border-black/10' : ''}`}>
            <div className={`text-[9px] font-medium uppercase tracking-wide ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>Entry</div>
            <div className="mono font-semibold text-[12px] mt-1 tracking-tight">${safeLocale(entry)}</div>
          </div>
          <div className={`p-2.5 rounded-lg border bg-zinc-50 border-zinc-200 dark:bg-zinc-800/30 dark:border-zinc-800 ${isSelected ? '!bg-white/10 !border-white/20 dark:!bg-black/5' : ''}`}>
            <div className="text-[9px] font-medium uppercase tracking-wide text-zinc-500">SL</div>
            <div className="mono font-semibold text-[12px] mt-1 text-zinc-600 dark:text-zinc-400">${safeLocale(sl)}</div>
          </div>
          <div className={`p-2.5 rounded-lg border bg-zinc-900 border-zinc-900 dark:bg-white dark:border-white ${isSelected ? '!bg-white !text-black dark:!bg-black dark:!text-white' : ''}`}>
            <div className={`text-[9px] font-medium uppercase tracking-wide ${isSelected ? 'text-white/60 dark:text-black/60' : 'text-white/60 dark:text-black/60'}`}>TP1</div>
            <div className={`mono font-semibold text-[12px] mt-1 ${isSelected ? 'text-white dark:text-black' : 'text-white dark:text-black'}`}>${safeLocale(tp1)}</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-3">
          {[
            { label: 'TP2', value: tp2 },
            { label: 'TP3', value: tp3 },
            { label: 'R:R', value: `1:${safeFixed(rr1,1)}` },
          ].map((item, i) => (
            <div key={i} className={`p-2 rounded-lg text-center border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 ${isSelected ? '!bg-white/10 !border-white/20 dark:!bg-black/5' : ''}`}>
              <div className="text-[9px] uppercase tracking-wide text-zinc-500">{item.label}</div>
              <div className="mono font-medium text-[11px] mt-0.5">${typeof item.value === 'string' ? item.value : safeLocale(item.value)}</div>
            </div>
          ))}
        </div>

        <div className={`flex items-center justify-between pt-2.5 border-t ${isLight ? 'border-zinc-100' : 'border-zinc-800'} ${isSelected ? '!border-white/20 dark:!border-black/10' : ''}`}>
          <span className={`text-[11px] ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>
            {call.timestamp ? new Date(call.timestamp).toLocaleTimeString() : 'Just now'}
          </span>
          <span className={`px-3 py-1 rounded-full font-medium text-[11px] gpu-accelerated transition-transform duration-200 group-hover:scale-105 ${isBuy ? 'bg-zinc-900 text-white dark:bg-white dark:text-black' : 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300'}`}>
            {call.action}
          </span>
        </div>

        <div className="mt-2.5 h-1 w-full bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all duration-700 ease-out ${isBuy ? 'bg-zinc-900 dark:bg-white' : 'bg-zinc-400'}`}
            style={{ width: `${Math.min(100, Math.max(5, confidence))}%`, transform: 'translateZ(0)', willChange: 'width' }}
          />
        </div>
      </div>
    </div>
  )
}

export function TradingCallSummary({ summary }) {
  if (!summary) return null
  
  const cards = [
    { label: 'Total', value: summary.total ?? 0, sub: `${summary.buys ?? 0}B ${summary.sells ?? 0}S ${summary.holds ?? 0}H` },
    { label: 'Buys', value: summary.buys ?? 0, sub: 'Long' },
    { label: 'Sells', value: summary.sells ?? 0, sub: 'Short' },
    { label: 'Confidence', value: `${Math.round(summary.avg_confidence || 0)}%`, sub: `${summary.high_confidence ?? 0} high` },
  ]
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 stagger-children">
      {cards.map((c, i) => (
        <div key={i} className="group p-4 rounded-xl border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 hover:translate-y-[-1px] transition-all duration-200 gpu-accelerated">
          <div className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">{c.label}</div>
          <div className="text-[20px] font-semibold mono tracking-tight mt-1 text-zinc-900 dark:text-white">{c.value}</div>
          <div className="text-[11px] mt-1 text-zinc-500">{c.sub}</div>
        </div>
      ))}
    </div>
  )
}
