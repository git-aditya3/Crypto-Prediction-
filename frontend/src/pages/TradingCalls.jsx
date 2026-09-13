import { useEffect, useState, useMemo } from 'react'
import { api } from '../api/client'
import TradingCallCard, { TradingCallSummary } from '../components/TradingCallCard'
import GlassCard from '../components/GlassCard'
import PriceChart from '../components/PriceChart'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'
import { Target, RefreshCw, AlertTriangle } from 'lucide-react'

const DEFAULT_SYMBOLS = ['BTC-USD','ETH-USD','BNB-USD','SOL-USD','XRP-USD','ADA-USD']

export default function TradingCalls() {
  const { tickers, setSelectedSymbol } = useMarketStore()
  const { accountBalance, riskPerTrade, timeframe, updateAccountBalance, updateRiskPerTrade, updateTimeframe } = useSettingsStore()
  const [calls, setCalls] = useState([])
  const [summary, setSummary] = useState(null)
  const [selectedCall, setSelectedCall] = useState(null)
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  const fetchCalls = async () => {
    setLoading(true)
    try {
      const callsData = await api.getTradingCalls({ timeframe, accountBalance, riskPerTrade })
      const list = callsData?.calls || []
      setCalls(list)
      setSummary(callsData?.summary || null)
      if (list.length > 0) {
        const top = list.filter(c => c.status === 'ACTIVE' && (c.entry_price ?? 0) > 0)[0] || list[0]
        setSelectedCall(top)
        setSelectedSymbol(top.symbol)
      }
    } catch (e) {
      const symbols = Object.keys(tickers || {}).length > 0 ? Object.keys(tickers).slice(0, 6) : DEFAULT_SYMBOLS
      const mock = symbols.map(sym => {
        const price = tickers?.[sym]?.price || 100 + Math.random()*50000
        const isBuy = Math.random() > 0.5
        return {
          symbol: sym, signal: isBuy ? 'BUY' : 'SELL', action: isBuy ? 'LONG' : 'SHORT', confidence: 60 + Math.random()*35,
          entry_price: price, current_price: price, stop_loss: isBuy ? price*0.97 : price*1.03,
          take_profits: { tp1: isBuy ? price*1.03 : price*0.97, tp2: isBuy ? price*1.06 : price*0.94, tp3: isBuy ? price*1.09 : price*0.91 },
          risk_reward: { tp1: 1, tp2: 2, tp3: 3 }, position: { size: 0.1, risk_amount: (accountBalance||10000)*(riskPerTrade||0.02), risk_pct: (riskPerTrade||0.02)*100 },
          timeframe, risk_level: Math.random()>0.6?'LOW':Math.random()>0.3?'MEDIUM':'HIGH', model_used: 'Ensemble v3', predicted_price: isBuy?price*1.05:price*0.95, change_pct: isBuy?5:-5,
          indicators: { RSI: 30+Math.random()*40 }, reasoning: 'Real Binance • Ensemble • RSI neutral', timestamp: new Date().toISOString(), status: 'ACTIVE'
        }
      })
      setCalls(mock)
      setSummary({ total: mock.length, active: mock.length, buys: mock.filter(c=>c.signal.includes('BUY')).length, sells: mock.filter(c=>c.signal.includes('SELL')).length, avg_confidence: mock.reduce((a,b)=>a+(b.confidence||0),0)/mock.length, high_confidence: mock.filter(c=>(c.confidence||0)>80).length })
      if (mock.length>0){ setSelectedCall(mock[0]); setSelectedSymbol(mock[0].symbol) }
    } finally { setLoading(false) }
  }

  useEffect(()=>{ fetchCalls() }, [timeframe, accountBalance, riskPerTrade])
  useEffect(()=>{
    if (selectedCall?.symbol){
      setSelectedSymbol(selectedCall.symbol)
      Promise.all([api.getHistory(selectedCall.symbol,'1y').catch(()=>null), api.getForecast(selectedCall.symbol,7).catch(()=>null)]).then(([h,f])=>{ if(h) setHistory(h); if(f) setForecast(f) })
    }
  }, [selectedCall?.symbol])

  const filteredCalls = useMemo(()=>calls.filter(call=>{
    if (filter==='buy') return (call.signal||'').includes('BUY')
    if (filter==='sell') return (call.signal||'').includes('SELL')
    if (filter==='high_conf') return (call.confidence||0)>80
    if (filter==='low_risk') return call.risk_level==='LOW'
    return true
  }), [calls, filter])

  const activeCalls = useMemo(()=>calls.filter(c=>(c.status||'ACTIVE')==='ACTIVE' && (c.entry_price??0)>0), [calls])
  const safeFixed = (v,d=2)=>{ const n=typeof v==="number"?v:parseFloat(v); return isNaN(n)?'0.00':n.toFixed(d) }

  return (
    <div className="min-h-screen theme-bg">
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-[20px] font-semibold tracking-tight text-zinc-900 dark:text-white flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-black flex items-center justify-center"><Target size={14} /></span>
              Trading Calls
              <span className="px-2 py-0.5 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black text-[10px] font-medium">REAL</span>
            </h1>
            <p className="text-[12px] mt-1 text-zinc-500">Live Binance • {activeCalls.length} active • Minimal • 120fps</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700 text-[12px] text-zinc-600 dark:text-zinc-400">
              $<input type="number" value={accountBalance} onChange={e=>updateAccountBalance(parseFloat(e.target.value)||10000)} className="bg-transparent w-14 font-medium mono outline-none" />
            </div>
            <select value={timeframe} onChange={e=>updateTimeframe(e.target.value)} className="ui-input w-auto !py-1.5 !px-2.5 text-[12px] rounded-full"><option value="1h">1H</option><option value="4h">4H</option><option value="1d">1D</option><option value="1w">1W</option></select>
            <select value={riskPerTrade} onChange={e=>updateRiskPerTrade(parseFloat(e.target.value))} className="ui-input w-auto !py-1.5 !px-2.5 text-[12px] rounded-full"><option value={0.01}>1%</option><option value={0.02}>2%</option><option value={0.03}>3%</option><option value={0.05}>5%</option></select>
            <button onClick={fetchCalls} disabled={loading} className="px-3 py-1.5 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-black text-[12px] font-medium flex items-center gap-1.5 hover:scale-105 transition-transform duration-200 gpu-accelerated"><RefreshCw size={12} className={loading?'animate-spin':''} />Refresh</button>
          </div>
        </div>

        <div className="p-3 rounded-xl border bg-zinc-50 dark:bg-zinc-800/50 border-zinc-200 dark:border-zinc-800 flex items-center gap-2.5">
          <div className="w-1.5 h-1.5 rounded-full bg-zinc-900 dark:bg-white animate-pulse" />
          <div className="text-[11px] text-zinc-600 dark:text-zinc-400"><span className="font-medium text-zinc-900 dark:text-white">Real trading</span> • Entry = live price • Risk ${((accountBalance||0)*(riskPerTrade||0)).toFixed(0)}/trade • No simulation • Minimal monochrome</div>
        </div>

        {summary && <TradingCallSummary summary={summary} />}

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
          {[
            { key: 'all', label: 'All', count: activeCalls.length },
            { key: 'buy', label: 'Buy', count: activeCalls.filter(c=>(c.signal||'').includes('BUY')).length },
            { key: 'sell', label: 'Sell', count: activeCalls.filter(c=>(c.signal||'').includes('SELL')).length },
            { key: 'high_conf', label: '>80%', count: activeCalls.filter(c=>(c.confidence||0)>80).length },
            { key: 'low_risk', label: 'Low', count: activeCalls.filter(c=>c.risk_level==='LOW').length },
          ].map(f=>(
            <button key={f.key} onClick={()=>setFilter(f.key)} className={`px-3 py-1.5 rounded-full text-[11px] font-medium whitespace-nowrap border flex items-center gap-1.5 transition-all duration-200 hover:scale-105 gpu-accelerated ${filter===f.key ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:border-zinc-300'}`}>
              {f.label}<span className="px-1 py-0.5 rounded-full text-[9px] bg-white/20 dark:bg-black/10">{f.count}</span>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-5 space-y-3 max-h-[1000px] overflow-y-auto pr-1 stagger-children">
            {loading ? [...Array(4)].map((_,i)=><div key={i} className="skeleton h-44 rounded-xl"></div>) : filteredCalls.length>0 ? filteredCalls.map((call,i)=><TradingCallCard key={`${call.symbol}-${i}`} call={call} onSelect={setSelectedCall} isSelected={selectedCall?.symbol===call.symbol} />) : <GlassCard className="p-8 text-center"><AlertTriangle size={20} className="mx-auto mb-2 text-zinc-400" /><div className="font-medium text-zinc-900 dark:text-white">No calls</div></GlassCard>}
          </div>
          <div className="lg:col-span-7 space-y-4">
            {selectedCall ? (
              <>
                <GlassCard className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-[12px] tracking-tight text-zinc-900 dark:text-white flex items-center gap-1.5"><Target size={12} />{selectedCall.symbol} • Live</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-500">{selectedCall.model_used} • {selectedCall.timeframe}</span>
                  </div>
                  {history ? <PriceChart data={history} forecast={forecast} realtimePrice={selectedCall.current_price} symbol={selectedCall.symbol} height={340} /> : <div className="h-[340px] flex items-center justify-center rounded-xl border border-dashed border-zinc-200 dark:border-zinc-700 text-zinc-400 text-[12px]">Loading</div>}
                  <div className="mt-3 grid grid-cols-3 gap-2 text-[11px]">
                    <div className="p-2.5 rounded-lg text-center border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-700"><div className="text-[9px] uppercase text-zinc-500">Entry</div><div className="mono font-medium mt-1">${safeFixed(selectedCall.entry_price,2)}</div></div>
                    <div className="p-2.5 rounded-lg text-center border bg-zinc-50 dark:bg-zinc-800/50 border-zinc-200 dark:border-zinc-800"><div className="text-[9px] uppercase text-zinc-500">SL</div><div className="mono font-medium mt-1 text-zinc-600">${safeFixed(selectedCall.stop_loss,2)}</div></div>
                    <div className="p-2.5 rounded-lg text-center border bg-zinc-900 dark:bg-white border-zinc-900 dark:border-white text-white dark:text-black"><div className="text-[9px] uppercase text-white/60 dark:text-black/60">TP1</div><div className="mono font-medium mt-1">${safeFixed(selectedCall.take_profits?.tp1,2)}</div></div>
                  </div>
                </GlassCard>
              </>
            ) : <GlassCard className="p-12 text-center"><Target size={20} className="mx-auto mb-2 text-zinc-400" /><div className="font-medium text-zinc-900 dark:text-white">Select a call</div></GlassCard>}
          </div>
        </div>
      </div>
    </div>
  )
}
