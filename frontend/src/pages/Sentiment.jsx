import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useMarketStore } from '../store/useMarketStore'
import GlassCard from '../components/GlassCard'
import SentimentGauge from '../components/SentimentGauge'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, AreaChart, Area } from 'recharts'
import { Sparkles, MessageCircle, Newspaper, Users, Brain, TrendingUp, Search } from 'lucide-react'

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
    <div className="min-h-screen bg-crypto-bg relative">
      <div className="absolute inset-0 bg-gradient-mesh opacity-20 pointer-events-none"></div>
      
      <div className="relative max-w-[1600px] mx-auto p-6 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg">
                <Sparkles size={20} className="text-white" />
              </span>
              <span className="text-white">Sentiment Intelligence</span>
              <span className="px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-bold tracking-widest">VADER • FINBERT</span>
            </h1>
            <p className="text-crypto-muted text-sm mt-2">News + Reddit + Twitter aggregated • Daily compound score merged into price features</p>
          </div>
          
          <select value={selectedSymbol} onChange={e => setSelectedSymbol(e.target.value)} className="bg-crypto-card border border-crypto-border rounded-xl px-4 py-2.5 text-sm font-medium text-white">
            {['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD','DOGE-USD'].map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-white flex items-center gap-2">
                  <TrendingUp size={18} className="text-crypto-accent" />
                  Daily Sentiment • {selectedSymbol} • Avg: {data?.average_compound?.toFixed(3) || '0.000'}
                </h3>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-1 rounded-full bg-crypto-bull/10 text-crypto-bull border border-crypto-bull/20">Bullish &gt; 0.1</span>
                  <span className="px-2 py-1 rounded-full bg-crypto-bear/10 text-crypto-bear border border-crypto-bear/20">Bearish &lt; -0.1</span>
                </div>
              </div>
              
              {loading ? (
                <div className="h-[300px] flex items-center justify-center text-crypto-muted">Loading sentiment...</div>
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
                <div className="h-[300px] flex items-center justify-center text-crypto-muted">No sentiment data - using synthetic fallback</div>
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
                  { icon: Newspaper, title: 'CryptoPanic News', desc: 'Real-time crypto news aggregated, filtered by currency. Fallback to synthetic if no API key.', color: 'from-crypto-accent to-crypto-accent3' },
                  { icon: MessageCircle, title: 'Reddit', desc: 'r/CryptoCurrency, r/Bitcoin, r/Ethereum. PRAW API or public JSON fallback.', color: 'from-orange-500 to-red-500' },
                  { icon: Users, title: 'Twitter / X', desc: 'Bearer token search, VADER + FinBERT scoring. Weighted by engagement.', color: 'from-blue-500 to-cyan-500' },
                ].map((item, i) => (
                  <div key={i} className="p-4 rounded-xl bg-crypto-bg/40 border border-crypto-border/30">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${item.color} flex items-center justify-center mb-3`}>
                      <item.icon size={18} className="text-white" />
                    </div>
                    <div className="font-bold text-white text-sm mb-1">{item.title}</div>
                    <div className="text-xs text-crypto-muted leading-relaxed">{item.desc}</div>
                  </div>
                ))}
              </div>
              <div className="mt-6 p-4 rounded-xl bg-crypto-accent/5 border border-crypto-accent/10">
                <div className="flex gap-3">
                  <Brain size={16} className="text-crypto-accent mt-0.5" />
                  <div className="text-xs text-crypto-muted leading-relaxed">
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
                <Search size={16} className="text-crypto-accent" />
                Analyze Custom Text
              </h3>
              <textarea 
                value={text} 
                onChange={e => setText(e.target.value)} 
                placeholder="e.g. Bitcoin is extremely bullish, going to the moon! Institutional adoption accelerating..." 
                className="w-full bg-crypto-bg border border-crypto-border rounded-xl p-4 h-28 text-sm text-white placeholder:text-crypto-muted focus:border-crypto-accent/50 focus:outline-none resize-none" 
              />
              <button onClick={analyze} className="btn-primary w-full mt-3 flex items-center justify-center gap-2">
                <Sparkles size={14} /> Analyze Sentiment
              </button>
              
              {analysis && (
                <div className="mt-4 p-4 rounded-xl bg-crypto-bg border border-crypto-border">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-bold tracking-widest text-crypto-muted uppercase">Result</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${analysis.sentiment.compound > 0 ? 'bg-crypto-bull/10 text-crypto-bull' : analysis.sentiment.compound < 0 ? 'bg-crypto-bear/10 text-crypto-bear' : 'bg-gray-500/10 text-gray-400'}`}>
                      {analysis.sentiment.compound > 0.5 ? 'Very Bullish' : analysis.sentiment.compound > 0.1 ? 'Bullish' : analysis.sentiment.compound < -0.5 ? 'Very Bearish' : analysis.sentiment.compound < -0.1 ? 'Bearish' : 'Neutral'}
                    </span>
                  </div>
                  <div className="text-2xl font-black mono text-white mb-2">{analysis.sentiment.compound?.toFixed(3)}</div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-crypto-bull/10 text-center">
                      <div className="text-crypto-muted">Pos</div>
                      <div className="font-bold text-crypto-bull">{analysis.sentiment.pos?.toFixed(2)}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-crypto-bear/10 text-center">
                      <div className="text-crypto-muted">Neg</div>
                      <div className="font-bold text-crypto-bear">{analysis.sentiment.neg?.toFixed(2)}</div>
                    </div>
                    <div className="p-2 rounded-lg bg-gray-500/10 text-center">
                      <div className="text-crypto-muted">Neu</div>
                      <div className="font-bold text-gray-400">{analysis.sentiment.neu?.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-6">
                <div className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-3">Example Phrases</div>
                <div className="space-y-2">
                  {[
                    'Bitcoin to the moon! 🚀 Extremely bullish!',
                    'Market crash incoming, bearish sentiment dominates',
                    'Ethereum upgrade successful, positive momentum',
                  ].map((ex, i) => (
                    <button key={i} onClick={() => setText(ex)} className="w-full text-left p-2.5 rounded-xl bg-crypto-bg/50 border border-crypto-border/30 hover:border-crypto-border/60 text-xs text-crypto-muted hover:text-white transition">
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
                  <div className="font-semibold text-crypto-bull mb-1">Bullish Keywords</div>
                  <div className="flex flex-wrap gap-1">
                    {['moon', 'bullish', 'pump', 'breakout', 'rally', 'ATH', 'accumulate', 'buy'].map(k => (
                      <span key={k} className="px-2 py-1 rounded-full bg-crypto-bull/10 text-crypto-bull border border-crypto-bull/20 text-[11px]">{k}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="font-semibold text-crypto-bear mb-1">Bearish Keywords</div>
                  <div className="flex flex-wrap gap-1">
                    {['crash', 'bearish', 'dump', 'selloff', 'fud', 'panic', 'capitulation'].map(k => (
                      <span key={k} className="px-2 py-1 rounded-full bg-crypto-bear/10 text-crypto-bear border border-crypto-bear/20 text-[11px]">{k}</span>
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
