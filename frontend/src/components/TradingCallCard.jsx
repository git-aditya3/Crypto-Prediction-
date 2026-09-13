import { useSettingsStore } from '../store/useSettingsStore'

const safeFixed = (v, d=2) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toFixed(d) }
const safeLocale = (v) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toLocaleString(undefined, { maximumFractionDigits: 2 }) }

export default function TradingCallCard({ call, onSelect, isSelected = false }) {
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
          ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)] scale-[1.01] ring-2 ring-[var(--accent-ring)]' 
          : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)]'
      }`}
      style={{ willChange: 'transform, border-color' }}
    >
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-[11px] font-semibold gpu-accelerated transition-transform duration-200 group-hover:scale-110 group-hover:rotate-3 ${
              isSelected 
                ? 'bg-white/20 text-white' 
                : isBuy ? 'bg-[var(--buy)] text-white shadow-sm' 
                : isSell ? 'bg-[var(--sell-soft)] text-[var(--sell)] border border-[var(--sell-border)]' 
                : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border border-[var(--border)]'
            }`}>
              {isBuy ? '↗' : isSell ? '↘' : '→'}
            </div>
            <div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className={`font-semibold text-[13px] tracking-tight ${isSelected ? 'text-white' : 'text-[var(--text)]'}`}>{call.symbol}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                  isSelected ? 'bg-white/20 text-white border-white/20' :
                  isBuy ? 'bg-[var(--buy)] text-white border-[var(--buy)]' 
                  : isSell ? 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]' 
                  : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border-[var(--border)]'
                }`}>
                  {call.signal}
                </span>
                {isHighConf && <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold ${isSelected ? 'bg-white text-[var(--accent)]' : 'bg-[var(--accent)] text-white'}`}>HIGH</span>}
              </div>
              <div className={`text-[11px] mt-1 flex items-center gap-1.5 ${isSelected ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>
                <span>{call.action}</span>
                <span className="w-0.5 h-0.5 rounded-full bg-current opacity-50" />
                <span className="font-medium mono">{safeFixed(confidence,0)}%</span>
                <span className="w-0.5 h-0.5 rounded-full bg-current opacity-50" />
                <span>{call.timeframe || '1d'}</span>
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <div className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${isSelected ? 'bg-white/20 text-white border-white/20' : call.risk_level === 'LOW' ? 'bg-[var(--buy-soft)] text-[var(--buy)] border-[var(--buy-border)]' : call.risk_level === 'HIGH' ? 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]' : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border-[var(--border)]'}`}>
              {call.risk_level || 'MEDIUM'}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-2.5">
          <div className={`p-2.5 rounded-lg border ${isSelected ? 'bg-white/10 border-white/20' : 'bg-[var(--bg-secondary)] border-[var(--border)]'}`}>
            <div className={`text-[9px] font-medium uppercase tracking-wide ${isSelected ? 'text-white/60' : 'text-[var(--text-muted)]'}`}>Entry</div>
            <div className={`mono font-semibold text-[12px] mt-1 tracking-tight ${isSelected ? 'text-white' : 'text-[var(--text)]'}`}>${safeLocale(entry)}</div>
          </div>
          <div className={`p-2.5 rounded-lg border ${isSelected ? 'bg-white/10 border-white/20' : 'bg-[var(--sell-soft)] border-[var(--sell-border)]'}`}>
            <div className={`text-[9px] font-medium uppercase tracking-wide ${isSelected ? 'text-white/60' : 'text-[var(--sell)]'}`}>SL</div>
            <div className={`mono font-semibold text-[12px] mt-1 ${isSelected ? 'text-white' : 'text-[var(--sell)]'}`}>${safeLocale(sl)}</div>
          </div>
          <div className={`p-2.5 rounded-lg border ${isSelected ? 'bg-white text-[var(--accent)] border-white' : 'bg-[var(--buy)] border-[var(--buy)] text-white shadow-sm'}`}>
            <div className={`text-[9px] font-medium uppercase tracking-wide ${isSelected ? 'text-[var(--accent)]/70' : 'text-white/70'}`}>TP1</div>
            <div className="mono font-semibold text-[12px] mt-1">${safeLocale(tp1)}</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-3">
          {[
            { label: 'TP2', value: tp2 },
            { label: 'TP3', value: tp3 },
            { label: 'R:R', value: `1:${safeFixed(rr1,1)}`, isRatio: true },
          ].map((item, i) => (
            <div key={i} className={`p-2 rounded-lg text-center border ${isSelected ? 'bg-white/10 border-white/20' : 'bg-[var(--card)] border-[var(--border)]'}`}>
              <div className={`text-[9px] uppercase tracking-wide ${isSelected ? 'text-white/60' : 'text-[var(--text-muted)]'}`}>{item.label}</div>
              <div className={`mono font-medium text-[11px] mt-0.5 ${isSelected ? 'text-white' : 'text-[var(--text)]'}`}>{item.isRatio ? item.value : `$${safeLocale(item.value)}`}</div>
            </div>
          ))}
        </div>

        <div className={`flex items-center justify-between pt-2.5 border-t ${isSelected ? 'border-white/20' : 'border-[var(--border)]'}`}>
          <span className={`text-[11px] ${isSelected ? 'text-white/60' : 'text-[var(--text-muted)]'}`}>
            {call.timestamp ? new Date(call.timestamp).toLocaleTimeString() : 'Just now'}
          </span>
          <span className={`px-3 py-1 rounded-full font-medium text-[11px] gpu-accelerated transition-transform duration-200 group-hover:scale-105 ${isBuy ? 'bg-[var(--buy)] text-white shadow-sm' : 'bg-[var(--bg-secondary)] text-[var(--text-sec)] border border-[var(--border)]'}`}>
            {call.action}
          </span>
        </div>

        <div className="mt-2.5 h-1 w-full bg-[var(--bg-secondary)] rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{ 
              width: `${Math.min(100, Math.max(5, confidence))}%`, 
              background: isBuy ? 'var(--buy)' : 'var(--accent)',
              transform: 'translateZ(0)', 
              willChange: 'width' 
            }}
          />
        </div>
      </div>
    </div>
  )
}

export function TradingCallSummary({ summary }) {
  if (!summary) return null
  
  const cards = [
    { label: 'Total', value: summary.total ?? 0, sub: `${summary.buys ?? 0}B ${summary.sells ?? 0}S ${summary.holds ?? 0}H`, accent: true },
    { label: 'Buys', value: summary.buys ?? 0, sub: 'Long', color: 'buy' },
    { label: 'Sells', value: summary.sells ?? 0, sub: 'Short', color: 'sell' },
    { label: 'Confidence', value: `${Math.round(summary.avg_confidence || 0)}%`, sub: `${summary.high_confidence ?? 0} high`, color: 'accent' },
  ]
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 stagger-children">
      {cards.map((c, i) => (
        <div key={i} className={`group p-4 rounded-xl border transition-all duration-200 hover:translate-y-[-1px] gpu-accelerated ${c.accent ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)]'}`}>
          <div className={`text-[10px] font-medium uppercase tracking-wide ${c.accent ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>{c.label}</div>
          <div className={`text-[20px] font-semibold mono tracking-tight mt-1 ${c.accent ? 'text-white' : c.color === 'buy' ? 'text-[var(--buy)]' : c.color === 'sell' ? 'text-[var(--sell)]' : 'text-[var(--text)]'}`}>{c.value}</div>
          <div className={`text-[11px] mt-1 ${c.accent ? 'text-white/60' : 'text-[var(--text-muted)]'}`}>{c.sub}</div>
        </div>
      ))}
    </div>
  )
}
