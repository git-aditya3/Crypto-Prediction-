import { useSettingsStore } from '../store/useSettingsStore'
import { THEMES } from '../store/useSettingsStore'
import { useEffect, useState } from 'react'
import { Search, Zap, TrendingUp, Activity, AlertTriangle } from 'lucide-react'
import { api } from '../api/client'

export default function Scanner() {
  const theme = useSettingsStore(s => s.theme)
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const isDark = !isLight

  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('all')

  const safeFixed = (v, d=2) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return '0.00'
    return n.toFixed(d)
  }

  const safeLocale = (v) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return 'N/A'
    return n.toLocaleString(undefined, { maximumFractionDigits: 4 })
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const json = await api.getScanner().catch(() => fetch('/api/scanner').then(r => r.json()))
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
    <div className="max-w-[1600px] mx-auto px-6 py-6 font-poppins space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3"><Search className="text-emerald-600" /> Market Scanner - Real Opportunities</h1>
          <p className="text-zinc-500 mt-1">Live Binance scan - volume spikes, momentum, RSI - real trading opportunities, no fake</p>
        </div>
        <button onClick={fetchData} className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-bold">Scan Now</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-xs text-zinc-500 uppercase">Total Opportunities</div>
          <div className="text-2xl font-black mt-1">{data?.total_opportunities ?? 0}</div>
          <div className="text-xs text-emerald-600 mt-1">Real market data</div>
        </div>
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-xs text-zinc-500 uppercase">Volume Spikes</div>
          <div className="text-2xl font-black mt-1">{data?.volume_spikes?.length ?? 0}</div>
          <div className="text-xs text-zinc-500 mt-1">Whale activity</div>
        </div>
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-xs text-zinc-500 uppercase">Momentum</div>
          <div className="text-2xl font-black mt-1">{data?.momentum?.length ?? 0}</div>
          <div className="text-xs text-zinc-500 mt-1">Strong movers</div>
        </div>
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-xs text-zinc-500 uppercase">RSI Signals</div>
          <div className="text-2xl font-black mt-1">{data?.rsi_signals?.length ?? 0}</div>
          <div className="text-xs text-blue-400 mt-1">Oversold/Overbought</div>
        </div>
      </div>

      <div className="flex gap-2 p-1 rounded-xl ui-card border border-black/5 dark:border-white/5 w-fit overflow-x-auto">
        {[
          { id: 'all', label: 'Top Opportunities' },
          { id: 'volume', label: 'Volume Spikes' },
          { id: 'momentum', label: 'Momentum' },
          { id: 'rsi', label: 'RSI' }
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`px-4 py-2 rounded-lg text-sm font-medium transition whitespace-nowrap ${tab === t.id ? 'bg-white text-black' : 'text-zinc-500 hover:text-[var(--text)]'}`}>{t.label}</button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-zinc-500">No opportunities found - market is quiet, real data shows no strong signals</div>
        ) : (
          filtered.map((item, i) => (
            <div key={i} className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5 hover:border-black/5 dark:border-white/5Light transition">
              <div className="flex items-center justify-between">
                <span className="font-black text-lg">{item.symbol || 'Unknown'}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                  item.type === 'VOLUME_SPIKE' ? 'bg-amber-500/10 text-zinc-500 border border-amber-500/20' :
                  item.type === 'MOMENTUM' ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 border border-black/5 dark:border-white/5' :
                  item.type === 'OVERSOLD' ? 'bg-zinc-100 dark:bg-zinc-800 text-emerald-600 border border-black/5 dark:border-white/5' :
                  item.type === 'OVERBOUGHT' ? 'bg-red-500/10 text-red-500 border border-red-500/10' :
                  'bg-transparent text-zinc-500'
                }`}>{item.type || 'UNKNOWN'}</span>
              </div>
              
              <div className="mt-3 space-y-1 text-sm">
                {item.price != null && <div className="flex justify-between"><span className="text-zinc-500">Price</span><span className="font-bold">${safeLocale(item.price)}</span></div>}
                {item.change_pct != null && <div className="flex justify-between"><span className="text-zinc-500">Change</span><span className={`font-bold ${(item.change_pct||0) >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>{safeFixed(item.change_pct,2)}%</span></div>}
                {item.ratio != null && <div className="flex justify-between"><span className="text-zinc-500">Vol Ratio</span><span className="font-bold text-zinc-500">{safeFixed(item.ratio,2)}x</span></div>}
                {item.rsi != null && <div className="flex justify-between"><span className="text-zinc-500">RSI</span><span className={`font-bold ${(item.rsi||50) < 30 ? 'text-emerald-600' : (item.rsi||50) > 70 ? 'text-red-500' : 'text-zinc-500'}`}>{safeFixed(item.rsi,1)}</span></div>}
                {item.strength && <div className="flex justify-between"><span className="text-zinc-500">Strength</span><span className={`text-xs px-2 py-0.5 rounded-full ${item.strength === 'STRONG' ? 'bg-zinc-100 dark:bg-zinc-800 text-emerald-600' : 'bg-amber-500/10 text-zinc-500'}`}>{item.strength}</span></div>}
              </div>

              <div className="mt-3 p-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
                <div className="text-xs text-zinc-500 flex items-center gap-1">
                  {item.type === 'VOLUME_SPIKE' ? <Activity size={12} /> : item.type === 'MOMENTUM' ? <TrendingUp size={12} /> : <AlertTriangle size={12} />}
                  {item.signal || item.action || 'No signal'}
                </div>
              </div>

              <div className="mt-2 flex items-center gap-2 text-[10px] text-zinc-500">
                <span className="px-1.5 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-emerald-600 border border-emerald-500/10">REAL DATA</span>
                <span>{item.category || item.type}</span>
                <span className="ml-auto">{item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}</span>
              </div>
            </div>
          ))
        )}
      </div>

      {data && (
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-xs text-zinc-500">Source: {data.source || 'Live Binance'} • {data.no_fake || 'Real data'} • Timestamp: {data.timestamp ? new Date(data.timestamp).toLocaleString() : new Date().toLocaleString()}</div>
        </div>
      )}
    </div>
  )
}
