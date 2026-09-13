import { TrendingUp, TrendingDown, Minus, Target, Shield, Zap, Clock, DollarSign, BarChart3, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

export default function TradingCallCard({ call, onSelect, isSelected = false }) {
  if (!call) return null

  const isBuy = call.signal?.includes('BUY')
  const isSell = call.signal?.includes('SELL')
  const isHold = call.signal === 'HOLD'

  const config = {
    BUY: { 
      color: 'from-emerald-500 to-green-600', 
      bg: 'bg-emerald-500/10', 
      border: 'border-emerald-500/20', 
      text: 'text-emerald-400',
      lightBg: 'bg-emerald-500/5',
      icon: TrendingUp,
      actionColor: 'bg-emerald-500 text-black'
    },
    SELL: { 
      color: 'from-red-500 to-red-600', 
      bg: 'bg-red-500/10', 
      border: 'border-red-500/20', 
      text: 'text-red-400',
      lightBg: 'bg-red-500/5',
      icon: TrendingDown,
      actionColor: 'bg-red-500 text-white'
    },
    HOLD: { 
      color: 'from-gray-500 to-gray-600', 
      bg: 'bg-gray-500/10', 
      border: 'border-crypto-border', 
      text: 'text-gray-400',
      lightBg: 'bg-gray-500/5',
      icon: Minus,
      actionColor: 'bg-crypto-card text-crypto-muted'
    }
  }

  const style = isBuy ? config.BUY : isSell ? config.SELL : config.HOLD
  const Icon = style.icon

  const entry = call.entry_price || 0
  const sl = call.stop_loss || 0
  const tp1 = call.take_profits?.tp1 || 0
  const tp2 = call.take_profits?.tp2 || 0
  const tp3 = call.take_profits?.tp3 || 0
  const rr1 = call.risk_reward?.tp1 || 1
  const confidence = call.confidence || 0

  const riskPct = Math.abs(entry - sl) / entry * 100
  const rewardPct1 = Math.abs(tp1 - entry) / entry * 100

  return (
    <div 
      onClick={() => onSelect && onSelect(call)}
      className={`group relative rounded-2xl border backdrop-blur-xl overflow-hidden cursor-pointer transition-all duration-300 ${
        isSelected 
          ? `bg-white border-white shadow-xl shadow-white/10 scale-[1.02]` 
          : `${style.bg} ${style.border} hover:border-opacity-60 hover:shadow-xl hover:shadow-black/20 hover:-translate-y-1`
      }`}
    >
      <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${style.color}`}></div>
      
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${style.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
              <Icon size={20} className={isHold ? "text-white" : "text-black"} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className={`font-black text-lg tracking-tight ${isSelected ? 'text-black' : 'text-white'}`}>{call.symbol}</span>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-black tracking-widest border ${isSelected ? 'bg-black text-white border-black' : `${style.bg} ${style.text} ${style.border}`}`}>
                  {call.signal}
                </span>
              </div>
              <div className={`text-xs font-medium mt-1 flex items-center gap-2 ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>
                <Zap size={10} />
                {call.action} • {call.timeframe} • {confidence.toFixed(0)}% conf
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className={`text-[10px] font-bold tracking-widest uppercase ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>Risk</div>
            <div className={`px-2.5 py-1 rounded-full text-xs font-black mt-1 border ${
              call.risk_level === 'LOW' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
              call.risk_level === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
              'bg-red-500/10 text-red-400 border-red-500/20'
            }`}>
              {call.risk_level}
            </div>
          </div>
        </div>

        {/* Price Levels */}
        <div className="space-y-3 mb-4">
          <div className="grid grid-cols-3 gap-2">
            <div className={`p-3 rounded-xl border ${isSelected ? 'bg-black/5 border-black/10' : 'bg-crypto-bg/50 border-crypto-border/30'}`}>
              <div className={`text-[10px] font-bold tracking-widest uppercase ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>Entry</div>
              <div className={`mono font-black text-sm mt-1 ${isSelected ? 'text-black' : 'text-white'}`}>${entry.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
              <div className={`text-[11px] mt-1 ${isSelected ? 'text-black/50' : 'text-crypto-muted'}`}>Current</div>
            </div>
            <div className={`p-3 rounded-xl border ${isSelected ? 'bg-red-500/10 border-red-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
              <div className="text-[10px] font-bold tracking-widest uppercase text-red-400">Stop Loss</div>
              <div className="mono font-black text-sm mt-1 text-red-400">${sl.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
              <div className="text-[11px] mt-1 text-red-400/70">-{riskPct.toFixed(2)}%</div>
            </div>
            <div className={`p-3 rounded-xl border ${isSelected ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-emerald-500/5 border-emerald-500/20'}`}>
              <div className="text-[10px] font-bold tracking-widest uppercase text-emerald-400">TP1 (1:1)</div>
              <div className="mono font-black text-sm mt-1 text-emerald-400">${tp1.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
              <div className="text-[11px] mt-1 text-emerald-400/70">+{rewardPct1.toFixed(2)}%</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div className={`p-2.5 rounded-xl border ${isSelected ? 'bg-black/5 border-black/10' : 'bg-crypto-bg/30 border-crypto-border/20'}`}>
              <div className={`text-[10px] uppercase ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>TP2 (1:2)</div>
              <div className={`mono font-bold text-xs mt-1 ${isSelected ? 'text-black' : 'text-white'}`}>${tp2.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            </div>
            <div className={`p-2.5 rounded-xl border ${isSelected ? 'bg-black/5 border-black/10' : 'bg-crypto-bg/30 border-crypto-border/20'}`}>
              <div className={`text-[10px] uppercase ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>TP3 (1:3)</div>
              <div className={`mono font-bold text-xs mt-1 ${isSelected ? 'text-black' : 'text-white'}`}>${tp3.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
            </div>
            <div className={`p-2.5 rounded-xl border ${isSelected ? 'bg-black/5 border-black/10' : 'bg-crypto-bg/30 border-crypto-border/20'}`}>
              <div className={`text-[10px] uppercase ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>R:R</div>
              <div className={`mono font-bold text-xs mt-1 ${isSelected ? 'text-black' : 'text-white'}`}>1:{rr1.toFixed(1)}</div>
            </div>
          </div>
        </div>

        {/* Position Info */}
        <div className={`grid grid-cols-3 gap-2 p-3 rounded-xl border mb-4 ${isSelected ? 'bg-black/5 border-black/10' : 'bg-crypto-bg/30 border-crypto-border/20'}`}>
          <div className="text-center">
            <div className={`text-[10px] uppercase ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>Size</div>
            <div className={`font-bold text-xs mt-1 ${isSelected ? 'text-black' : 'text-white'}`}>{call.position?.size?.toFixed(4) || '—'} {call.symbol.split('-')[0]}</div>
          </div>
          <div className="text-center">
            <div className={`text-[10px] uppercase ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>Risk</div>
            <div className={`font-bold text-xs mt-1 ${isSelected ? 'text-black' : 'text-white'}`}>${call.position?.risk_amount?.toFixed(0) || '—'}</div>
          </div>
          <div className="text-center">
            <div className={`text-[10px] uppercase ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>Leverage</div>
            <div className={`font-bold text-xs mt-1 ${isSelected ? 'text-black' : 'text-white'}`}>{call.leverage?.split(' ')[0] || '—'}</div>
          </div>
        </div>

        {/* Indicators */}
        <div className="flex items-center gap-2 mb-3">
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-medium border ${isSelected ? 'bg-black/5 border-black/10 text-black/70' : 'bg-crypto-bg/50 border-crypto-border/30 text-crypto-muted'}`}>
            <BarChart3 size={10} />
            RSI {call.indicators?.RSI?.toFixed(0) || '—'}
          </div>
          <div className={`px-2 py-1 rounded-full text-[11px] font-medium border ${isSelected ? 'bg-black/5 border-black/10 text-black/70' : 'bg-crypto-bg/50 border-crypto-border/30 text-crypto-muted'}`}>
            Vol {((call.indicators?.volatility || 0) * 100).toFixed(1)}%
          </div>
          <div className={`px-2 py-1 rounded-full text-[11px] font-bold border ${call.sentiment?.average_compound > 0 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : call.sentiment?.average_compound < 0 ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-gray-500/10 text-gray-400 border-gray-500/20'}`}>
            Sent {(call.sentiment?.average_compound || 0).toFixed(2)}
          </div>
        </div>

        {/* Reasoning */}
        <div className={`p-3 rounded-xl border ${isSelected ? 'bg-black/5 border-black/10' : 'bg-crypto-bg/20 border-crypto-border/20'}`}>
          <div className={`text-[10px] font-bold tracking-widest uppercase mb-1 ${isSelected ? 'text-black/60' : 'text-crypto-muted'}`}>AI Reasoning</div>
          <div className={`text-xs leading-relaxed line-clamp-2 ${isSelected ? 'text-black/70' : 'text-white/60'}`}>
            {call.reasoning || 'Ensemble analysis'}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-crypto-border/20">
          <div className={`flex items-center gap-2 text-[11px] ${isSelected ? 'text-black/50' : 'text-crypto-muted'}`}>
            <Clock size={10} />
            {new Date(call.timestamp).toLocaleTimeString()} • Exp {new Date(call.expiry).toLocaleDateString()}
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-black ${style.actionColor}`}>
            {call.action} NOW
          </div>
        </div>
      </div>
    </div>
  )
}

export function TradingCallSummary({ summary }) {
  if (!summary) return null

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="p-4 rounded-2xl bg-gradient-to-br from-crypto-card to-crypto-bg border border-crypto-border/50">
        <div className="flex items-center gap-2 mb-2">
          <Target size={14} className="text-crypto-accent" />
          <span className="text-xs font-bold tracking-widest text-crypto-muted uppercase">Total Calls</span>
        </div>
        <div className="text-2xl font-black text-white mono">{summary.total}</div>
        <div className="text-xs text-crypto-muted mt-1">{summary.buys} buys • {summary.sells} sells</div>
      </div>
      
      <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-crypto-card border border-emerald-500/20">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle size={14} className="text-emerald-400" />
          <span className="text-xs font-bold tracking-widest text-emerald-400 uppercase">Buy Signals</span>
        </div>
        <div className="text-2xl font-black text-emerald-400 mono">{summary.buys}</div>
        <div className="text-xs text-emerald-400/70 mt-1">Long opportunities</div>
      </div>
      
      <div className="p-4 rounded-2xl bg-gradient-to-br from-red-500/10 to-crypto-card border border-red-500/20">
        <div className="flex items-center gap-2 mb-2">
          <XCircle size={14} className="text-red-400" />
          <span className="text-xs font-bold tracking-widest text-red-400 uppercase">Sell Signals</span>
        </div>
        <div className="text-2xl font-black text-red-400 mono">{summary.sells}</div>
        <div className="text-xs text-red-400/70 mt-1">Short opportunities</div>
      </div>
      
      <div className="p-4 rounded-2xl bg-gradient-to-br from-crypto-accent2/10 to-crypto-card border border-crypto-accent2/20">
        <div className="flex items-center gap-2 mb-2">
          <Zap size={14} className="text-crypto-accent2" />
          <span className="text-xs font-bold tracking-widest text-crypto-accent2 uppercase">Avg Confidence</span>
        </div>
        <div className="text-2xl font-black text-crypto-accent2 mono">{summary.avg_confidence?.toFixed(0)}%</div>
        <div className="text-xs text-crypto-accent2/70 mt-1">{summary.high_confidence} high conf (&gt;80%)</div>
      </div>
    </div>
  )
}
