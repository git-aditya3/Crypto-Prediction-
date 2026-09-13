import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMarketStore } from '../store/useMarketStore'
import GlassCard from '../components/GlassCard'
import SentimentGauge from '../components/SentimentGauge'
import { Sparkles, MessageCircle, Newspaper, Users, Brain, TrendingUp, Search } from 'lucide-react'

const safeFixed = (v,d=2)=>{ const n=typeof v==="number"?v:parseFloat(v); return isNaN(n)? (0).toFixed(d) : n.toFixed(d) }

export default function Sentiment() {
  const { selectedSymbol, setSelectedSymbol } = useMarketStore()
  const [data, setData] = useState(null)
  const [text, setText] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getSentiment(selectedSymbol, 30).then(setData).catch(console.error).finally(() => setLoading(false))
  }, [selectedSymbol])

  const analyze = () => {
    if (!text) return
    api.analyzeSentiment(text).then(setAnalysis).catch(console.error)
  }

  return (
    <div className="min-h-screen theme-bg">
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-[20px] font-semibold tracking-tight text-[var(--text)] flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center shadow-[var(--glow)]"><Sparkles size={14} /></span>
              Sentiment Intelligence
              <span className="px-2 py-0.5 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] text-[var(--accent)] text-[10px] font-medium">VADER • FINBERT</span>
            </h1>
            <p className="text-[12px] mt-1 text-[var(--text-muted)]">News + Reddit + Twitter aggregated • Themed colors • 120fps</p>
          </div>
          <select value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)} className="rounded-full border bg-[var(--card)] border-[var(--border)] px-3 py-1.5 text-[12px] font-medium text-[var(--text)]">
            {['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD','DOGE-USD'].map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-8 space-y-5">
            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2">
                  <TrendingUp size={14} className="text-[var(--accent)]" />
                  Daily Sentiment • {selectedSymbol} • Avg: {safeFixed(data?.average_compound,3)}
                </h3>
                <div className="flex items-center gap-1.5 text-[10px]">
                  <span className="px-2 py-0.5 rounded-full bg-[var(--buy-soft)] text-[var(--buy)] border border-[var(--buy-border)] font-medium">Bullish &gt; 0.1</span>
                  <span className="px-2 py-0.5 rounded-full bg-[var(--sell-soft)] text-[var(--sell)] border border-[var(--sell-border)] font-medium">Bearish &lt; -0.1</span>
                </div>
              </div>
              {loading ? (
                <div className="h-[300px] flex items-center justify-center text-[var(--text-muted)]">Loading sentiment...</div>
              ) : data?.daily ? (
                <div className="space-y-2">
                  {data.daily.slice(-14).map((d, i) => (
                    <div key={i} className="flex items-center gap-3 p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
                      <span className="text-[11px] text-[var(--text-muted)] w-20">{d.date?.slice(5)}</span>
                      <div className="flex-1 h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${((d.compound + 1) / 2) * 100}%`, background: d.compound > 0 ? 'var(--buy)' : 'var(--sell)' }} />
                      </div>
                      <span className={`text-[11px] mono font-medium ${d.compound > 0 ? 'text-[var(--buy)]' : 'text-[var(--sell)]'}`}>{safeFixed(d.compound,2)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-[var(--text-muted)] text-[12px]">No sentiment data - using synthetic fallback</div>
              )}
            </GlassCard>

            <GlassCard className="p-5">
              <h3 className="font-medium text-[13px] text-[var(--text)] mb-4">How Sentiment Works</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {[
                  { icon: Newspaper, title: 'CryptoPanic News', desc: 'Real-time crypto news aggregated, filtered by currency.', color: 'var(--accent)' },
                  { icon: MessageCircle, title: 'Reddit', desc: 'r/CryptoCurrency, r/Bitcoin, r/Ethereum. PRAW API fallback.', color: 'var(--buy)' },
                  { icon: Users, title: 'Twitter / X', desc: 'Bearer token search, VADER + FinBERT scoring.', color: 'var(--sell)' },
                ].map((item, i) => (
                  <div key={i} className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-2 text-white shadow-sm" style={{ background: item.color }}>
                      <item.icon size={14} />
                    </div>
                    <div className="font-medium text-[12px] text-[var(--text)] mb-1">{item.title}</div>
                    <div className="text-[11px] text-[var(--text-muted)] leading-relaxed">{item.desc}</div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>

          <div className="lg:col-span-4 space-y-5">
            {data && <SentimentGauge sentiment={data} symbol={selectedSymbol} />}

            <GlassCard className="p-5">
              <h3 className="font-medium text-[13px] text-[var(--text)] mb-3 flex items-center gap-2">
                <Search size={14} className="text-[var(--accent)]" />
                Analyze Custom Text
              </h3>
              <textarea 
                value={text} 
                onChange={e => setText(e.target.value)} 
                placeholder="e.g. Bitcoin is extremely bullish, going to the moon!..." 
                className="w-full bg-[var(--bg-secondary)] border border-[var(--border)] rounded-xl p-3 h-24 text-[13px] text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--accent)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-ring)] resize-none transition-all" 
              />
              <button onClick={analyze} className="w-full mt-3 px-3 py-2 rounded-full bg-[var(--accent)] text-white text-[12px] font-medium flex items-center justify-center gap-1.5 shadow-[var(--glow)] hover:scale-[1.02] transition-transform">
                <Sparkles size={12} /> Analyze Sentiment
              </button>
              
              {analysis && (
                <div className="mt-4 p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)]">Result</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${analysis.sentiment.compound > 0 ? 'bg-[var(--buy-soft)] text-[var(--buy)] border-[var(--buy-border)]' : analysis.sentiment.compound < 0 ? 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]' : 'bg-[var(--bg-tertiary)] text-[var(--text-muted)] border-[var(--border)]'}`}>
                      {analysis.sentiment.compound > 0.5 ? 'Very Bullish' : analysis.sentiment.compound > 0.1 ? 'Bullish' : analysis.sentiment.compound < -0.5 ? 'Very Bearish' : analysis.sentiment.compound < -0.1 ? 'Bearish' : 'Neutral'}
                    </span>
                  </div>
                  <div className="text-[20px] font-semibold mono text-[var(--text)] mb-2">{safeFixed(analysis.sentiment?.compound,3)}</div>
                  <div className="grid grid-cols-3 gap-2 text-[11px]">
                    <div className="p-2 rounded-lg bg-[var(--buy-soft)] border border-[var(--buy-border)] text-center">
                      <div className="text-[10px] text-[var(--text-muted)]">Pos</div>
                      <div className="font-medium text-[var(--buy)]">{safeFixed(analysis.sentiment?.pos,2)}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-[var(--sell-soft)] border border-[var(--sell-border)] text-center">
                      <div className="text-[10px] text-[var(--text-muted)]">Neg</div>
                      <div className="font-medium text-[var(--sell)]">{safeFixed(analysis.sentiment?.neg,2)}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border)] text-center">
                      <div className="text-[10px] text-[var(--text-muted)]">Neu</div>
                      <div className="font-medium text-[var(--text-sec)]">{safeFixed(analysis.sentiment?.neu,2)}</div>
                    </div>
                  </div>
                </div>
              )}
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  )
}
