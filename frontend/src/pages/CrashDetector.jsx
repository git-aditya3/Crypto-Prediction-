import { useEffect, useState } from 'react'
import { AlertTriangle, Activity, Zap, Shield, TrendingDown, DollarSign, BarChart3, MessageSquare, Newspaper, Eye, RefreshCw } from 'lucide-react'
import { useSettingsStore } from '../store/useSettingsStore'

export default function CrashDetector() {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'
  const [data, setData] = useState(null)
  const [history, setHistory] = useState([])
  const [alerts, setAlerts] = useState([])
  const [raw, setRaw] = useState(null)
  const [loading, setLoading] = useState(true)
  const [auto, setAuto] = useState(true)

  const fetchAll = async (force=false) => {
    try {
      const [statusRes, histRes, alertsRes, rawRes] = await Promise.all([
        fetch(`/api/crash/scan${force ? '?force=true' : ''}`).then(r=>r.json()).catch(()=>null),
        fetch('/api/crash/history?limit=20').then(r=>r.json()).catch(()=>null),
        fetch('/api/crash/alerts?limit=10').then(r=>r.json()).catch(()=>null),
        fetch('/api/crash/raw').then(r=>r.json()).catch(()=>null),
      ])
      if (statusRes) setData(statusRes)
      if (histRes) setHistory(histRes.history||[])
      if (alertsRes) setAlerts(alertsRes.alerts||[])
      if (rawRes) setRaw(rawRes)
    } catch(e){console.error(e)} finally {setLoading(false)}
  }

  useEffect(()=>{ fetchAll(true) },[])
  useEffect(()=>{
    if(!auto) return
    const id=setInterval(()=>fetchAll(false), 20000)
    return ()=>clearInterval(id)
  },[auto])

  const levelColor = (lvl) => {
    if(lvl==='CRITICAL') return 'bg-red-600 text-white border-red-600'
    if(lvl==='HIGH') return 'bg-orange-500 text-black border-orange-500'
    if(lvl==='MEDIUM') return 'bg-amber-400 text-black border-amber-400'
    return 'bg-emerald-500 text-black border-emerald-500'
  }
  const scoreColor = (s) => {
    if(s>=80) return 'text-red-500'
    if(s>=60) return 'text-orange-500'
    if(s>=35) return 'text-amber-500'
    return 'text-emerald-500'
  }

  if(loading) return <div className="p-6 text-center text-zinc-500">Loading crash detector - local fast scraper...</div>

  return (
    <div className={`min-h-screen font-poppins ${isDark ? 'bg-black' : 'bg-[#E3EDF7]'}`}>
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h1 className={`text-2xl font-bold flex items-center gap-3 ${isDark ? 'text-white' : 'text-black'}`}><AlertTriangle className="text-red-500" /> Crash Detector • Early Warning</h1>
            <p className="text-[11px] text-zinc-500 mt-1">Local processing • Fast scraper • Detects crashes BEFORE market impact • Binance + Funding + OI + Liquidations + Orderbook + Whales + Fear&Greed + Reddit + News</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-[10px] px-2 py-1 rounded-full border ${isDark ? 'bg-zinc-900 border-white/10 text-zinc-400' : 'bg-white border-black/5 text-zinc-500'}`}>LOCAL • {data?.total_time_ms?.toFixed(0) || 0}ms total • {data?.processing_time_ms?.toFixed(0) || 0}ms processing</span>
            <button onClick={()=>setAuto(!auto)} className={`px-3 py-1.5 rounded-xl text-[11px] font-bold border ${auto ? 'bg-emerald-500 text-black border-emerald-500' : 'ui-card'}`}>{auto ? 'Auto 20s' : 'Manual'}</button>
            <button onClick={()=>fetchAll(true)} className="px-3 py-1.5 rounded-xl bg-black dark:bg-white text-white text-[11px] font-bold flex items-center gap-1"><RefreshCw size={12} /> Scan Now</button>
          </div>
        </div>

        {/* Main Risk Card */}
        {data && (
          <div className={`ui-card p-5 border-2 ${data.level==='CRITICAL' ? 'border-red-500/50' : data.level==='HIGH' ? 'border-orange-500/30' : data.level==='MEDIUM' ? 'border-amber-500/20' : 'border-emerald-500/20'}`}>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className={`w-20 h-20 rounded-2xl flex flex-col items-center justify-center border-2 font-black ${levelColor(data.level)}`}>
                  <span className="text-2xl">{data.crash_risk?.toFixed(0)}%</span>
                  <span className="text-[9px]">{data.level}</span>
                </div>
                <div>
                  <div className={`font-bold text-[16px] ${isDark ? 'text-white' : 'text-black'}`}>BTC ${data.btc_price?.toLocaleString()} • {data.btc_change>0?'+':''}{data.btc_change?.toFixed(2)}% 24h</div>
                  <div className="text-[12px] text-zinc-500 mt-1 max-w-[600px]">{data.summary}</div>
                  <div className={`text-[11px] mt-2 p-2 rounded-lg ${isDark ? 'bg-zinc-900' : 'bg-zinc-100'} ${data.level==='CRITICAL' ? 'text-red-500' : data.level==='HIGH' ? 'text-orange-500' : 'text-zinc-500'}`}>{data.action}</div>
                </div>
              </div>
              <div className="text-[11px] space-y-1">
                <div className="flex justify-between gap-4"><span className="text-zinc-500">Confidence</span><span className="font-bold">{data.confidence}%</span></div>
                <div className="flex justify-between gap-4"><span className="text-zinc-500">Fetch</span><span>{data.fetch_time_ms?.toFixed(0)}ms</span></div>
                <div className="flex justify-between gap-4"><span className="text-zinc-500">Processing</span><span>{data.processing_time_ms?.toFixed(0)}ms local</span></div>
                <div className="flex justify-between gap-4"><span className="text-zinc-500">Cached</span><span>{data.cached ? 'Yes 20s' : 'No fresh'}</span></div>
                <div className="flex justify-between gap-4"><span className="text-zinc-500">Sources</span><span>{data.raw?.spot_count || 0} tickers</span></div>
              </div>
            </div>
          </div>
        )}

        {/* Signals Grid */}
        {data?.signals && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {data.signals.map((s,i)=>(
              <div key={i} className={`ui-card p-3 border ${s.score>=60 ? 'border-orange-500/20' : 'border-black/5 dark:border-white/5'}`}>
                <div className="flex items-center justify-between">
                  <span className={`font-bold text-[11px] uppercase ${isDark ? 'text-white' : 'text-black'}`}>{s.name.replace('_',' ')}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${levelColor(s.level)}`}>{s.score}% {s.level}</span>
                </div>
                <div className="text-[11px] text-zinc-500 mt-2 leading-tight">{s.reason}</div>
                <div className="mt-2 w-full h-1.5 rounded-full bg-zinc-200 dark:bg-zinc-800 overflow-hidden">
                  <div className={`h-full ${s.score>=80 ? 'bg-red-500' : s.score>=60 ? 'bg-orange-500' : s.score>=35 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{width: `${Math.min(100,s.score)}%`}}></div>
                </div>
                <div className="mt-1 text-[10px] text-zinc-400">Weight {s.weight}x</div>
              </div>
            ))}
          </div>
        )}

        {/* Raw Sources + Alerts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="ui-card p-4 lg:col-span-2">
            <h3 className={`font-bold text-[13px] mb-3 flex items-center gap-2 ${isDark ? 'text-white' : 'text-black'}`}><Activity size={14} /> Live Sources • Local Fast Scraper</h3>
            {raw && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-[11px]">
                <div className={`p-2 rounded-lg ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'}`}><div className="text-zinc-500">Spot Tickers</div><div className="font-bold">{raw.spot_tickers_count}</div><div className="text-[10px] text-zinc-400">BTC ${raw.btc?.price?.toLocaleString()} {raw.btc?.change_pct?.toFixed(1)}%</div></div>
                <div className={`p-2 rounded-lg ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'}`}><div className="text-zinc-500">Futures</div><div className="font-bold">{raw.futures_count}</div></div>
                <div className={`p-2 rounded-lg ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'}`}><div className="text-zinc-500">Funding Rates</div><div className="font-bold">{raw.funding_count}</div></div>
                <div className={`p-2 rounded-lg ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'}`}><div className="text-zinc-500">Fear & Greed</div><div className={`font-bold ${raw.fear_greed?.value<25 ? 'text-red-500' : raw.fear_greed?.value<50 ? 'text-amber-500' : 'text-emerald-500'}`}>{raw.fear_greed?.value} {raw.fear_greed?.classification}</div></div>
                <div className={`p-2 rounded-lg ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'}`}><div className="text-zinc-500">Liquidations</div><div className="font-bold">{Object.keys(raw.liquidations||{}).length} symbols</div><div className="text-[10px]">{Object.entries(raw.liquidations||{}).slice(0,2).map(([k,v])=>`${k}: $${(v.total/1e6).toFixed(1)}M`).join(' ')}</div></div>
                <div className={`p-2 rounded-lg ${isDark ? 'bg-zinc-900' : 'bg-zinc-50'}`}><div className="text-zinc-500">Reddit + News</div><div className="font-bold">{raw.reddit_count} posts, {raw.news_count} news</div><div className="text-[10px] text-red-400">{raw.reddit_crash?.length || 0} crash posts, {raw.news_crash?.length || 0} crash news</div></div>
              </div>
            )}
            {raw?.reddit_crash?.length>0 && (
              <div className="mt-3">
                <div className="text-[11px] font-bold mb-1 flex items-center gap-1"><MessageSquare size={12} /> Crash Reddit</div>
                {raw.reddit_crash.map((p,i)=><div key={i} className="text-[11px] text-zinc-500 truncate">• {p.title} ({p.score}↑)</div>)}
              </div>
            )}
            {raw?.news_crash?.length>0 && (
              <div className="mt-2">
                <div className="text-[11px] font-bold mb-1 flex items-center gap-1"><Newspaper size={12} /> Crash News</div>
                {raw.news_crash.map((n,i)=><div key={i} className="text-[11px] text-zinc-500 truncate">• {n.title}</div>)}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="ui-card p-4">
              <h3 className={`font-bold text-[13px] mb-3 flex items-center gap-2 ${isDark ? 'text-white' : 'text-black'}`}><Shield size={14} /> Crash Alerts</h3>
              {alerts.length===0 ? <div className="text-[11px] text-zinc-500">No HIGH/CRITICAL alerts - market stable</div> : (
                <div className="space-y-2">
                  {alerts.map((a,i)=>(
                    <div key={i} className={`p-2 rounded-lg border text-[11px] ${a.level==='CRITICAL' ? 'bg-red-500/10 border-red-500/20' : 'bg-orange-500/10 border-orange-500/20'}`}>
                      <div className="flex justify-between"><span className="font-bold">{a.level} {a.risk}%</span><span className="text-zinc-500">{new Date(a.timestamp).toLocaleTimeString()}</span></div>
                      <div className="text-zinc-500 mt-1">{a.summary?.slice(0,120)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="ui-card p-4">
              <h3 className={`font-bold text-[13px] mb-3 flex items-center gap-2 ${isDark ? 'text-white' : 'text-black'}`}><BarChart3 size={14} /> History</h3>
              <div className="space-y-1 max-h-[200px] overflow-auto">
                {history.map((h,i)=>(
                  <div key={i} className="flex justify-between text-[11px] py-1 border-b border-black/5 dark:border-white/5 last:border-0">
                    <span className="text-zinc-500">{new Date(h.timestamp).toLocaleTimeString()}</span>
                    <span className={`font-bold ${scoreColor(h.crash_risk)}`}>{h.crash_risk?.toFixed(0)}% {h.level}</span>
                    <span className={h.btc_change<0 ? 'text-red-500' : 'text-emerald-500'}>{h.btc_change?.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="ui-card p-4">
          <h3 className={`font-bold text-[12px] mb-2 ${isDark ? 'text-white' : 'text-black'}`}>How it detects crashes BEFORE market impact • Local & Fast</h3>
          <div className={`text-[11px] leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
            <span className="font-bold">1. Orderbook Imbalance:</span> Bid liquidity drying 30-70% before crash, ask walls building. <span className="font-bold">2. Whale Sells:</span> Large sells concentration above 60% sell ratio. <span className="font-bold">3. Liquidations:</span> Long liquidation cascade signals squeeze. <span className="font-bold">4. Funding Flip:</span> Funding positive to negative rapidly, extreme negative. <span className="font-bold">5. Correlation:</span> 80%+ coins dropping together = systemic. <span className="font-bold">6. Volume Spike + Drop:</span> Distribution. <span className="font-bold">7. Fear & Greed:</span> Panic below 25. <span className="font-bold">8. News/Reddit:</span> Crash keywords spike before price. <span className="font-bold">9. Stablecoin Flight:</span> BTC drop above 7% with volume. All processing locally with Session reuse, ThreadPoolExecutor parallel 12 workers, 3-5s timeouts, numpy below 10ms per signal, total under 3s.
          </div>
        </div>
      </div>
    </div>
  )
}
