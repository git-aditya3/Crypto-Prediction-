import { TrendingUp, TrendingDown, Minus, Target, Shield, Zap, Clock, DollarSign, BarChart3, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { useSettingsStore } from '../store/useSettingsStore'

const safeFixed = (v, d=2) => {
  const n = typeof v === 'number' ? v : parseFloat(v)
  if (isNaN(n)) return '0.00'
  return n.toFixed(d)
}
const safeLocale = (v) => {
  const n = typeof v === 'number' ? v : parseFloat(v)
  if (isNaN(n)) return '0.00'
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

export default function TradingCallCard({ call, onSelect, isSelected = false }) {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'
  
  if (!call) return null

  const isBuy = call.signal?.includes('BUY')
  const isSell = call.signal?.includes('SELL')
  const isHold = call.signal === 'HOLD'

  const style = isBuy 
    ? { color: 'from-emerald-500 to-green-600', bg: 'bg-emerald-500/5', border: 'border-emerald-500/10', text: 'text-emerald-500', icon: TrendingUp, action: 'bg-emerald-500 text-black' }
    : isSell 
      ? { color: 'from-red-500 to-red-600', bg: 'bg-red-500/5', border: 'border-red-500/10', text: 'text-red-500', icon: TrendingDown, action: 'bg-red-500 text-white' }
      : { color: 'from-gray-500 to-gray-600', bg: 'bg-gray-500/5', border: 'border-white/5', text: 'text-gray-400', icon: Minus, action: 'bg-white/10 text-white/60' }
  
  const Icon = style.icon
  const entry = call.entry_price ?? 0
  const sl = call.stop_loss ?? 0
  const tp1 = call.take_profits?.tp1 ?? 0
  const tp2 = call.take_profits?.tp2 ?? 0
  const tp3 = call.take_profits?.tp3 ?? 0
  const rr1 = call.risk_reward?.tp1 ?? (typeof call.risk_reward === 'number' ? call.risk_reward : 1)
  const confidence = call.confidence ?? 0
  const riskPct = entry ? Math.abs(entry - sl) / entry * 100 : 0
  const rewardPct1 = entry ? Math.abs(tp1 - entry) / entry * 100 : 0

  return (
    <div 
      onClick={() => onSelect && onSelect(call)}
      className={`group relative rounded-[32px] backdrop-blur-xl overflow-hidden cursor-pointer transition-all duration-500 font-poppins clay-card ${
        isSelected 
          ? isDark
            ? 'bg-white !text-black shadow-[0px_20px_40px_rgba(0,0,0,0.5),inset_6px_6px_12px_rgba(255,255,255,0.9),inset_-6px_-6px_12px_rgba(0,0,0,0.1)] scale-[1.02] border-white'
            : 'bg-white !text-black shadow-[0px_20px_40px_rgba(31,38,135,0.1),inset_6px_6px_12px_rgba(255,255,255,0.9),inset_-6px_-6px_12px_rgba(0,0,0,0.1)] scale-[1.02] border-white'
          : 'hover:scale-[1.01] hover:-translate-y-1'
      }`}
      style={!isSelected ? (isDark ? {
        background: 'rgba(28,28,30,0.7)',
        border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0px 20px 40px rgba(0,0,0,0.6), inset 4px 4px 8px rgba(255,255,255,0.12), inset -4px -4px 8px rgba(0,0,0,0.5)'
      } : {
        background: '#ffffff',
        border: '1px solid rgba(255,255,255,0.4)',
        boxShadow: '0px 20px 40px rgba(31,38,135,0.08), inset 6px 6px 12px rgba(255,255,255,0.9), inset -6px -6px 12px rgba(0,0,0,0.1)'
      }) : {}}
    >
      {/* Top accent line - clay style */}
      <div className={`absolute top-0 left-6 right-6 h-1.5 rounded-full bg-gradient-to-r ${style.color} opacity-80`}
        style={{ boxShadow: '0px 2px 8px rgba(0,0,0,0.2)' }}></div>
      
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-center gap-4">
            <div className={`w-14 h-14 rounded-[20px] bg-gradient-to-br ${style.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300`}
              style={isDark ? {
                boxShadow: '0px 8px 16px rgba(0,0,0,0.4), inset 2px 2px 4px rgba(255,255,255,0.2), inset -2px -2px 4px rgba(0,0,0,0.2)',
                border: '1px solid rgba(255,255,255,0.08)'
              } : {
                boxShadow: '0px 8px 16px rgba(31,38,135,0.1), inset 3px 3px 6px rgba(255,255,255,0.5), inset -3px -3px 6px rgba(0,0,0,0.1)',
                border: '1px solid rgba(255,255,255,0.4)'
              }}>
              <Icon size={22} className={isHold ? "text-white" : "text-black"} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className={`font-black text-xl tracking-tight font-poppins ${isSelected ? 'text-black' : isDark ? 'text-[#F3F4F6]' : 'text-[#1e293b]'}`}>{call.symbol || 'Unknown'}</span>
                <span className={`px-3 py-1 rounded-full text-[10px] font-black tracking-widest clay-pill font-poppins ${
                  isSelected ? 'bg-black text-white border-black' : `${style.bg} ${style.text} border ${style.border}`
                }`}>
                  {call.signal || 'HOLD'}
                </span>
              </div>
              <div className={`text-xs font-semibold mt-1 flex items-center gap-2 font-poppins ${isSelected ? 'text-black/60' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>
                <Zap size={12} />
                {call.action || 'WAIT'} • {call.timeframe || '1d'} • {safeFixed(confidence,0)}% conf • Clay 3D
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className={`text-[10px] font-bold tracking-widest uppercase font-poppins ${isSelected ? 'text-black/60' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>Risk</div>
            <div className={`clay-pill px-3 py-1.5 rounded-full text-xs font-black mt-1 font-poppins ${
              call.risk_level === 'LOW' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' :
              call.risk_level === 'MEDIUM' ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20' :
              'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20'
            }`}>
              {call.risk_level || 'MEDIUM'}
            </div>
          </div>
        </div>

        {/* Price Levels - Clay Cards */}
        <div className="space-y-3 mb-5">
          <div className="grid grid-cols-3 gap-3">
            <div className={`p-4 rounded-[20px] transition-all duration-300`}
              style={isDark ? {
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid rgba(255,255,255,0.06)',
                boxShadow: 'inset 3px 3px 6px rgba(0,0,0,0.4), inset -3px -3px 6px rgba(255,255,255,0.03)'
              } : {
                background: '#f8fafc',
                border: '1px solid rgba(255,255,255,0.4)',
                boxShadow: 'inset 3px 3px 6px rgba(0,0,0,0.03), inset -3px -3px 6px rgba(255,255,255,0.9)'
              }}>
              <div className={`text-[10px] font-bold tracking-widest uppercase font-poppins ${isSelected ? 'text-black/60' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>Entry • Clay</div>
              <div className={`mono font-black text-sm mt-1 ${isSelected ? 'text-black' : isDark ? 'text-[#F3F4F6]' : 'text-[#1e293b]'}`}>${safeLocale(entry)}</div>
              <div className={`text-[11px] mt-1 font-poppins ${isSelected ? 'text-black/50' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>Live Binance</div>
            </div>
            <div className="p-4 rounded-[20px] bg-red-500/5 border border-red-500/10"
              style={isDark ? {
                boxShadow: 'inset 2px 2px 4px rgba(0,0,0,0.2), inset -2px -2px 4px rgba(255,255,255,0.02)'
              } : {}}>
              <div className="text-[10px] font-bold tracking-widest uppercase text-red-500 font-poppins">Stop Loss • Clay</div>
              <div className="mono font-black text-sm mt-1 text-red-500">${safeLocale(sl)}</div>
              <div className="text-[11px] mt-1 text-red-500/70 font-poppins">-{safeFixed(riskPct,2)}% • Real</div>
            </div>
            <div className="p-4 rounded-[20px] bg-emerald-500/5 border border-emerald-500/10">
              <div className="text-[10px] font-bold tracking-widest uppercase text-emerald-500 font-poppins">TP1 • Clay 1:1</div>
              <div className="mono font-black text-sm mt-1 text-emerald-500">${safeLocale(tp1)}</div>
              <div className="text-[11px] mt-1 text-emerald-500/70 font-poppins">+{safeFixed(rewardPct1,2)}% • Real</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'TP2 (1:2)', value: tp2 },
              { label: 'TP3 (1:3)', value: tp3 },
              { label: 'R:R • Clay', value: `1:${safeFixed(rr1,1)}`, isText: true }
            ].map((item, idx) => (
              <div key={idx} className="p-3 rounded-[16px] transition-all"
                style={isDark ? {
                  background: 'rgba(0,0,0,0.2)',
                  border: '1px solid rgba(255,255,255,0.04)',
                  boxShadow: 'inset 2px 2px 4px rgba(0,0,0,0.3), inset -2px -2px 4px rgba(255,255,255,0.02)'
                } : {
                  background: '#ffffff',
                  border: '1px solid rgba(255,255,255,0.4)',
                  boxShadow: '0px 4px 12px rgba(31,38,135,0.04), inset 2px 2px 4px rgba(255,255,255,0.9)'
                }}>
                <div className={`text-[10px] uppercase font-poppins font-bold ${isSelected ? 'text-black/60' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>{item.label}</div>
                <div className={`mono font-bold text-xs mt-1 ${isSelected ? 'text-black' : isDark ? 'text-[#F3F4F6]' : 'text-[#1e293b]'}`}>{item.isText ? item.value : `$${safeLocale(item.value)}`}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Position Info - Clay */}
        <div className="grid grid-cols-3 gap-3 p-4 rounded-[20px] mb-5"
          style={isDark ? {
            background: 'rgba(0,0,0,0.25)',
            border: '1px solid rgba(255,255,255,0.05)',
            boxShadow: 'inset 3px 3px 6px rgba(0,0,0,0.4), inset -3px -3px 6px rgba(255,255,255,0.02)'
          } : {
            background: '#f8fafc',
            border: '1px solid rgba(255,255,255,0.4)',
            boxShadow: 'inset 2px 2px 4px rgba(0,0,0,0.02), inset -2px -2px 4px rgba(255,255,255,0.9)'
          }}>
          {[
            { label: 'Size • Clay', value: call.position?.size != null ? `${safeFixed(call.position.size,4)} ${call.symbol?.split('-')[0] || ''}` : '—' },
            { label: 'Risk • Real', value: call.position?.risk_amount != null ? `$${safeFixed(call.position.risk_amount,0)}` : '—' },
            { label: 'Leverage • 3D', value: call.leverage?.split(' ')[0] || call.position?.leverage_suggestion || '—' }
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <div className={`text-[10px] uppercase font-poppins font-bold ${isSelected ? 'text-black/60' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>{stat.label}</div>
              <div className={`font-bold text-xs mt-1 font-poppins ${isSelected ? 'text-black' : isDark ? 'text-[#F3F4F6]' : 'text-[#1e293b]'}`}>{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Indicators - Clay Pills */}
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          {[
            { label: `RSI ${call.indicators?.RSI != null ? safeFixed(call.indicators.RSI,0) : '—'}`, icon: BarChart3 },
            { label: `Vol ${safeFixed((call.indicators?.volatility ?? 0) * 100,1)}%` },
            { label: `Sent ${safeFixed(call.sentiment?.average_compound,2)}`, sentiment: true }
          ].map((pill, i) => (
            <div key={i} className={`clay-pill flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-bold font-poppins ${
              pill.sentiment
                ? (call.sentiment?.average_compound ?? 0) > 0 ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' : (call.sentiment?.average_compound ?? 0) < 0 ? 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20' : 'bg-gray-500/10 text-gray-500 border-gray-500/20'
                : isDark ? 'bg-black/30 text-[#9CA3AF] border-white/5' : 'bg-white text-[#64748b] border-white/40'
            }`}>
              {pill.icon && <pill.icon size={12} />}
              {pill.label}
            </div>
          ))}
        </div>

        {/* Reasoning - Clay Inset */}
        <div className="p-4 rounded-[20px] mb-5"
          style={isDark ? {
            background: 'rgba(0,0,0,0.2)',
            border: '1px solid rgba(255,255,255,0.04)',
            boxShadow: 'inset 3px 3px 6px rgba(0,0,0,0.4), inset -3px -3px 6px rgba(255,255,255,0.02)'
          } : {
            background: '#ffffff',
            border: '1px solid rgba(255,255,255,0.4)',
            boxShadow: 'inset 2px 2px 4px rgba(0,0,0,0.03), inset -2px -2px 4px rgba(255,255,255,0.9)'
          }}>
          <div className={`text-[10px] font-bold tracking-widest uppercase mb-2 font-poppins ${isSelected ? 'text-black/60' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>AI Reasoning • Claymorphism • Real Data</div>
          <div className={`text-xs leading-relaxed line-clamp-2 font-poppins ${isSelected ? 'text-black/70' : isDark ? 'text-[#E5E7EB]/70' : 'text-[#475569]'}`}>
            {call.reasoning || 'Ensemble analysis • Claymorphic 3D • Real Binance'}
          </div>
        </div>

        {/* Footer - Flat */}
        <div className={`flex items-center justify-between pt-4 border-t ${isDark ? 'border-white/5' : 'border-black/5'}`}>
          <div className={`flex items-center gap-2 text-[11px] font-poppins ${isSelected ? 'text-black/50' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>
            <Clock size={12} />
            {call.timestamp ? new Date(call.timestamp).toLocaleTimeString() : ''} • Clay • {call.expiry ? new Date(call.expiry).toLocaleDateString() : ''}
          </div>
          <div className={`clay-pill px-4 py-1.5 rounded-full text-xs font-black font-poppins ${style.action} shadow-lg`}>
            {call.action || 'HOLD'} NOW • Clay
          </div>
        </div>
      </div>
    </div>
  )
}

export function TradingCallSummary({ summary }) {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'
  
  if (!summary) return null
  const safeFixedInner = (v, d=0) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return '0'
    return n.toFixed(d)
  }

  const cards = [
    { label: 'Total Calls • Clay', value: summary.total ?? 0, sub: `${summary.buys ?? 0} buys • ${summary.sells ?? 0} sells`, icon: Target, color: 'from-violet-500 to-purple-600' },
    { label: 'Buy Signals • 3D', value: summary.buys ?? 0, sub: 'Long opportunities • Clay', icon: CheckCircle, color: 'from-emerald-500 to-green-600' },
    { label: 'Sell Signals • Puffy', value: summary.sells ?? 0, sub: 'Short opportunities • Real', icon: XCircle, color: 'from-red-500 to-red-600' },
    { label: 'Avg Confidence • Clay', value: `${safeFixedInner(summary.avg_confidence,0)}%`, sub: `${summary.high_confidence ?? 0} high conf (>80%) • 3D`, icon: Shield, color: 'from-blue-500 to-indigo-600' },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((card, i) => (
        <div key={i} className="clay-card p-5 font-poppins"
          style={isDark ? {
            background: 'rgba(28,28,30,0.7)',
            border: '1px solid rgba(255,255,255,0.08)',
            boxShadow: '0px 20px 40px rgba(0,0,0,0.6), inset 4px 4px 8px rgba(255,255,255,0.12), inset -4px -4px 8px rgba(0,0,0,0.5)'
          } : {
            background: '#ffffff',
            border: '1px solid rgba(255,255,255,0.4)',
            boxShadow: '0px 20px 40px rgba(31,38,135,0.08), inset 6px 6px 12px rgba(255,255,255,0.9), inset -6px -6px 12px rgba(0,0,0,0.1)'
          }}>
          <div className="flex items-center gap-2 mb-3">
            <div className={`w-8 h-8 rounded-[12px] bg-gradient-to-br ${card.color} flex items-center justify-center shadow-lg`}>
              <card.icon size={14} className="text-white" />
            </div>
            <span className="text-[10px] font-bold tracking-widest uppercase font-poppins"
              style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>{card.label}</span>
          </div>
          <div className="text-2xl font-black mono" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>{card.value}</div>
          <div className="text-xs mt-1 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>{card.sub}</div>
        </div>
      ))}
    </div>
  )
}
