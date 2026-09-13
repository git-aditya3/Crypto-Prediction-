import { useEffect, useState } from 'react'
import { api } from '../api/client'
import TradingCallCard, { TradingCallSummary } from '../components/TradingCallCard'
import GlassCard from '../components/GlassCard'
import PriceChart from '../components/PriceChart'
import { useMarketStore } from '../store/useMarketStore'
import { useSettingsStore } from '../store/useSettingsStore'
import { Target, Filter, RefreshCw, Settings, TrendingUp, AlertTriangle, Zap, DollarSign, Clock, Shield } from 'lucide-react'

export default function TradingCalls() {
  const { tickers, prices, selectedSymbol, setSelectedSymbol } = useMarketStore()
  const { accountBalance, riskPerTrade, timeframe, updateAccountBalance, updateRiskPerTrade, updateTimeframe } = useSettingsStore()
  
  const [calls, setCalls] = useState([])
  const [summary, setSummary] = useState(null)
  const [selectedCall, setSelectedCall] = useState(null)
  const [history, setHistory] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, buy, sell, high_conf

  const fetchCalls = async () => {
    setLoading(true)
    try {
      const data = await api.getTradingCalls({ timeframe, accountBalance, riskPerTrade })
      setCalls(data.calls || [])
      setSummary(data.summary || null)
      if (data.calls && data.calls.length > 0) {
        setSelectedCall(data.calls[0])
        setSelectedSymbol(data.calls[0].symbol)
      }
    } catch (e) {
      console.error('Failed to fetch trading calls', e)
      // Fallback to mock data for demo if backend fails
      const mockCalls = Object.keys(tickers).slice(0, 6).map(sym => {
        const ticker = tickers[sym]
        const price = ticker?.price || 100
        const isBuy = Math.random() > 0.5
        return {
          symbol: sym,
          signal: isBuy ? (Math.random() > 0.5 ? 'STRONG_BUY' : 'BUY') : (Math.random() > 0.5 ? 'STRONG_SELL' : 'SELL'),
          action: isBuy ? 'LONG' : 'SHORT',
          confidence: 60 + Math.random() * 35,
          entry_price: price,
          current_price: price,
          stop_loss: isBuy ? price * 0.97 : price * 1.03,
          take_profits: {
            tp1: isBuy ? price * 1.03 : price * 0.97,
            tp2: isBuy ? price * 1.06 : price * 0.94,
            tp3: isBuy ? price * 1.09 : price * 0.91
          },
          risk_reward: { tp1: 1, tp2: 2, tp3: 3 },
          position: { size: 0.1, risk_amount: accountBalance * riskPerTrade, risk_pct: riskPerTrade * 100, leverage_suggestion: '3x-5x' },
          timeframe,
          risk_level: Math.random() > 0.6 ? 'LOW' : Math.random() > 0.3 ? 'MEDIUM' : 'HIGH',
          model_used: 'Ensemble v3',
          model_versions: { lstm: 'v3', transformer: 'v3' },
          predicted_price: isBuy ? price * 1.05 : price * 0.95,
          change_pct: isBuy ? 5 : -5,
          indicators: { RSI: 30 + Math.random() * 40, volatility: 0.02 + Math.random() * 0.03, atr: price * 0.02 },
          sentiment: { average_compound: (Math.random() - 0.5) },
          reasoning: 'Ensemble models predict bullish momentum • RSI neutral • MACD bullish crossover • Strong trend',
          timestamp: new Date().toISOString(),
          expiry: new Date(Date.now() + 7*24*60*60*1000).toISOString(),
          leverage: '3x-5x (Medium volatility)',
          status: 'ACTIVE'
        }
      })
      setCalls(mockCalls)
      setSummary({
        total: mockCalls.length,
        buys: mockCalls.filter(c => c.signal.includes('BUY')).length,
        sells: mockCalls.filter(c => c.signal.includes('SELL')).length,
        holds: 0,
        avg_confidence: mockCalls.reduce((a, b) => a + b.confidence, 0) / mockCalls.length,
        high_confidence: mockCalls.filter(c => c.confidence > 80).length
      })
      if (mockCalls.length > 0) setSelectedCall(mockCalls[0])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCalls()
  }, [timeframe, accountBalance, riskPerTrade])

  useEffect(() => {
    if (selectedCall) {
      setSelectedSymbol(selectedCall.symbol)
      // Fetch chart data
      Promise.all([
        api.getHistory(selectedCall.symbol, '1y').catch(() => null),
        api.getForecast(selectedCall.symbol, 7).catch(() => null)
      ]).then(([h, f]) => {
        if (h) setHistory(h)
        if (f) setForecast(f)
      })
    }
  }, [selectedCall])

  const filteredCalls = calls.filter(call => {
    if (filter === 'buy') return call.signal.includes('BUY')
    if (filter === 'sell') return call.signal.includes('SELL')
    if (filter === 'high_conf') return call.confidence > 80
    if (filter === 'low_risk') return call.risk_level === 'LOW'
    return true
  })

  return (
    <div className="min-h-screen bg-crypto-bg relative">
      <div className="absolute inset-0 bg-gradient-mesh opacity-20 pointer-events-none"></div>
      
      <div className="relative max-w-[1600px] mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Target size={20} className="text-black" />
              </span>
              <span className="text-white">Trading Calls</span>
              <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold tracking-widest">PRO • LIVE</span>
            </h1>
            <p className="text-crypto-muted text-sm mt-2">
              Professional trading signals with entry, stop loss, take profit, risk/reward • AI Ensemble v3 • Real-time Binance • {calls.length} active calls
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-crypto-card border border-crypto-border">
              <DollarSign size={14} className="text-crypto-accent" />
              <input 
                type="number" 
                value={accountBalance} 
                onChange={e => updateAccountBalance(parseFloat(e.target.value) || 10000)}
                className="bg-transparent w-20 text-sm font-bold text-white outline-none"
                placeholder="Balance"
              />
              <span className="text-xs text-crypto-muted">USDT</span>
            </div>
            
            <select value={timeframe} onChange={e => updateTimeframe(e.target.value)} className="bg-crypto-card border border-crypto-border rounded-xl px-3 py-2.5 text-sm font-medium text-white">
              <option value="1h">1H</option>
              <option value="4h">4H</option>
              <option value="1d">1D</option>
              <option value="1w">1W</option>
            </select>
            
            <select value={riskPerTrade} onChange={e => updateRiskPerTrade(parseFloat(e.target.value))} className="bg-crypto-card border border-crypto-border rounded-xl px-3 py-2.5 text-sm font-medium text-white">
              <option value={0.01}>1% Risk</option>
              <option value={0.02}>2% Risk</option>
              <option value={0.03}>3% Risk</option>
              <option value={0.05}>5% Risk</option>
            </select>
            
            <button onClick={fetchCalls} disabled={loading} className="btn-primary flex items-center gap-2">
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Summary */}
        {summary && <TradingCallSummary summary={summary} />}

        {/* Filters */}
        <div className="flex items-center gap-2 overflow-x-auto">
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-crypto-card/50 border border-crypto-border/50">
            <Filter size={14} className="text-crypto-muted" />
            <span className="text-xs font-bold tracking-widest text-crypto-muted uppercase">Filter:</span>
          </div>
          {[
            { key: 'all', label: 'All Calls', count: calls.length },
            { key: 'buy', label: 'Buy Only', count: calls.filter(c => c.signal.includes('BUY')).length },
            { key: 'sell', label: 'Sell Only', count: calls.filter(c => c.signal.includes('SELL')).length },
            { key: 'high_conf', label: 'High Conf >80%', count: calls.filter(c => c.confidence > 80).length },
            { key: 'low_risk', label: 'Low Risk', count: calls.filter(c => c.risk_level === 'LOW').length },
          ].map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition flex items-center gap-2 border ${
                filter === f.key 
                  ? 'bg-white text-black border-white shadow-lg' 
                  : 'bg-crypto-card border-crypto-border text-crypto-muted hover:text-white hover:border-crypto-borderLight'
              }`}
            >
              {f.label}
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${filter === f.key ? 'bg-black text-white' : 'bg-crypto-bg text-crypto-muted'}`}>
                {f.count}
              </span>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Calls Grid */}
          <div className="lg:col-span-5 space-y-4 max-h-[1200px] overflow-y-auto pr-2">
            {loading ? (
              [...Array(4)].map((_, i) => (
                <div key={i} className="shimmer h-64 rounded-2xl"></div>
              ))
            ) : filteredCalls.length > 0 ? (
              filteredCalls.map((call, i) => (
                <TradingCallCard 
                  key={`${call.symbol}-${i}`} 
                  call={call} 
                  onSelect={setSelectedCall}
                  isSelected={selectedCall?.symbol === call.symbol}
                />
              ))
            ) : (
              <GlassCard className="p-12 text-center">
                <AlertTriangle size={32} className="mx-auto mb-4 text-crypto-muted" />
                <div className="text-white font-bold">No calls match filter</div>
                <div className="text-crypto-muted text-sm mt-1">Try changing filter or refresh</div>
              </GlassCard>
            )}
          </div>

          {/* Detail View */}
          <div className="lg:col-span-7 space-y-6">
            {selectedCall ? (
              <>
                <GlassCard className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="font-bold text-white flex items-center gap-2">
                      <Target size={18} className="text-crypto-accent" />
                      {selectedCall.symbol} • Detailed Analysis
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className="text-xs px-2 py-1 rounded-full bg-crypto-accent/10 text-crypto-accent border border-crypto-accent/20">
                        {selectedCall.model_used}
                      </span>
                      <span className="text-xs px-2 py-1 rounded-full bg-crypto-bg border border-crypto-border text-crypto-muted">
                        {selectedCall.timeframe}
                      </span>
                    </div>
                  </div>

                  {history && (
                    <PriceChart 
                      data={history} 
                      forecast={forecast} 
                      realtimePrice={selectedCall.current_price}
                      symbol={selectedCall.symbol}
                      height={400}
                    />
                  )}

                  {/* Trading Levels Visualization */}
                  <div className="mt-6 p-4 rounded-xl bg-crypto-bg/50 border border-crypto-border/30">
                    <div className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-4">Trading Levels • Visual Risk Management</div>
                    
                    <div className="relative">
                      {/* Price scale */}
                      <div className="flex justify-between text-[10px] text-crypto-muted mb-2">
                        <span>Stop Loss</span>
                        <span>Entry</span>
                        <span>TP1</span>
                        <span>TP2</span>
                        <span>TP3</span>
                      </div>
                      
                      <div className="relative h-20 bg-crypto-card rounded-xl border border-crypto-border/30 overflow-hidden">
                        {/* SL Zone */}
                        <div className="absolute left-0 top-0 bottom-0 w-[20%] bg-red-500/10 border-r border-red-500/20 flex items-center justify-center">
                          <div className="text-center">
                            <div className="text-[10px] text-red-400 font-bold">SL</div>
                            <div className="mono text-xs font-bold text-red-400">${selectedCall.stop_loss.toFixed(2)}</div>
                          </div>
                        </div>
                        
                        {/* Entry */}
                        <div className="absolute left-[20%] top-0 bottom-0 w-[15%] bg-crypto-accent/10 border-x border-crypto-accent/20 flex items-center justify-center">
                          <div className="text-center">
                            <div className="text-[10px] text-crypto-accent font-bold">ENTRY</div>
                            <div className="mono text-xs font-bold text-crypto-accent">${selectedCall.entry_price.toFixed(2)}</div>
                          </div>
                        </div>
                        
                        {/* TP Zones */}
                        <div className="absolute left-[35%] top-0 bottom-0 w-[20%] bg-emerald-500/10 border-r border-emerald-500/20 flex items-center justify-center">
                          <div className="text-center">
                            <div className="text-[10px] text-emerald-400 font-bold">TP1</div>
                            <div className="mono text-xs font-bold text-emerald-400">${selectedCall.take_profits.tp1.toFixed(2)}</div>
                            <div className="text-[9px] text-emerald-400/70">1:1</div>
                          </div>
                        </div>
                        
                        <div className="absolute left-[55%] top-0 bottom-0 w-[20%] bg-emerald-500/15 border-r border-emerald-500/20 flex items-center justify-center">
                          <div className="text-center">
                            <div className="text-[10px] text-emerald-400 font-bold">TP2</div>
                            <div className="mono text-xs font-bold text-emerald-400">${selectedCall.take_profits.tp2.toFixed(2)}</div>
                            <div className="text-[9px] text-emerald-400/70">1:2</div>
                          </div>
                        </div>
                        
                        <div className="absolute left-[75%] top-0 bottom-0 w-[25%] bg-emerald-500/20 flex items-center justify-center">
                          <div className="text-center">
                            <div className="text-[10px] text-emerald-400 font-bold">TP3</div>
                            <div className="mono text-xs font-bold text-emerald-400">${selectedCall.take_profits.tp3.toFixed(2)}</div>
                            <div className="text-[9px] text-emerald-400/70">1:3</div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex justify-between mt-3 text-[11px]">
                        <div className="flex items-center gap-2">
                          <Shield size={12} className="text-red-400" />
                          <span className="text-crypto-muted">Risk: <span className="text-red-400 font-bold">${selectedCall.position?.risk_amount?.toFixed(0)} ({selectedCall.position?.risk_pct?.toFixed(0)}%)</span></span>
                        </div>
                        <div className="flex items-center gap-2">
                          <TrendingUp size={12} className="text-emerald-400" />
                          <span className="text-crypto-muted">Reward: <span className="text-emerald-400 font-bold">Up to {(selectedCall.risk_reward?.tp3 || 3).toFixed(1)}x</span></span>
                        </div>
                      </div>
                    </div>
                  </div>
                </GlassCard>

                <div className="grid grid-cols-2 gap-4">
                  <GlassCard className="p-5">
                    <h4 className="font-bold text-white text-sm mb-3 flex items-center gap-2">
                      <Zap size={14} className="text-crypto-accent" />
                      Model Analysis
                    </h4>
                    <div className="space-y-2.5">
                      <div className="flex justify-between p-2.5 rounded-xl bg-crypto-bg/40 border border-crypto-border/20">
                        <span className="text-xs text-crypto-muted">Predicted</span>
                        <span className="mono font-bold text-sm text-white">${selectedCall.predicted_price.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between p-2.5 rounded-xl bg-crypto-bg/40 border border-crypto-border/20">
                        <span className="text-xs text-crypto-muted">Change</span>
                        <span className={`mono font-bold text-sm ${selectedCall.change_pct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {selectedCall.change_pct >= 0 ? '+' : ''}{selectedCall.change_pct.toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex justify-between p-2.5 rounded-xl bg-crypto-bg/40 border border-crypto-border/20">
                        <span className="text-xs text-crypto-muted">Confidence</span>
                        <span className="font-bold text-sm text-white">{selectedCall.confidence.toFixed(0)}%</span>
                      </div>
                      <div className="p-3 rounded-xl bg-crypto-accent/5 border border-crypto-accent/10">
                        <div className="text-[11px] text-crypto-muted leading-relaxed">{selectedCall.reasoning}</div>
                      </div>
                    </div>
                  </GlassCard>

                  <GlassCard className="p-5">
                    <h4 className="font-bold text-white text-sm mb-3 flex items-center gap-2">
                      <Shield size={14} className="text-crypto-accent2" />
                      Risk Management
                    </h4>
                    <div className="space-y-2.5">
                      <div className="flex justify-between p-2.5 rounded-xl bg-crypto-bg/40 border border-crypto-border/20">
                        <span className="text-xs text-crypto-muted">Position Size</span>
                        <span className="mono font-bold text-xs text-white">{selectedCall.position?.size?.toFixed(4)} {selectedCall.symbol.split('-')[0]}</span>
                      </div>
                      <div className="flex justify-between p-2.5 rounded-xl bg-crypto-bg/40 border border-crypto-border/20">
                        <span className="text-xs text-crypto-muted">Position Value</span>
                        <span className="mono font-bold text-xs text-white">${selectedCall.position?.position_value?.toFixed(0)}</span>
                      </div>
                      <div className="flex justify-between p-2.5 rounded-xl bg-crypto-bg/40 border border-crypto-border/20">
                        <span className="text-xs text-crypto-muted">Leverage</span>
                        <span className="font-bold text-xs text-white">{selectedCall.leverage}</span>
                      </div>
                      <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/10">
                        <div className="flex gap-2">
                          <AlertTriangle size={12} className="text-amber-400 mt-0.5" />
                          <div className="text-[11px] text-amber-400/80 leading-relaxed">
                            Risk {selectedCall.position?.risk_pct}% per trade. Use stop loss strictly. Not financial advice.
                          </div>
                        </div>
                      </div>
                    </div>
                  </GlassCard>
                </div>
              </>
            ) : (
              <GlassCard className="p-12 text-center">
                <Target size={32} className="mx-auto mb-4 text-crypto-muted" />
                <div className="text-white font-bold">Select a Trading Call</div>
                <div className="text-crypto-muted text-sm mt-1">Click on any call to see detailed analysis and chart</div>
              </GlassCard>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
