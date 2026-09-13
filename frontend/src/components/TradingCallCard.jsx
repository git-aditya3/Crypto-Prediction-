import { TrendingUp, TrendingDown, Minus, Target, Shield, Zap, Clock, Award, BarChart3, TrendingUp as TrendIcon } from 'lucide-react'
import { useSettingsStore } from '../store/useSettingsStore'

const safeFixed = (v, d=2) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toFixed(d) }
const safeLocale = (v) => { const n = typeof v === 'number' ? v : parseFloat(v); return isNaN(n) ? '0.00' : n.toLocaleString(undefined, { maximumFractionDigits: 2 }) }

export default function TradingCallCard({ call, onSelect, isSelected = false }) {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
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
  const isHighConf = confidence >= 80
  const isReal = call.real_trading || entry > 0

  return (
    <div
      onClick={() => onSelect && onSelect(call)}
      className={`group relative rounded-[20px] overflow-hidden cursor-pointer transition-all duration-300 border hover:scale-[1.02] hover:shadow-xl ${
        isSelected 
          ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)] shadow-xl shadow-[var(--accent)]/20 scale-[1.02] ring-2 ring-[var(--accent)]/30' 
          : 'ui-card hover:border-[var(--accent)]/30 hover:shadow-[var(--glow)]'
      }`}
    >
      {/* Top accent bar with gradient */}
      <div className={`h-1 w-full relative overflow-hidden ${isBuy ? 'bg-gradient-to-r from-emerald-400 to-emerald-600' : isSell ? 'bg-gradient-to-r from-red-400 to-red-600' : 'bg-gradient-to-r from-zinc-400 to-zinc-600'}`}>
        <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent animate-pulse" />
      </div>
      
      {/* Glow effect for high confidence */}
      {isHighConf && !isSelected && (
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      )}

      <div className="p-5 relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center shadow-lg transition-all group-hover:scale-110 group-hover:rotate-3 relative overflow-hidden ${
              isSelected 
                ? 'bg-black/20 text-white' 
                : isBuy ? 'bg-gradient-to-br from-emerald-400 to-emerald-600 text-black shadow-emerald-500/20' 
                : isSell ? 'bg-gradient-to-br from-red-400 to-red-600 text-white shadow-red-500/20' 
                : 'bg-[var(--accent-soft)] text-[var(--text)] border border-[var(--border)]'
            }`}>
              <Icon size={18} />
              {isSelected && <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`font-black text-[16px] tracking-tight ${isSelected ? 'text-white' : isLight ? 'text-black' : 'text-white'} group-hover:tracking-wide transition-all`}>{call.symbol}</span>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-black tracking-wide border transition-all group-hover:scale-105 ${
                  isBuy ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 group-hover:bg-emerald-500 group-hover:text-black' 
                  : isSell ? 'bg-red-500/10 text-red-500 border-red-500/20 group-hover:bg-red-500 group-hover:text-white' 
                  : 'bg-[var(--accent-soft)] text-[var(--text-sec)] border-[var(--border)]'
                }`}>
                  {call.signal}
                </span>
                {isHighConf && <span className="px-2 py-0.5 rounded-full bg-amber-500 text-black text-[9px] font-black animate-pulse">HIGH CONF</span>}
              </div>
              <div className={`text-[11px] mt-1 flex items-center gap-2 ${isSelected ? 'text-white/70' : isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>
                <span className="flex items-center gap-1"><Zap size={10} className={isBuy ? 'text-emerald-500' : isSell ? 'text-red-500' : 'text-[var(--accent)]'} /> {call.action}</span>
                <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
                <span className={`px-1.5 py-0.5 rounded-full font-bold ${confidence >= 80 ? 'bg-emerald-500/20 text-emerald-500' : confidence >= 60 ? 'bg-amber-500/20 text-amber-500' : 'bg-zinc-500/20 text-zinc-500'}`}>{safeFixed(confidence,0)}%</span>
                <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
                <span>{call.timeframe || '1d'}</span>
                {isReal && <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />}
              </div>
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <div className={`px-2.5 py-1 rounded-full text-[10px] font-black tracking-wide border ${
              call.risk_level === 'LOW' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' 
              : call.risk_level === 'HIGH' ? 'bg-red-500/10 text-red-500 border-red-500/20' 
              : 'bg-[var(--accent-soft)] text-[var(--text-sec)] border-[var(--border)]'
            }`}>
              {call.risk_level || 'MEDIUM'}
            </div>
            {isReal && <span className="text-[9px] px-2 py-0.5 rounded-full bg-emerald-500 text-black font-black">REAL</span>}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2.5 mb-3">
          <div className={`p-3 rounded-xl border transition-all group-hover:scale-[1.02] group-hover:shadow-md relative overflow-hidden ${isLight ? 'bg-zinc-50 border-black/5 group-hover:bg-white group-hover:border-black/10' : 'bg-black/40 border-white/5 group-hover:bg-black/60 group-hover:border-[var(--accent)]/20'} ${isSelected ? '!bg-black/10 !border-black/10' : ''}`}>
            <div className={`text-[9px] font-bold uppercase tracking-wide flex items-center gap-1 ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>
              <Target size={10} /> Entry
            </div>
            <div className="mono font-black text-[13px] mt-1 tracking-tight">${safeLocale(entry)}</div>
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--accent)]/30 scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
          </div>
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 group-hover:bg-red-500/15 group-hover:border-red-500/30 transition-all group-hover:scale-[1.02] relative overflow-hidden">
            <div className="text-[9px] font-bold uppercase tracking-wide text-red-500 flex items-center gap-1">
              <Shield size={10} /> SL
            </div>
            <div className="mono font-black text-[13px] mt-1 text-red-500">${safeLocale(sl)}</div>
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-red-500/50 scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
          </div>
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 group-hover:bg-emerald-500/15 group-hover:border-emerald-500/30 transition-all group-hover:scale-[1.02] relative overflow-hidden">
            <div className="text-[9px] font-bold uppercase tracking-wide text-emerald-600 flex items-center gap-1">
              <Award size={10} /> TP1
            </div>
            <div className="mono font-black text-[13px] mt-1 text-emerald-600">${safeLocale(tp1)}</div>
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500/50 scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-4">
          {[
            { label: 'TP2', value: tp2, icon: BarChart3 },
            { label: 'TP3', value: tp3, icon: TrendIcon },
            { label: 'R:R', value: `1:${safeFixed(rr1,1)}`, icon: Target, isRatio: true },
          ].map((item, i) => (
            <div key={i} className={`p-2.5 rounded-xl text-center border transition-all hover:scale-105 hover:shadow-md group/item ${isLight ? 'bg-white border-black/5 hover:border-black/10 hover:bg-zinc-50' : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-[var(--accent)]/20'} ${isSelected ? '!bg-black/5 !border-black/10' : ''}`}>
              <div className={`text-[9px] uppercase tracking-wide flex items-center justify-center gap-1 ${isLight ? 'text-zinc-500' : 'text-zinc-400'} group-hover/item:text-[var(--accent)] transition-colors`}>
                <item.icon size={10} /> {item.label}
              </div>
              <div className={`mono font-bold text-[11px] mt-1 ${item.isRatio ? 'text-[var(--accent)]' : ''}`}>{item.isRatio ? item.value : `$${safeLocale(item.value)}`}</div>
            </div>
          ))}
        </div>

        <div className={`flex items-center justify-between pt-3 border-t ${isLight ? 'border-black/5' : 'border-white/5'} ${isSelected ? '!border-black/10' : ''}`}>
          <span className={`flex items-center gap-1.5 text-[11px] font-medium ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>
            <Clock size={12} className="text-[var(--accent)]" />
            {call.timestamp ? new Date(call.timestamp).toLocaleTimeString() : 'Just now'}
            {call.model_used && (
              <>
                <span className="w-1 h-1 rounded-full bg-[var(--border)]" />
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--accent-soft)] border border-[var(--border)]">{call.model_used.split(' ')[0]}</span>
              </>
            )}
          </span>
          <span className={`px-3.5 py-1.5 rounded-full font-black text-[11px] tracking-wide shadow-md transition-all group-hover:scale-105 group-hover:shadow-lg flex items-center gap-1.5 ${isBuy ? 'bg-gradient-to-r from-emerald-400 to-emerald-600 text-black shadow-emerald-500/20' : isSell ? 'bg-gradient-to-r from-red-400 to-red-600 text-white shadow-red-500/20' : 'bg-[var(--accent)] text-[var(--bg)]'}`}>
            <Zap size={12} />
            {call.action} NOW
          </span>
        </div>

        {/* Confidence bar */}
        <div className="mt-3 h-1 w-full bg-[var(--accent-soft)] rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all duration-1000 ${isBuy ? 'bg-gradient-to-r from-emerald-400 to-emerald-600' : isSell ? 'bg-gradient-to-r from-red-400 to-red-600' : 'bg-[var(--accent)]'}`}
            style={{ width: `${Math.min(100, Math.max(5, confidence))}%` }}
          />
        </div>
      </div>
    </div>
  )
}

export function TradingCallSummary({ summary }) {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  if (!summary) return null
  
  const cards = [
    { label: 'Total Calls', value: summary.total ?? 0, sub: `${summary.buys ?? 0}B • ${summary.sells ?? 0}S • ${summary.holds ?? 0}H`, icon: Target, accent: true },
    { label: 'Buy Signals', value: summary.buys ?? 0, sub: 'Long opportunities', icon: TrendingUp, color: 'emerald' },
    { label: 'Sell Signals', value: summary.sells ?? 0, sub: 'Short opportunities', icon: TrendingDown, color: 'red' },
    { label: 'Avg Confidence', value: `${Math.round(summary.avg_confidence || 0)}%`, sub: `${summary.high_confidence ?? 0} high conf`, icon: Award, color: 'amber' },
  ]
  
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((c, i) => (
        <div key={i} className={`group p-4 rounded-xl border transition-all hover:scale-105 hover:shadow-lg relative overflow-hidden ${isLight ? 'bg-white border-black/5 hover:border-black/10 hover:shadow-md' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--accent)]/30 hover:shadow-[var(--glow)]'} ${c.accent ? 'ring-1 ring-[var(--accent)]/20' : ''}`}>
          <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-2">
              <div className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-full ${isLight ? 'bg-black/5 text-zinc-600' : 'bg-white/5 text-zinc-400'} group-hover:bg-[var(--accent-soft)] transition-colors`}>{c.label}</div>
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all group-hover:scale-110 group-hover:rotate-3 ${c.color === 'emerald' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : c.color === 'red' ? 'bg-red-500/10 text-red-500 border border-red-500/20' : c.color === 'amber' ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20' : isLight ? 'bg-black text-white' : 'bg-white text-black'}`}>
                <c.icon size={14} />
              </div>
            </div>
            <div className={`text-2xl font-black mono tracking-tight ${isLight ? 'text-black' : 'text-white'} group-hover:tracking-wide transition-all`}>{c.value}</div>
            <div className={`text-[11px] mt-1 font-medium ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>{c.sub}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
