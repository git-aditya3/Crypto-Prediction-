import { TrendingUp, TrendingDown, Minus, Target, Shield, Zap, Clock } from 'lucide-react'
import { useSettingsStore } from '../store/useSettingsStore'

const safeFixed = (v, d=2) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toFixed(d) }
const safeLocale = (v) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toLocaleString(undefined, { maximumFractionDigits: 2 }) }

export default function TradingCallCard({ call, onSelect, isSelected = false }) {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'
  if (!call) return null

  const isBuy = call.signal?.includes('BUY')
  const isSell = call.signal?.includes('SELL')
  const Icon = isBuy ? TrendingUp : isSell ? TrendingDown : Minus

  const entry = call.entry_price ?? 0
  const sl = call.stop_loss ?? 0
  const tp1 = call.take_profits?.tp1 ?? 0
  const tp2 = call.take_profits?.tp2 ?? 0
  const tp3 = call.take_profits?.tp3 ?? 0
  const rr1 = call.risk_reward?.tp1 ?? 1
  const confidence = call.confidence ?? 0

  return (
    <div
      onClick={() => onSelect && onSelect(call)}
      className={`group relative rounded-[20px] overflow-hidden cursor-pointer transition-all border ${
        isSelected ? (isDark ? 'bg-white text-black border-white' : 'bg-black text-white border-black') : 'ui-card hover:translate-y-[-1px]'
      }`}
    >
      <div className={`h-1 w-full ${isBuy ? 'bg-emerald-500' : isSell ? 'bg-red-500' : 'bg-zinc-400'}`} />
      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${isSelected ? 'bg-black text-white dark:bg-black dark:text-white' : isBuy ? 'bg-emerald-500 text-black' : isSell ? 'bg-red-500 text-white' : 'bg-zinc-200 text-zinc-600'}`}>
              <Icon size={16} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-[15px]">{call.symbol}</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${isBuy ? 'ui-pill-buy' : isSell ? 'ui-pill-sell' : 'ui-pill'}`}>{call.signal}</span>
              </div>
              <div className={`text-[11px] mt-0.5 flex items-center gap-1 ${isSelected ? 'text-black/60 dark:text-white/60' : isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>
                <Zap size={10} /> {call.action} • {safeFixed(confidence,0)}% • {call.timeframe || '1d'}
              </div>
            </div>
          </div>
          <div className={`px-2 py-1 rounded-full text-[10px] font-bold ${call.risk_level === 'LOW' ? 'ui-pill-buy' : call.risk_level === 'HIGH' ? 'ui-pill-sell' : 'ui-pill'}`}>{call.risk_level || 'MEDIUM'}</div>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className={`p-3 rounded-xl ${isDark ? 'bg-black border border-white/5' : 'bg-zinc-50 border border-black/5'} ${isSelected ? '!bg-black/10 !border-black/10 dark:!bg-white/10' : ''}`}>
            <div className={`text-[9px] font-bold uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>Entry</div>
            <div className="mono font-bold text-[13px] mt-0.5">${safeLocale(entry)}</div>
          </div>
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/10">
            <div className="text-[9px] font-bold uppercase text-red-500">SL</div>
            <div className="mono font-bold text-[13px] mt-0.5 text-red-500">${safeLocale(sl)}</div>
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/10">
            <div className="text-[9px] font-bold uppercase text-emerald-600">TP1</div>
            <div className="mono font-bold text-[13px] mt-0.5 text-emerald-600">${safeLocale(tp1)}</div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className={`p-2.5 rounded-xl text-center ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'} ${isSelected ? '!bg-black/5 dark:!bg-white/10' : ''}`}>
            <div className={`text-[9px] uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>TP2</div>
            <div className="mono font-bold text-[11px]">${safeLocale(tp2)}</div>
          </div>
          <div className={`p-2.5 rounded-xl text-center ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'} ${isSelected ? '!bg-black/5 dark:!bg-white/10' : ''}`}>
            <div className={`text-[9px] uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>TP3</div>
            <div className="mono font-bold text-[11px]">${safeLocale(tp3)}</div>
          </div>
          <div className={`p-2.5 rounded-xl text-center ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'} ${isSelected ? '!bg-black/5 dark:!bg-white/10' : ''}`}>
            <div className={`text-[9px] uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>R:R</div>
            <div className="mono font-bold text-[11px]">1:{safeFixed(rr1,1)}</div>
          </div>
        </div>

        <div className={`flex items-center justify-between pt-3 border-t text-[11px] ${isDark ? 'border-white/5' : 'border-black/5'} ${isSelected ? '!border-black/10 dark:!border-white/10' : ''}`}>
          <span className={`flex items-center gap-1 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}><Clock size={11} />{call.timestamp ? new Date(call.timestamp).toLocaleTimeString() : ''}</span>
          <span className={`px-3 py-1 rounded-full font-bold text-[11px] ${isBuy ? 'bg-emerald-500 text-black' : isSell ? 'bg-red-500 text-white' : 'bg-zinc-200 text-zinc-700'}`}>{call.action} NOW</span>
        </div>
      </div>
    </div>
  )
}

export function TradingCallSummary({ summary }) {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'
  if (!summary) return null
  const cards = [
    { label: 'Total', value: summary.total ?? 0, sub: `${summary.buys ?? 0}B • ${summary.sells ?? 0}S` },
    { label: 'Buy', value: summary.buys ?? 0, sub: 'Long' },
    { label: 'Sell', value: summary.sells ?? 0, sub: 'Short' },
    { label: 'Avg Conf', value: `${Math.round(summary.avg_confidence || 0)}%`, sub: `${summary.high_confidence ?? 0} high` },
  ]
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {cards.map((c, i) => (
        <div key={i} className="ui-card p-4">
          <div className={`text-[10px] font-bold uppercase tracking-widest ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{c.label}</div>
          <div className="text-xl font-bold mono mt-1">{c.value}</div>
          <div className={`text-[11px] mt-0.5 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>{c.sub}</div>
        </div>
      ))}
    </div>
  )
}
