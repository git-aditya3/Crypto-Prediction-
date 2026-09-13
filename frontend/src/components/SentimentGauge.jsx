import { Sparkles, TrendingUp, MessageCircle, Users, Newspaper } from 'lucide-react'

export default function SentimentGauge({ sentiment, symbol }) {
  const avg = sentiment?.average_compound || 0
  const daily = sentiment?.daily || []
  
  // Convert -1 to 1 to 0-100
  const score = ((avg + 1) / 2) * 100
  const isPositive = avg > 0.1
  const isNegative = avg < -0.1
  
  let label = 'Neutral'
  let color = 'from-gray-500 to-gray-600'
  let bg = 'bg-gray-500/10'
  let textColor = 'text-gray-400'
  
  if (avg > 0.5) {
    label = 'Very Bullish'
    color = 'from-emerald-400 to-crypto-bull'
    bg = 'bg-crypto-bull/10'
    textColor = 'text-crypto-bull'
  } else if (avg > 0.1) {
    label = 'Bullish'
    color = 'from-emerald-500 to-crypto-bull'
    bg = 'bg-crypto-bull/10'
    textColor = 'text-crypto-bull'
  } else if (avg < -0.5) {
    label = 'Very Bearish'
    color = 'from-red-500 to-crypto-bear'
    bg = 'bg-crypto-bear/10'
    textColor = 'text-crypto-bear'
  } else if (avg < -0.1) {
    label = 'Bearish'
    color = 'from-red-400 to-crypto-bear'
    bg = 'bg-crypto-bear/10'
    textColor = 'text-crypto-bear'
  }

  const totalMentions = daily.reduce((sum, d) => sum + (d.count || 0), 0)

  return (
    <div className="rounded-2xl border border-crypto-border/50 bg-crypto-card/30 backdrop-blur-xl overflow-hidden">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg">
              <Sparkles size={18} className="text-white" />
            </div>
            <div>
              <div className="font-semibold text-white">Market Sentiment</div>
              <div className="text-xs text-crypto-muted">{symbol} • {daily.length} days • {totalMentions} mentions</div>
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-xs font-bold border ${bg} ${textColor} border-current/20`}>
            {label}
          </div>
        </div>

        {/* Gauge */}
        <div className="relative">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-crypto-muted">Bearish</span>
            <span className="text-xs font-medium text-crypto-muted">Bullish</span>
          </div>
          
          <div className="relative h-3 bg-crypto-bg rounded-full overflow-hidden border border-crypto-border/30">
            <div className="absolute inset-0 bg-gradient-to-r from-crypto-bear via-gray-500 to-crypto-bull opacity-30"></div>
            <div 
              className={`absolute top-0 bottom-0 w-1 bg-white shadow-lg shadow-white/50 rounded-full transition-all duration-1000 ease-out`}
              style={{ left: `${score}%`, transform: 'translateX(-50%)' }}
            >
              <div className="absolute -top-1 -bottom-1 left-1/2 -translate-x-1/2 w-1 bg-white rounded-full"></div>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg border-2 border-crypto-bg"></div>
            </div>
          </div>
          
          <div className="flex justify-between mt-2 text-[10px] font-bold tracking-widest text-crypto-muted uppercase">
            <span>-1.0</span>
            <span>0</span>
            <span>+1.0</span>
          </div>
        </div>

        {/* Score */}
        <div className="grid grid-cols-3 gap-3 mt-6">
          <div className="p-3 rounded-xl bg-crypto-bg/50 border border-crypto-border/30 text-center">
            <div className="text-[10px] font-bold tracking-widest text-crypto-muted uppercase">Score</div>
            <div className={`text-xl font-black mono mt-1 ${textColor}`}>{avg.toFixed(3)}</div>
          </div>
          <div className="p-3 rounded-xl bg-crypto-bg/50 border border-crypto-border/30 text-center">
            <div className="text-[10px] font-bold tracking-widest text-crypto-muted uppercase">Sentiment</div>
            <div className={`text-sm font-bold mt-1 ${textColor}`}>{score.toFixed(0)}%</div>
          </div>
          <div className="p-3 rounded-xl bg-crypto-bg/50 border border-crypto-border/30 text-center">
            <div className="text-[10px] font-bold tracking-widest text-crypto-muted uppercase">Sources</div>
            <div className="text-sm font-bold text-white mt-1">{daily.length} days</div>
          </div>
        </div>

        {/* Daily trend */}
        {daily.length > 0 && (
          <div className="mt-6">
            <div className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-3">14-Day Trend</div>
            <div className="flex items-end gap-1 h-16">
              {daily.slice(-14).map((d, i) => {
                const h = ((d.compound + 1) / 2) * 100
                const isPos = d.compound > 0
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1 group">
                    <div className="relative flex-1 w-full flex items-end">
                      <div
                        className={`w-full rounded-t transition-all duration-500 group-hover:opacity-80 ${
                          isPos ? 'bg-crypto-bull/60 group-hover:bg-crypto-bull' : 'bg-crypto-bear/60 group-hover:bg-crypto-bear'
                        }`}
                        style={{ height: `${Math.max(8, h)}%` }}
                        title={`${d.date}: ${d.compound.toFixed(3)} (${d.count} mentions)`}
                      ></div>
                    </div>
                    <div className="text-[9px] text-crypto-muted font-medium">
                      {new Date(d.date).toLocaleDateString('en', { day: '2-digit' })}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Sources */}
        <div className="grid grid-cols-3 gap-2 mt-6">
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-crypto-bg/30 border border-crypto-border/20">
            <Newspaper size={14} className="text-crypto-accent" />
            <div>
              <div className="text-xs font-semibold text-white">News</div>
              <div className="text-[10px] text-crypto-muted">CryptoPanic</div>
            </div>
          </div>
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-crypto-bg/30 border border-crypto-border/20">
            <MessageCircle size={14} className="text-crypto-accent2" />
            <div>
              <div className="text-xs font-semibold text-white">Reddit</div>
              <div className="text-[10px] text-crypto-muted">r/Crypto</div>
            </div>
          </div>
          <div className="flex items-center gap-2 p-2.5 rounded-xl bg-crypto-bg/30 border border-crypto-border/20">
            <Users size={14} className="text-violet-400" />
            <div>
              <div className="text-xs font-semibold text-white">Twitter</div>
              <div className="text-[10px] text-crypto-muted">Social</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
