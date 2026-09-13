import { useEffect, useState } from 'react'
import { api } from '../api/client'
import PriceChart from '../components/PriceChart'
import { TrendingUp, TrendingDown, Activity, Zap } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export default function Dashboard() {
  const [symbol, setSymbol] = useState('BTC-USD')
  const [symbols, setSymbols] = useState([])
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [signal, setSignal] = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getSymbols().then(d => setSymbols(d.symbols || [])).catch(()=>setSymbols(['BTC-USD','ETH-USD','SOL-USD']))
  }, [])

  useEffect(() => {
    setLoading(true)
    Promise.allSettled([
      api.getHistory(symbol, '1y'),
      api.getForecast(symbol, 7).catch(()=>null),
      api.getSignal(symbol).catch(()=>null),
      api.getSentiment(symbol, 14).catch(()=>null)
    ]).then(([h,f,s,sent]) => {
      if (h.status==='fulfilled') setHistory(h.value)
      if (f.status==='fulfilled') setForecast(f.value)
      if (s.status==='fulfilled') setSignal(s.value)
      if (sent.status==='fulfilled') setSentiment(sent.value)
      setLoading(false)
    })
  }, [symbol])

  if (loading) return <div className="p-10 text-center">Loading {symbol}...</div>

  const currentPrice = history?.close?.[history.close.length-1] || 0
  const prevPrice = history?.close?.[history.close.length-2] || currentPrice
  const changePct = ((currentPrice - prevPrice)/prevPrice*100).toFixed(2)

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <select value={symbol} onChange={e=>setSymbol(e.target.value)} className="bg-crypto-card border border-crypto-border rounded-lg px-4 py-2">
          {symbols.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="card">
          <div className="text-gray-400 text-sm">Price</div>
          <div className="text-2xl font-bold mono">${currentPrice.toLocaleString()}</div>
          <div className={`flex items-center gap-1 text-sm ${parseFloat(changePct)>=0 ? 'text-crypto-bull' : 'text-crypto-bear'}`}>
            {parseFloat(changePct)>=0 ? <TrendingUp size={14}/> : <TrendingDown size={14}/>} {changePct}%
          </div>
        </div>
        <div className="card">
          <div className="text-gray-400 text-sm">Signal</div>
          <div className={`text-xl font-bold ${signal?.signal?.includes('BUY') ? 'text-crypto-bull' : signal?.signal?.includes('SELL') ? 'text-crypto-bear' : 'text-gray-300'}`}>{signal?.signal || 'HOLD'}</div>
          <div className="text-sm text-gray-400">{signal?.confidence}% confidence</div>
        </div>
        <div className="card">
          <div className="text-gray-400 text-sm">Sentiment</div>
          <div className="text-xl font-bold">{sentiment?.average_compound ? (sentiment.average_compound*100).toFixed(1) : '0'}%</div>
          <div className="text-sm text-gray-400">{sentiment?.daily?.length || 0} sources</div>
        </div>
        <div className="card">
          <div className="text-gray-400 text-sm">Forecast (7d)</div>
          <div className="text-xl font-bold mono">${forecast?.ensemble?.[6]?.toFixed(2) || '-'}</div>
          <div className="text-sm text-gray-400">Ensemble prediction</div>
        </div>
      </div>

      {history && <PriceChart data={history} forecast={forecast} />}

      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <h3 className="font-semibold mb-3 flex items-center gap-2"><Zap size={16} className="text-crypto-accent"/> Model Predictions</h3>
          {forecast ? (
            <div className="space-y-2">
              {['lstm','transformer','xgboost','arima','ensemble'].map(m => forecast[m] && (
                <div key={m} className="flex justify-between text-sm">
                  <span className="uppercase text-gray-400">{m}</span>
                  <span className="mono font-medium">${forecast[m][0]?.toFixed(2)} → ${forecast[m][forecast[m].length-1]?.toFixed(2)}</span>
                </div>
              ))}
            </div>
          ) : <div className="text-gray-500">No models trained. Run training script.</div>}
        </div>

        <div className="card">
          <h3 className="font-semibold mb-3 flex items-center gap-2"><Activity size={16} className="text-crypto-accent2"/> Sentiment Trend</h3>
          {sentiment?.daily?.length ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={sentiment.daily}>
                <XAxis dataKey="date" hide />
                <YAxis domain={[-1,1]} />
                <Tooltip />
                <Line type="monotone" dataKey="compound" stroke="#00d395" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <div className="text-gray-500">No sentiment data</div>}
        </div>
      </div>
    </div>
  )
}
