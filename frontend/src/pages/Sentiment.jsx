import { useSettingsStore } from '../store/useSettingsStore'
import { THEMES } from '../store/useSettingsStore'
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMarketStore } from '../store/useMarketStore'
import GlassCard from '../components/GlassCard'
import SentimentGauge from '../components/SentimentGauge'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, AreaChart, Area } from 'recharts'
import { Sparkles, MessageCircle, Newspaper, Users, Brain, TrendingUp, Search } from 'lucide-react'

const safeFixed = (v,d=2)=>{ const n=typeof v==="number"?v:parseFloat(v); return isNaN(n)? (0).toFixed(d) : n.toFixed(d) }

export default function Sentiment() {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const isDark = !isLight

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
    <div className={`min-h-screen relative font-poppins ${isDark ? 'bg-black' : 'bg-[#E3EDF7]'}`}>

      
      
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-black dark:bg-white flex items-center justify-center shadow-lg">
                <Sparkles size={20} className="text-white" />
              </span>
              <span className="text-white">Sentiment Intelligence</span>
              <span className="px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-black/5 dark:border-white/5 text-zinc-500 text-xs font-bold tracking-widest">VADER • FINBERT</span>
            </h1>
            <p className="text-zinc-500 text-sm mt-2">News + Reddit + Twitter aggregated • Daily compound score merged into price features</p>
          </div>
          
          <select value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)} className="ui-card border border-black/5 dark:border-white/5 rounded-xl px-4 py-2.5 text-sm font-medium text-white">
            {['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD','DOGE-USD'].map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <TrendingUp size={18} className="text-zinc-900 dark:text-white" />
                  Daily Sentiment • {selectedSymbol} • Avg: {safeFixed(data?.average_compound,3) || '0.000'}
                </h3>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-600 border border-black/5 dark:border-white/5">Bullish &gt; 0.1</span>
                  <span className="px-2 py-1 rounded-full bg-red-500/10 text-red-500 border border-red-500/10">Bearish &lt; -0.1</span>
                </div>
              </div>
              
              {loading ? (
                <div className="h-[300px] flex items-center justify-center text-zinc-500">Loading sentiment...</div>
              ) : data?.daily ? (
                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={data.daily}>
                    <defs>
                      <linearGradient id="sentGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00d395" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00d395" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" stroke="#475569" fontSize={11} tickFormatter={d => d.slice(5)} />
                    <YAxis domain={[-1,1]} stroke="#475569" fontSize={11} />
                    <Tooltip contentStyle={{ background: '#10161f', border: '1px solid #1e2a3a', borderRadius: '12px' }} />
                    <Area type="monotone" dataKey="compound" stroke="#00d395" fill="url(#sentGrad)" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="compound" stroke="#00d395" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-zinc-500">No sentiment data - using synthetic fallback</div>
              )}
            </GlassCard>

            {data?.daily && (
              <GlassCard className="p-6">
                <h3 className="font-bold text-white mb-4">Sentiment Breakdown • Positive vs Negative</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={data.daily}>
                    <XAxis dataKey="date" stroke="#475569" fontSize={11} tickFormatter={d => d.slice(5)} />
                    <YAxis stroke="#475569" fontSize={11} />
                    <Tooltip contentStyle={{ background: '#10161f', border: '1px solid #1e2a3a', borderRadius: '12px' }} />
                    <Bar dataKey="pos" stackId="a" fill="#00d395" name="Positive" radius={[0,0,0,0]} />
                    <Bar dataKey="neg" stackId="a" fill="#ff4b4b" name="Negative" radius={[4,4,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </GlassCard>
            )}

            <GlassCard className="p-6">
              <h3 className="font-bold text-white mb-4">How Sentiment Works</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { icon: Newspaper, title: 'CryptoPanic News', desc: 'Real-time crypto news aggregated, filtered by currency. Fallback to synthetic if no API key.', color: 'from-black to-zinc-800' },
                  { icon: MessageCircle, title: 'Reddit', desc: 'r/CryptoCurrency, r/Bitcoin, r/Ethereum. PRAW API or public JSON fallback.', color: 'from-zinc-500 to-zinc-700' },
                  { icon: Users, title: 'Twitter / X', desc: 'Bearer token search, VADER + FinBERT scoring. Weighted by engagement.', color: 'from-zinc-500 to-zinc-700' },
                ].map((item, i) => (
                  <div key={i} className="p-4 rounded-xl bg-transparent/40 border border-black/5 dark:border-white/5/30">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center mb-3`}>
                      <item.icon size={18} className="text-white" />
                    </div>
                    <div className="font-bold text-white text-sm mb-1">{item.title}</div>
                    <div className="text-xs text-zinc-500 leading-relaxed">{item.desc}</div>
                  </div>
                ))}
              </div>
              <div className="mt-6 p-4 rounded-xl bg-crypto-accent/5 border border-crypto-accent/10">
                <div className="flex gap-3">
                  <Brain size={16} className="text-zinc-900 dark:text-white mt-0.5" />
                  <div className="text-xs text-zinc-500 leading-relaxed">
                    <span className="text-white font-medium">Feature Engineering:</span> Daily aggregated compound score → Sentiment_Compound, Sentiment_MA7 (7-day moving avg), Sentiment_Diff (daily change), Sentiment_Count (mention volume). Merged into price DataFrame for model training. 69 total features.
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>

          <div className="lg:col-span-4 space-y-6">
            {data && <SentimentGauge sentiment={data} symbol={selectedSymbol} />}

            <GlassCard className="p-6">
              <h3 className="font-bold text-white mb-4 flex items-center gap-2">
                <Search size={16} className="text-zinc-900 dark:text-white" />
                Analyze Custom Text
              </h3>
              <textarea 
                value={text} 
                onChange={e => setText(e.target.value)} 
                placeholder="e.g. Bitcoin is extremely bullish, going to the moon! Institutional adoption accelerating..." 
                className="w-full bg-transparent border border-black/5 dark:border-white/5 rounded-xl p-4 h-28 text-sm text-white placeholder:text-zinc-500 focus:border-crypto-accent/50 focus:outline-none resize-none" 
              />
              <button onClick={analyze} className="btn-primary w-full mt-3 flex items-center justify-center gap-2">
                <Sparkles size={14} /> Analyze Sentiment
              </button>
              
              {analysis && (
                <div className="mt-4 p-4 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-bold tracking-widest text-zinc-500 uppercase">Result</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${analysis.sentiment.compound > 0 ? 'bg-emerald-500/10 text-emerald-600' : analysis.sentiment.compound < 0 ? 'bg-red-500/10 text-red-500' : 'bg-gray-500/10 text-gray-400'}`}>
                      {analysis.sentiment.compound > 0.5 ? 'Very Bullish' : analysis.sentiment.compound > 0.1 ? 'Bullish' : analysis.sentiment.compound < -0.5 ? 'Very Bearish' : analysis.sentiment.compound < -0.1 ? 'Bearish' : 'Neutral'}
                    </span>
                  </div>
                  <div className="text-2xl font-black mono text-white mb-2">{safeFixed(analysis.sentiment?.compound,3)}</div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-emerald-500/10 text-center">
                      <div className="text-zinc-500">Pos</div>
                      <div className="font-bold text-emerald-600">{safeFixed(analysis.sentiment?.pos,2)}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-red-500/10 text-center">
                      <div className="text-zinc-500">Neg</div>
                      <div className="font-bold text-red-500">{safeFixed(analysis.sentiment?.neg,2)}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-gray-500/10 text-center">
                      <div className="text-zinc-500">Neu</div>
                      <div className="font-bold text-gray-400">{safeFixed(analysis.sentiment?.neu,2)}</div>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-6">
                <div className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-3">Example Phrases</div>
                <div className="space-y-2">
                  {[
                    'Bitcoin to the moon! 🚀 Extremely bullish!',
                    'Market crash incoming, bearish sentiment dominates',
                    'Ethereum upgrade successful, positive momentum',
                  ].map((ex, i) => (
                    <button key={i} onClick={() => setText(ex)} className="w-full text-left p-2.5 rounded-xl bg-transparent/50 border border-black/5 dark:border-white/5/30 hover:border-black/5 dark:border-white/5/60 text-xs text-zinc-500 hover:text-white transition">
                      "{ex}"
                    </button>
                  ))}
                </div>
              </div>
            </GlassCard>

            <GlassCard className="p-6">
              <h3 className="font-bold text-white mb-3">Lexicon Highlights</h3>
              <div className="space-y-3 text-xs">
                <div>
                  <div className="font-semibold text-emerald-600 mb-1">Bullish Keywords</div>
                  <div className="flex flex-wrap gap-1">
                    {['moon', 'bullish', 'pump', 'breakout', 'rally', 'ATH', 'accumulate', 'buy'].map(k => (
                      <span key={k} className="px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-600 border border-black/5 dark:border-white/5 text-[11px]">{k}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="font-semibold text-red-500 mb-1">Bearish Keywords</div>
                  <div className="flex flex-wrap gap-1">
                    {['crash', 'bearish', 'dump', 'selloff', 'fud', 'panic', 'capitulation'].map(k => (
                      <span key={k} className="px-2 py-1 rounded-full bg-red-500/10 text-red-500 border border-red-500/10 text-[11px]">{k}</span>
                    ))}
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  )
}
