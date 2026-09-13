import { useEffect, useState, useCallback } from 'react'
import { AlertTriangle, Activity, Shield, BarChart3, MessageSquare, Newspaper, RefreshCw, Zap, TrendingDown, Eye, Brain, Gauge } from 'lucide-react'
import { useSettingsStore, THEMES } from '../store/useSettingsStore'
import { api } from '../api/client'
import GlassCard from '../components/GlassCard'

export default function CrashDetector() {
  const theme = useSettingsStore(s => s.theme)
  const currentTheme = THEMES[theme] || THEMES.dark
  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const [data, setData] = useState(null)
  const [history, setHistory] = useState([])
  const [alerts, setAlerts] = useState([])
  const [raw, setRaw] = useState(null)
  const [loading, setLoading] = useState(true)
  const [auto, setAuto] = useState(true)
  const [error, setError] = useState(null)

  const fetchAll = useCallback(async (force=false) => {
    try {
      setError(null)
      const results = await Promise.allSettled([
        api.scanCrash(null, force),
        api.getCrashHistory(20),
        api.getCrashAlerts(10),
        api.getCrashRaw(),
      ])
      const [statusRes, histRes, alertsRes, rawRes] = results.map(r => r.status==='fulfilled' ? r.value : null)
      if (statusRes) setData(statusRes)
      else if (results[0].status==='rejected') setError(results[0].reason?.message || 'Scan failed')

      if (histRes?.history) setHistory(histRes.history)
      if (alertsRes?.alerts) setAlerts(alertsRes.alerts)
      if (rawRes) setRaw(rawRes)
    } catch(e){
      console.error(e)
      setError(e.message || 'Failed to fetch crash data')
    } finally {setLoading(false)}
  },[])

  useEffect(()=>{ fetchAll(true) },[fetchAll])
  useEffect(()=>{
    if(!auto) return
    const id=setInterval(()=>fetchAll(false), 20000)
    return ()=>clearInterval(id)
  },[auto, fetchAll])

  const levelColor = (lvl) => {
    if(lvl==='CRITICAL') return 'bg-gradient-to-br from-red-500 to-red-700 text-white border-red-500 shadow-lg shadow-red-500/20'
    if(lvl==='HIGH') return 'bg-gradient-to-br from-orange-400 to-orange-600 text-black border-orange-500 shadow-lg shadow-orange-500/20'
    if(lvl==='MEDIUM') return 'bg-gradient-to-br from-amber-300 to-amber-500 text-black border-amber-400 shadow-lg shadow-amber-500/20'
    return 'bg-gradient-to-br from-emerald-400 to-emerald-600 text-black border-emerald-500 shadow-lg shadow-emerald-500/20'
  }
  const scoreColor = (s) => {
    if(s>=80) return 'text-red-500'
    if(s>=60) return 'text-orange-500'
    if(s>=35) return 'text-amber-500'
    return 'text-emerald-500'
  }
  const safeFixed = (v,d=2)=>{ const n=typeof v==='number'?v:parseFloat(v); return isNaN(n)?'0.00':n.toFixed(d) }

  if(loading) return (
    <div className="min-h-screen theme-bg p-6 flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="w-12 h-12 rounded-xl bg-[var(--accent)] animate-pulse mx-auto" />
        <div className={`font-bold ${isLight ? 'text-black' : 'text-white'}`}>Loading crash detector</div>
        <div className="text-zinc-500 text-[12px]">Local fast scraper • {currentTheme.icon} {currentTheme.name} theme</div>
        <div className="flex justify-center gap-1">
          <span className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" />
          <span className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-[var(--accent)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  )

  return (
    <div className={`min-h-screen font-poppins theme-bg ${isLight ? '' : ''}`}>
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-6">
        {/* Header */}
        <div className="ui-card p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 via-orange-500/5 to-transparent opacity-60 group-hover:opacity-100 transition-opacity" />
          <div className="relative z-10">
            <h1 className={`text-2xl md:text-3xl font-black tracking-tight flex items-center gap-3 flex-wrap ${isLight ? 'text-black' : 'text-white'}`}>
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 text-white flex items-center justify-center shadow-lg animate-pulse">
                <AlertTriangle size={20} />
              </div>
              Crash Detector
              <span className="ui-pill-live px-3 py-1 text-[10px] font-black">EARLY WARNING</span>
              <span className={`hidden md:inline-flex text-[10px] px-2.5 py-1 rounded-full border font-bold ${currentTheme.preview}`}>{currentTheme.icon} {currentTheme.name}</span>
            </h1>
            <p className={`text-[12px] mt-2 max-w-4xl leading-relaxed ${isLight ? 'text-zinc-700' : 'text-zinc-300'}`}>
              <span className="inline-flex items-center gap-1.5"><Eye size={12} className="text-[var(--accent)]" /> Local processing</span>
              <span className="mx-2 w-1 h-1 bg-[var(--border)] rounded-full inline-block" />
              Fast scraper detects crashes BEFORE market impact
              <span className="mx-2 w-1 h-1 bg-[var(--border)] rounded-full inline-block" />
              CoinDCX INR primary + Binance fallback
            </p>
            <div className="flex gap-1.5 mt-2 flex-wrap">
              <span className="ui-pill text-[9px]">Funding</span>
              <span className="ui-pill text-[9px]">OI</span>
              <span className="ui-pill text-[9px]">Liquidations</span>
              <span className="ui-pill text-[9px]">Orderbook</span>
              <span className="ui-pill text-[9px]">Whales</span>
              <span className="ui-pill text-[9px]">Fear&Greed</span>
              <span className="ui-pill text-[9px]">Reddit</span>
              <span className="ui-pill text-[9px]">News</span>
              <span className="ui-pill-accent text-[9px]">CoinDCX</span>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap relative z-10">
            <span className={`text-[10px] px-3 py-2 rounded-xl border font-bold flex items-center gap-2 ${isLight ? 'bg-white border-black/5 text-zinc-700 shadow-sm' : 'bg-black/40 border-white/10 text-zinc-300'}`}>
              <Gauge size={12} className="text-[var(--accent)]" />
              {safeFixed(data?.total_time_ms,0)}ms total • {safeFixed(data?.processing_time_ms,0)}ms proc • Q {((data?.data_quality||0)*100).toFixed(0)}%
            </span>
            <button onClick={()=>setAuto(!auto)} className={`px-4 py-2 rounded-xl text-[11px] font-black border transition-all hover:scale-105 ${auto ? 'bg-emerald-500 text-black border-emerald-500 shadow-lg shadow-emerald-500/20' : 'ui-card hover:border-[var(--accent)]/30'}`}>
              {auto ? '⚡ Auto 20s' : '⏸ Manual'}
            </button>
            <button onClick={()=>fetchAll(true)} className="px-4 py-2 rounded-xl bg-[var(--accent)] text-[var(--bg)] text-[11px] font-black flex items-center gap-1.5 hover:scale-105 hover:shadow-lg transition-all shadow-md">
              <RefreshCw size={12} /> Scan Now
            </button>
          </div>
        </div>

        {error && (
          <div className="ui-card p-4 border border-red-500/30 bg-red-500/10 text-[12px] text-red-500 flex items-center gap-2">
            <AlertTriangle size={14} /> Error: {error} - retrying with cached data
          </div>
        )}

        {data?.warnings?.length>0 && (
          <div className={`ui-card p-4 border text-[11px] ${isLight ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-amber-500/20 bg-amber-500/10 text-amber-300'}`}>
            <div className="font-black flex items-center gap-2"><Shield size={12} /> Warnings:</div>
            <div className="mt-1 space-y-1">
              {data.warnings.map((w,i)=><div key={i} className="flex gap-2"><span>•</span><span>{w}</span></div>)}
            </div>
          </div>
        )}

        {data && (
          <GlassCard className={`p-6 border-2 overflow-hidden relative ${data.level==='CRITICAL' ? 'border-red-500/50 shadow-xl shadow-red-500/10' : data.level==='HIGH' ? 'border-orange-500/30 shadow-xl shadow-orange-500/10' : data.level==='MEDIUM' ? 'border-amber-500/20' : 'border-emerald-500/20'}`} glow={data.level!=='LOW'}>
            <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/5 via-transparent to-transparent pointer-events-none" />
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
              <div className="flex items-center gap-5">
                <div className={`w-24 h-24 rounded-2xl flex flex-col items-center justify-center border-2 font-black shadow-xl relative overflow-hidden group hover:scale-105 transition-transform ${levelColor(data.level)}`}>
                  <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
                  <span className="text-3xl relative z-10">{safeFixed(data.crash_risk,0)}%</span>
                  <span className="text-[10px] font-black tracking-wide relative z-10">{data.level}</span>
                  <div className="absolute bottom-1 left-1 right-1 h-1 bg-black/20 rounded-full overflow-hidden">
                    <div className="h-full bg-white/60 rounded-full" style={{ width: `${data.crash_risk}%` }} />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className={`font-black text-[18px] flex items-center gap-2 flex-wrap ${isLight ? 'text-black' : 'text-white'}`}>
                    BTC ${data.btc_price ? data.btc_price.toLocaleString() : 'N/A'} 
                    <span className={`px-2.5 py-1 rounded-full text-[12px] font-black ${data.btc_change>=0 ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' : 'bg-red-500/10 text-red-500 border border-red-500/20'}`}>
                      {data.btc_change>0?'+':''}{safeFixed(data.btc_change,2)}% 24h
                    </span>
                  </div>
                  <div className={`text-[13px] mt-2 leading-relaxed max-w-[600px] ${isLight ? 'text-zinc-700' : 'text-zinc-300'}`}>{data.summary || 'No summary'}</div>
                  <div className={`text-[12px] mt-3 p-3 rounded-xl border font-medium ${isLight ? 'bg-zinc-50 border-black/5 text-zinc-700' : 'bg-black/40 border-white/5 text-zinc-300'} ${data.level==='CRITICAL' ? '!border-red-500/30 !text-red-400 !bg-red-500/10' : data.level==='HIGH' ? '!border-orange-500/30 !text-orange-400 !bg-orange-500/10' : ''}`}>
                    <span className="flex items-start gap-2">
                      <Zap size={14} className="mt-0.5 shrink-0" />
                      {data.action || 'No action'}
                    </span>
                  </div>
                </div>
              </div>
              <div className={`p-4 rounded-xl border space-y-2.5 min-w-[200px] ${isLight ? 'bg-white border-black/5 shadow-sm' : 'bg-black/40 border-white/5'}`}>
                {[
                  { label: 'Confidence', value: `${safeFixed(data.confidence,0)}%`, icon: Brain },
                  { label: 'Fetch', value: `${safeFixed(data.fetch_time_ms,0)}ms`, icon: Activity },
                  { label: 'Processing', value: `${safeFixed(data.processing_time_ms,0)}ms local`, icon: Zap },
                  { label: 'Quality', value: `${((data.data_quality||0)*100).toFixed(0)}%`, icon: Gauge, color: data.data_quality<0.3?'text-red-500': data.data_quality<0.6?'text-amber-500':'text-emerald-500' },
                  { label: 'Cached', value: data.cached ? 'Yes 20s' : 'No fresh', icon: Eye },
                  { label: 'Sources', value: `${data.raw?.spot_count || 0} tickers, ${data.raw?.orderbooks||0} books`, icon: BarChart3 },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between gap-4 text-[11px] group hover:bg-[var(--accent-soft)] px-2 py-1 rounded-lg transition-colors">
                    <span className={`flex items-center gap-1.5 ${isLight ? 'text-zinc-500' : 'text-zinc-500'} group-hover:text-[var(--text-sec)]`}>
                      <item.icon size={10} /> {item.label}
                    </span>
                    <span className={`font-bold ${item.color || (isLight ? 'text-black' : 'text-white')}`}>{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </GlassCard>
        )}

        {data?.signals && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.signals.map((s,i)=>(
              <GlassCard key={i} className={`p-4 border hover:scale-[1.02] hover:shadow-xl transition-all group ${s.score>=60 ? 'border-orange-500/20 hover:border-orange-500/40 hover:shadow-orange-500/10' : 'border-[var(--border)] hover:border-[var(--accent)]/20'}`}>
                <div className="flex items-center justify-between">
                  <span className={`font-black text-[11px] uppercase tracking-wide ${isLight ? 'text-black' : 'text-white'} group-hover:text-[var(--accent)] transition-colors`}>{(s.name||'').replace('_',' ')}</span>
                  <span className={`text-[10px] px-2.5 py-1 rounded-full font-black border shadow-sm ${levelColor(s.level)}`}>{safeFixed(s.score,0)}% {s.level}</span>
                </div>
                <div className={`text-[11px] mt-3 leading-relaxed line-clamp-2 ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>{s.reason || 'No reason'}</div>
                <div className="mt-3 w-full h-2 rounded-full bg-[var(--accent-soft)] overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-1000 ${s.score>=80 ? 'bg-gradient-to-r from-red-400 to-red-600' : s.score>=60 ? 'bg-gradient-to-r from-orange-400 to-orange-600' : s.score>=35 ? 'bg-gradient-to-r from-amber-400 to-amber-600' : 'bg-gradient-to-r from-emerald-400 to-emerald-600'}`} style={{width: `${Math.min(100,s.score||0)}%`}}></div>
                </div>
                <div className="mt-2 flex justify-between text-[10px]">
                  <span className={`px-2 py-0.5 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Weight {s.weight}x</span>
                  <span className={`px-2 py-0.5 rounded-full border font-bold ${s.data_quality<0.3?'bg-red-500/10 text-red-500 border-red-500/20':'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'}`}>Q {((s.data_quality||0)*100).toFixed(0)}%</span>
                </div>
              </GlassCard>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <GlassCard className="p-6 lg:col-span-2">
            <h3 className={`font-black text-[14px] mb-5 flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}>
              <div className="w-8 h-8 rounded-lg bg-[var(--accent)] text-[var(--bg)] flex items-center justify-center">
                <Activity size={14} />
              </div>
              Live Sources • Local Fast Scraper
              <span className="ui-pill-live text-[9px]">FIXED & THREADED</span>
            </h3>
            {raw ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-[11px]">
                {[
                  { label: 'Spot Tickers', value: `${raw.spot_tickers_count||0} + ${raw.coindcx_tickers_count||0} CoinDCX`, sub: `BTC $${raw.btc?.price?.toLocaleString?.() || 'N/A'} ${safeFixed(raw.btc?.change_pct,1)}% | CoinDCX ₹${raw.coindcx_btc?.price_inr?.toLocaleString?.() || raw.coindcx_btc?.price?.toLocaleString?.() || 'N/A'}`, icon: BarChart3 },
                  { label: 'Futures', value: `${raw.futures_count||0}`, sub: 'Perpetual', icon: TrendingDown },
                  { label: 'Funding Rates', value: `${raw.funding_count||0}`, sub: 'Funding flip detection', icon: Activity },
                  { label: 'Fear & Greed', value: `${raw.fear_greed?.value||50} ${raw.fear_greed?.classification||'Neutral'}`, sub: 'Panic detection', icon: Brain, color: raw.fear_greed?.value<25 ? 'text-red-500' : raw.fear_greed?.value<50 ? 'text-amber-500' : 'text-emerald-500' },
                  { label: 'Liquidations', value: `${Object.keys(raw.liquidations||{}).length} symbols`, sub: Object.entries(raw.liquidations||{}).slice(0,2).map(([k,v])=>`${k}: $${((v.total||0)/1e6).toFixed(1)}M`).join(' '), icon: AlertTriangle },
                  { label: 'Reddit + News', value: `${raw.reddit_count||0} posts, ${raw.news_count||0} news`, sub: `${raw.reddit_crash?.length || 0} crash posts, ${raw.news_crash?.length || 0} crash news`, icon: MessageSquare },
                ].map((item, i) => (
                  <div key={i} className={`group p-3 rounded-xl border transition-all hover:scale-[1.02] hover:shadow-md ${isLight ? 'bg-zinc-50 border-black/5 hover:bg-white hover:border-black/10' : 'bg-black/20 border-white/5 hover:bg-black/40 hover:border-[var(--accent)]/20'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <item.icon size={12} className="text-[var(--accent)]" />
                      <div className={`text-[10px] font-bold uppercase tracking-wide ${isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>{item.label}</div>
                    </div>
                    <div className={`font-black ${item.color || (isLight ? 'text-black' : 'text-white')}`}>{item.value}</div>
                    <div className={`text-[10px] mt-1 leading-tight ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>{item.sub}</div>
                  </div>
                ))}
              </div>
            ) : <div className={`text-[12px] p-4 rounded-xl border text-center ${isLight ? 'text-zinc-500 bg-zinc-50 border-black/5' : 'text-zinc-500 bg-white/5 border-white/5'}`}>No raw data - fetch failed, check network</div>}
            
            {raw?.reddit_crash?.length>0 && (
              <div className="mt-5">
                <div className={`text-[12px] font-black mb-2 flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}><MessageSquare size={14} className="text-orange-500" /> Crash Reddit • Early Signals</div>
                <div className="space-y-1.5">
                  {raw.reddit_crash.map((p,i)=><div key={i} className={`text-[11px] p-2 rounded-lg border truncate ${isLight ? 'text-zinc-700 bg-white border-black/5' : 'text-zinc-300 bg-black/20 border-white/5'}`}>• {p.title} <span className="text-emerald-500 font-bold">({p.score}↑)</span></div>)}
                </div>
              </div>
            )}
            {raw?.news_crash?.length>0 && (
              <div className="mt-4">
                <div className={`text-[12px] font-black mb-2 flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}><Newspaper size={14} className="text-red-500" /> Crash News • Panic Detection</div>
                <div className="space-y-1.5">
                  {raw.news_crash.map((n,i)=><div key={i} className={`text-[11px] p-2 rounded-lg border truncate ${isLight ? 'text-zinc-700 bg-white border-black/5' : 'text-zinc-300 bg-black/20 border-white/5'}`}>• {n.title}</div>)}
                </div>
              </div>
            )}
          </GlassCard>

          <div className="space-y-5">
            <GlassCard className="p-5">
              <h3 className={`font-black text-[13px] mb-4 flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}>
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-orange-500 to-red-500 text-white flex items-center justify-center">
                  <Shield size={14} />
                </div>
                Crash Alerts
                {alerts.length>0 && <span className="ui-pill-live text-[9px] animate-pulse">{alerts.length} ACTIVE</span>}
              </h3>
              {alerts.length===0 ? (
                <div className={`text-center py-8 rounded-xl border-2 border-dashed ${isLight ? 'text-zinc-500 bg-zinc-50 border-black/5' : 'text-zinc-500 bg-white/5 border-white/10'}`}>
                  <Shield size={24} className="mx-auto mb-2 opacity-50" />
                  <div className="text-[12px] font-medium">No HIGH/CRITICAL alerts</div>
                  <div className="text-[10px]">Market stable • {currentTheme.icon} {currentTheme.name} theme</div>
                </div>
              ) : (
                <div className="space-y-3">
                  {alerts.map((a,i)=>(
                    <div key={i} className={`group p-3 rounded-xl border text-[11px] transition-all hover:scale-[1.02] hover:shadow-md ${a.level==='CRITICAL' ? 'bg-red-500/10 border-red-500/20 hover:bg-red-500/15 hover:border-red-500/30' : 'bg-orange-500/10 border-orange-500/20 hover:bg-orange-500/15 hover:border-orange-500/30'}`}>
                      <div className="flex justify-between items-center">
                        <span className="font-black flex items-center gap-1.5">
                          <span className={`w-2 h-2 rounded-full ${a.level==='CRITICAL' ? 'bg-red-500 animate-pulse' : 'bg-orange-500'}`} />
                          {a.level} {safeFixed(a.risk,0)}%
                        </span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full bg-[var(--card)] border border-[var(--border)] ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>{a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : ''}</span>
                      </div>
                      <div className={`mt-2 leading-relaxed ${isLight ? 'text-zinc-700' : 'text-zinc-300'}`}>{a.summary?.slice(0,120) || ''}</div>
                    </div>
                  ))}
                </div>
              )}
            </GlassCard>

            <GlassCard className="p-5">
              <h3 className={`font-black text-[13px] mb-4 flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}>
                <div className="w-8 h-8 rounded-lg bg-[var(--accent)] text-[var(--bg)] flex items-center justify-center">
                  <BarChart3 size={14} />
                </div>
                History • {history.length}
              </h3>
              <div className="space-y-1 max-h-[240px] overflow-auto">
                {history.length===0 ? <div className={`text-[11px] text-center py-4 ${isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>No history yet</div> : history.map((h,i)=>(
                  <div key={i} className={`group flex justify-between items-center text-[11px] py-2 px-2 rounded-lg border-b last:border-0 hover:bg-[var(--accent-soft)] transition-colors ${isLight ? 'border-black/5' : 'border-white/5'}`}>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full bg-[var(--card)] border ${isLight ? 'text-zinc-500 border-black/5' : 'text-zinc-400 border-white/5'}`}>{h.timestamp ? new Date(h.timestamp).toLocaleTimeString() : ''}</span>
                    <span className={`font-black px-2 py-0.5 rounded-full text-[10px] ${h.level==='CRITICAL' ? 'bg-red-500 text-white' : h.level==='HIGH' ? 'bg-orange-500 text-black' : h.level==='MEDIUM' ? 'bg-amber-500 text-black' : 'bg-emerald-500 text-black'}`}>{safeFixed(h.crash_risk,0)}% {h.level}</span>
                    <span className={`font-bold mono ${h.btc_change<0 ? 'text-red-500' : 'text-emerald-500'}`}>{safeFixed(h.btc_change,1)}%</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>

        <GlassCard className="p-6">
          <h3 className={`font-black text-[13px] mb-3 flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}>
            <Zap size={14} className="text-[var(--accent)]" /> How Crash Detection Works • Before Market Impact
          </h3>
          <div className={`text-[11px] leading-relaxed space-y-2 ${isLight ? 'text-zinc-700' : 'text-zinc-300'}`}>
            <div className="grid md:grid-cols-2 gap-4">
              <div className={`p-3 rounded-xl border ${isLight ? 'bg-white border-black/5' : 'bg-black/20 border-white/5'}`}>
                <div className="font-bold text-emerald-500 mb-1">✅ Fixed Bugs</div>
                <div>Bare except → specific, fallback 100k → historical + last known, volatility sqrt(86400)→sqrt(365), slippage skips, p_value NaN, OI history, stablecoin flight, quality-weighted aggregation, thread locks, rate limit 60/min, Pydantic validation, cached fallback, safeFixed guards, {Object.keys(THEMES).length} themes support</div>
              </div>
              <div className={`p-3 rounded-xl border ${isLight ? 'bg-white border-black/5' : 'bg-black/20 border-white/5'}`}>
                <div className="font-bold text-[var(--accent)] mb-1">🎯 Detection Logic</div>
                <div>1. Orderbook imbalance bid drying 30-70% before crash 2. Whale sells {'>'}60% 3. Liquidations $1M-20M+ 4. Funding flip 5. Correlation 80%+ systemic 6. Volume spike + drop 7. Fear & Greed {'<'}25 8. News/Reddit crash keywords 9. Stablecoin flight BTC {'>'}7% + alt drops. All local Session reuse, ThreadPool 12, 3-5s timeouts, numpy {'<'}10ms, total {'<'}3s</div>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
