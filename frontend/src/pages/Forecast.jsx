import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function Forecast() {
  const [symbol, setSymbol] = useState('BTC-USD')
  const [steps, setSteps] = useState(7)
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = () => {
    setLoading(true)
    api.getForecast(symbol, steps).then(setForecast).catch(e=>alert(e.message)).finally(()=>setLoading(false))
  }
  useEffect(()=>{load()}, [symbol, steps])

  const chartData = forecast?.dates?.map((d,i)=>({
    date: d,
    lstm: forecast.lstm?.[i],
    transformer: forecast.transformer?.[i],
    xgboost: forecast.xgboost?.[i],
    arima: forecast.arima?.[i],
    ensemble: forecast.ensemble?.[i]
  })) || []

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Forecast</h1>
        <div className="flex gap-2">
          <select value={symbol} onChange={e=>setSymbol(e.target.value)} className="bg-crypto-card border border-crypto-border rounded-lg px-3 py-2">
            {['BTC-USD','ETH-USD','SOL-USD','BNB-USD','XRP-USD'].map(s=><option key={s}>{s}</option>)}
          </select>
          <select value={steps} onChange={e=>setSteps(parseInt(e.target.value))} className="bg-crypto-card border border-crypto-border rounded-lg px-3 py-2">
            {[7,14,21,30].map(n=><option key={n} value={n}>{n} days</option>)}
          </select>
          <button onClick={load} className="btn-primary">Refresh</button>
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-4">Ensemble Forecast ({steps}d) - Current: ${forecast?.current_price?.toFixed(2)}</h3>
        {loading ? <div>Loading...</div> : (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <XAxis dataKey="date" stroke="#6b7280" />
              <YAxis stroke="#6b7280" domain={['auto','auto']} />
              <Tooltip contentStyle={{background:'#151a21', border:'1px solid #232a34'}} />
              <Legend />
              <Line type="monotone" dataKey="lstm" stroke="#00b7eb" dot={false} strokeDasharray="5 5" />
              <Line type="monotone" dataKey="transformer" stroke="#f59e0b" dot={false} strokeWidth={2} />
              <Line type="monotone" dataKey="xgboost" stroke="#8b5cf6" dot={false} />
              <Line type="monotone" dataKey="arima" stroke="#6b7280" dot={false} />
              <Line type="monotone" dataKey="ensemble" stroke="#00d395" dot={false} strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {forecast && (
        <div className="card">
          <h3 className="font-semibold mb-3">Detailed Forecast Table</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-gray-400 border-b border-crypto-border">
                <tr><th className="text-left p-2">Date</th><th>LSTM</th><th>Transformer</th><th>XGBoost</th><th>ARIMA</th><th>Ensemble</th></tr>
              </thead>
              <tbody>
                {chartData.map((row,i)=>(
                  <tr key={i} className="border-b border-crypto-border/50">
                    <td className="p-2">{row.date}</td>
                    <td className="p-2 mono">${row.lstm?.toFixed(2) || '-'}</td>
                    <td className="p-2 mono">${row.transformer?.toFixed(2) || '-'}</td>
                    <td className="p-2 mono">${row.xgboost?.toFixed(2) || '-'}</td>
                    <td className="p-2 mono">${row.arima?.toFixed(2) || '-'}</td>
                    <td className="p-2 mono font-bold text-crypto-accent">${row.ensemble?.toFixed(2) || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
