import { useEffect, useState } from 'react'
import { Search, Zap, TrendingUp, Activity, AlertTriangle } from 'lucide-react'

export default function Scanner() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('all')

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/scanner')
      const json = await res.json()
      setData(json)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 30000); return () => clearInterval(i) }, [])

  if (loading && !data) return <div className="p-6 text-center">Scanning real market for opportunities...</div>

  const filtered = (() => {
    if (!data) return []
    if (tab === 'volume') return data.volume_spikes || []
    if (tab === 'momentum') return data.momentum || []
    if (tab === 'rsi') return data.rsi_signals || []
    return data.top_opportunities || data.all || []
  })()

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3"><Search className="text-emerald-400" /> Market Scanner - Real Opportunities</h1>
          <p className="text-crypto-muted mt-1">Live Binance scan - volume spikes, momentum, RSI - real trading opportunities, no fake</p>
        </div>
        <button onClick={fetchData} className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-bold">Scan Now</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-crypto-card border border-crypto-border">
          <div className="text-xs text-crypto-muted uppercase">Total Opportunities</div>
          <div className="text-2xl font-black mt-1">{data?.total_opportunities || 0}</div>
          <div className="text-xs text-emerald-400 mt-1">Real market data</div>
        </div>
        <div className="p-4 rounded-2xl bg-crypto-card border border-crypto-border">
          <div className="text-xs text-crypto-muted uppercase">Volume Spikes</div>
          <div className="text-2xl font-black mt-1">{data?.volume_spikes?.length || 0}</div>
          <div className="text-xs text-amber-400 mt-1">Whale activity</div>
        </div>
        <div className="p-4 rounded-2xl bg-crypto-card border border-crypto-border">
          <div className="text-xs text-crypto-muted uppercase">Momentum</div>
          <div className="text-2xl font-black mt-1">{data?.momentum?.length || 0}</div>
          <div className="text-xs text-violet-400 mt-1">Strong movers</div>
        </div>
        <div className="p-4 rounded-2xl bg-crypto-card border border-crypto-border">
          <div className="text-xs text-crypto-muted uppercase">RSI Signals</div>
          <div className="text-2xl font-black mt-1">{data?.rsi_signals?.length || 0}</div>
          <div className="text-xs text-blue-400 mt-1">Oversold/Overbought</div>
        </div>
      </div>

      <div className="flex gap-2 p-1 rounded-xl bg-crypto-card border border-crypto-border w-fit">
        {[
          { id: 'all', label: 'Top Opportunities' },
          { id: 'volume', label: 'Volume Spikes' },
          { id: 'momentum', label: 'Momentum' },
          { id: 'rsi', label: 'RSI' }
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`px-4 py-2 rounded-lg text-sm font-medium transition ${tab === t.id ? 'bg-white text-black' : 'text-crypto-muted hover:text-white'}`}>{t.label}</button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-crypto-muted">No opportunities found - market is quiet, real data shows no strong signals</div>
        ) : (
          filtered.map((item, i) => (
            <div key={i} className="p-4 rounded-2xl bg-crypto-card border border-crypto-border hover:border-crypto-borderLight transition">
              <div className="flex items-center justify-between">
                <span className="font-black text-lg">{item.symbol}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                  item.type === 'VOLUME_SPIKE' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                  item.type === 'MOMENTUM' ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20' :
                  item.type === 'OVERSOLD' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                  item.type === 'OVERBOUGHT' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                  'bg-crypto-bg text-crypto-muted'
                }`}>{item.type}</span>
              </div>
              
              <div className="mt-3 space-y-1 text-sm">
                {item.price && <div className="flex justify-between"><span className="text-crypto-muted">Price</span><span className="font-bold">${item.price?.toLocaleString?.() || item.price}</span></div>}
                {item.change_pct !== undefined && <div className="flex justify-between"><span className="text-crypto-muted">Change</span><span className={`font-bold ${item.change_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{item.change_pct?.toFixed(2)}%</span></div>}
                {item.ratio && <div className="flex justify-between"><span className="text-crypto-muted">Vol Ratio</span><span className="font-bold text-amber-400">{item.ratio?.toFixed(2)}x</span></div>}
                {item.rsi && <div className="flex justify-between"><span className="text-crypto-muted">RSI</span><span className={`font-bold ${item.rsi < 30 ? 'text-emerald-400' : 'text-red-400'}`}>{item.rsi?.toFixed(1)}</span></div>}
                {item.strength && <div className="flex justify-between"><span className="text-crypto-muted">Strength</span><span className={`text-xs px-2 py-0.5 rounded-full ${item.strength === 'STRONG' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>{item.strength}</span></div>}
              </div>

              <div className="mt-3 p-2 rounded-xl bg-crypto-bg border border-crypto-border/50">
                <div className="text-xs text-crypto-muted flex items-center gap-1">
                  {item.type === 'VOLUME_SPIKE' ? <Activity size={12} /> : item.type === 'MOMENTUM' ? <TrendingUp size={12} /> : <AlertTriangle size={12} />}
                  {item.signal || item.action}
                </div>
              </div>

              <div className="mt-2 flex items-center gap-2 text-[10px] text-crypto-muted">
                <span className="px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/10">REAL DATA</span>
                <span>{item.category || item.type}</span>
                <span className="ml-auto">{item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {data && (
        <div className="p-4 rounded-2xl bg-crypto-card border border-crypto-border">
          <div className="text-xs text-crypto-muted">Source: {data.source} • {data.no_fake} • Timestamp: {new Date(data.timestamp).toLocaleString()}</div>
        </div>
      )}
    </div>
  )
}
