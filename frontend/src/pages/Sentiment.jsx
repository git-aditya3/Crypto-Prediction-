import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

export default function Sentiment() {
  const [symbol, setSymbol] = useState('BTC-USD')
  const [data, setData] = useState(null)
  const [text, setText] = useState('')
  const [analysis, setAnalysis] = useState(null)

  useEffect(()=>{
    api.getSentiment(symbol, 30).then(setData).catch(console.error)
  }, [symbol])

  const analyze = () => {
    if (!text) return
    api.analyzeSentiment(text).then(setAnalysis).catch(console.error)
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Sentiment Analysis</h1>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 card">
          <h3 className="font-semibold mb-3">Daily Sentiment (News + Reddit)</h3>
          <div className="flex gap-2 mb-4">
            <select value={symbol} onChange={e=>setSymbol(e.target.value)} className="bg-crypto-bg border border-crypto-border rounded-lg px-3 py-2">
              {['BTC-USD','ETH-USD','SOL-USD','ETH-USD'].map(s=><option key={s}>{s}</option>)}
            </select>
            <span className="text-sm text-gray-400 py-2">Avg: {data?.average_compound?.toFixed(3) || 0}</span>
          </div>
          {data?.daily ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.daily}>
                <XAxis dataKey="date" stroke="#6b7280" />
                <YAxis domain={[-1,1]} stroke="#6b7280" />
                <Tooltip contentStyle={{background:'#151a21', border:'1px solid #232a34'}} />
                <Line type="monotone" dataKey="compound" stroke="#00d395" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <div className="text-gray-500">Loading...</div>}
        </div>

        <div className="card">
          <h3 className="font-semibold mb-3">Analyze Custom Text</h3>
          <textarea value={text} onChange={e=>setText(e.target.value)} placeholder="e.g. Bitcoin is extremely bullish, going to the moon!" className="w-full bg-crypto-bg border border-crypto-border rounded-lg p-3 h-24 text-sm" />
          <button onClick={analyze} className="btn-primary w-full mt-3">Analyze</button>
          {analysis && (
            <div className="mt-4 p-3 bg-crypto-bg rounded-lg">
              <div className="text-sm">Compound: <span className={`font-bold ${analysis.sentiment.compound>0 ? 'text-crypto-bull' : 'text-crypto-bear'}`}>{analysis.sentiment.compound?.toFixed(3)}</span></div>
              <div className="text-xs text-gray-400 mt-1">Pos: {analysis.sentiment.pos?.toFixed(2)} Neg: {analysis.sentiment.neg?.toFixed(2)}</div>
            </div>
          )}
          <div className="mt-6 text-xs text-gray-500">
            <p className="font-semibold mb-1">Sources:</p>
            <ul className="list-disc ml-4 space-y-1">
              <li>CryptoPanic News (if API key)</li>
              <li>Reddit r/CryptoCurrency, r/Bitcoin</li>
              <li>CoinGecko trending fallback</li>
              <li>VADER-like lexicon + optional FinBERT</li>
            </ul>
          </div>
        </div>
      </div>

      {data?.daily && (
        <div className="card">
          <h3 className="font-semibold mb-3">Sentiment Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.daily}>
              <XAxis dataKey="date" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip contentStyle={{background:'#151a21', border:'1px solid #232a34'}} />
              <Bar dataKey="pos" stackId="a" fill="#00d395" name="Positive" />
              <Bar dataKey="neg" stackId="a" fill="#ff4b4b" name="Negative" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
