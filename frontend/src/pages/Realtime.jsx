import { useEffect, useState, useRef } from 'react'
import { api } from '../api/client'

export default function Realtime() {
  const [symbol, setSymbol] = useState('BTC-USD')
  const [price, setPrice] = useState(null)
  const [history, setHistory] = useState([])
  const [isLive, setIsLive] = useState(false)
  const intervalRef = useRef()

  const fetchPrice = async () => {
    try {
      const data = await api.getRealtimePrice(symbol)
      setPrice(data)
      setHistory(prev => [...prev.slice(-50), { time: new Date().toLocaleTimeString(), price: data.price || data.ticker?.lastPrice }])
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(()=>{
    fetchPrice()
    return ()=>clearInterval(intervalRef.current)
  }, [symbol])

  const toggleLive = () => {
    if (isLive) {
      clearInterval(intervalRef.current)
      setIsLive(false)
    } else {
      intervalRef.current = setInterval(fetchPrice, 2000)
      setIsLive(true)
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Realtime Binance Feed</h1>
        <div className="flex gap-2">
          <select value={symbol} onChange={e=>setSymbol(e.target.value)} className="bg-crypto-card border border-crypto-border rounded-lg px-3 py-2">
            {['BTC-USD','ETH-USD','SOL-USD','BNB-USD'].map(s=><option key={s}>{s}</option>)}
          </select>
          <button onClick={toggleLive} className={`${isLive ? 'bg-crypto-bear' : 'bg-crypto-bull'} text-black px-4 py-2 rounded-lg font-semibold`}>
            {isLive ? 'Stop Live' : 'Start Live (2s)'}
          </button>
          <button onClick={fetchPrice} className="btn-secondary">Refresh</button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="card col-span-2">
          <div className="text-gray-400 text-sm">Live Price ({price?.binance_symbol})</div>
          <div className="text-4xl font-bold mono">${parseFloat(price?.price || price?.ticker?.lastPrice || 0).toLocaleString()}</div>
          <div className="text-sm text-gray-400 mt-2">24h Change: {price?.ticker?.priceChangePercent}% | Volume: {parseFloat(price?.ticker?.volume || 0).toLocaleString()}</div>
          <div className="mt-6">
            <div className="text-sm font-semibold mb-2">Price History (live)</div>
            <div className="flex gap-1 h-20 items-end">
              {history.map((h,i)=>(
                <div key={i} className="flex-1 bg-crypto-accent rounded-t" style={{height: `${((h.price - Math.min(...history.map(x=>x.price)))/(Math.max(...history.map(x=>x.price))-Math.min(...history.map(x=>x.price))||1)*100)}%`, minHeight: '4px'}} title={`${h.time}: $${h.price}`}></div>
              ))}
            </div>
          </div>
        </div>
        <div className="card">
          <h3 className="font-semibold mb-3">Binance Ticker</h3>
          {price?.ticker ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-400">High</span><span className="mono">${parseFloat(price.ticker.highPrice).toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Low</span><span className="mono">${parseFloat(price.ticker.lowPrice).toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Open</span><span className="mono">${parseFloat(price.ticker.openPrice).toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Trades</span><span className="mono">{price.ticker.count}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Quote Vol</span><span className="mono">${(parseFloat(price.ticker.quoteVolume)/1e6).toFixed(2)}M</span></div>
            </div>
          ) : <div className="text-gray-500">No ticker</div>}
          <div className="mt-6 text-xs text-gray-500">
            WebSocket: wss://stream.binance.com:9443/ws/{symbol.replace('-','').toLowerCase()}@trade<br/>
            REST fallback used for demo. Full WS requires backend realtime manager.
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-3">How Realtime Works</h3>
        <div className="grid grid-cols-3 gap-4 text-sm text-gray-400">
          <div><span className="text-white font-medium">1. WebSocket</span><br/>Connects to Binance stream.binance.com for @trade and @kline_1m</div>
          <div><span className="text-white font-medium">2. Buffer</span><br/>Deque buffer 1000 trades, callbacks for live prediction</div>
          <div><span className="text-white font-medium">3. Live Signal</span><br/>LivePredictor merges live price with model forecast for real-time signal</div>
        </div>
      </div>
    </div>
  )
}
