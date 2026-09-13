import { useSettingsStore } from '../store/useSettingsStore'
import { useEffect, useState } from 'react'
import { Bot, Play, Square, AlertTriangle, Settings, Wallet, Shield, Zap, CheckCircle, XCircle, Clock, TrendingUp } from 'lucide-react'
import { api } from '../api/client'

export default function AutoTrading() {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'

  const [config, setConfig] = useState(null)
  const [status, setStatus] = useState(null)
  const [brokers, setBrokers] = useState({})
  const [trades, setTrades] = useState([])
  const [pending, setPending] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('control')
  const [brokerForm, setBrokerForm] = useState({ broker_id: 'coindcx', broker_type: 'coindcx', api_key: '', api_secret: '', testnet: false, initial_balance: 10000 })
  const [showBrokerForm, setShowBrokerForm] = useState(false)

  const safeFixed = (v, d=2) => {
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return '0.00'
    return n.toFixed(d)
  }

  const fetchData = async () => {
    try {
      // Use api client where possible, fallback to fetch
      const [cfgRes, statusRes, brokersRes, tradesRes, pendingRes] = await Promise.all([
        api.getAutoTradeConfig().catch(() => fetch('/api/autotrade/config').then(r => r.json())),
        api.getAutoTradeStatus().catch(() => fetch('/api/autotrade/status').then(r => r.json())),
        api.getBrokers().catch(() => fetch('/api/brokers').then(r => r.json())),
        api.getAutoTradeTrades(50).catch(() => fetch('/api/autotrade/trades?limit=50').then(r => r.json())),
        api.getPendingApprovals().catch(() => fetch('/api/autotrade/pending').then(r => r.json()))
      ])
      if (cfgRes) setConfig(cfgRes.config || cfgRes)
      if (statusRes) setStatus(statusRes)
      if (brokersRes) setBrokers(brokersRes.brokers || {})
      if (tradesRes) setTrades(tradesRes.trades || [])
      if (pendingRes) setPending(pendingRes.pending || [])
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 5000); return () => clearInterval(i) }, [])

  const updateConfig = async (newConfig) => {
    try {
      // Deep merge safety - ensure nested objects exist
      const safeConfig = {
        ...newConfig,
        risk: { ...(config?.risk||{}), ...(newConfig.risk||{}) },
        execution: { ...(config?.execution||{}), ...(newConfig.execution||{}) },
        strategies: { ...(config?.strategies||{}), ...(newConfig.strategies||{}) },
        symbols: { ...(config?.symbols||{}), ...(newConfig.symbols||{}) },
        trading_hours: { ...(config?.trading_hours||{}), ...(newConfig.trading_hours||{}) },
      }
      const data = await api.updateAutoTradeConfig(safeConfig).catch(async () => {
        const res = await fetch('/api/autotrade/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ config: safeConfig })
        })
        return res.json()
      })
      if (data?.config) {
        setConfig(data.config)
        fetchData()
      } else if (data?.detail) alert(data.detail)
    } catch (e) { alert(e.message) }
  }

  const toggleEnabled = () => {
    if (!config) return
    updateConfig({ ...config, enabled: !config.enabled })
  }

  const changeMode = (mode) => {
    if (!config) return
    updateConfig({ ...config, mode, execution: { ...(config.execution||{}), broker_id: config.execution?.broker_id || 'coindcx' } })
  }

  const startTrading = async () => {
    try {
      const data = await api.startAutoTrade().catch(() => fetch('/api/autotrade/start', { method: 'POST' }).then(r=>r.json()))
      if (data?.message) { alert(data.message); fetchData() } else if (data?.detail) alert(data.detail)
    } catch (e) { alert(e.message) }
  }

  const stopTrading = async () => {
    try {
      await api.stopAutoTrade().catch(() => fetch('/api/autotrade/stop', { method: 'POST' }))
      fetchData()
    } catch (e) { console.error(e) }
  }

  const emergencyStop = async () => {
    if (!confirm('🚨 EMERGENCY STOP - Halt all trading immediately?')) return
    try {
      const data = await api.emergencyStop().catch(() => fetch('/api/autotrade/emergency/stop', { method: 'POST' }).then(r=>r.json()))
      alert(data?.message || 'Emergency stopped')
      fetchData()
    } catch (e) { alert(e.message) }
  }

  const executeManual = async (symbol) => {
    try {
      const data = await api.executeAutoTrade(symbol, true).catch(() => 
        fetch('/api/autotrade/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ symbol, manual: true })
        }).then(r=>r.json())
      )
      if (data?.success) alert(`✅ ${data.message}`)
      else if (data?.requires_approval) alert(`📋 Requires approval: ${data.approval_id}`)
      else alert(`Failed: ${data?.reason || data?.detail || 'Unknown'}`)
      fetchData()
    } catch (e) { alert(e.message) }
  }

  const approveTrade = async (id) => {
    try {
      const data = await api.approveTrade(id).catch(() => fetch(`/api/autotrade/approve/${id}`, { method: 'POST' }).then(r=>r.json()))
      if (data?.success) { alert('Approved and executed'); fetchData() } else alert(data?.reason || data?.detail || 'Failed')
    } catch (e) { alert(e.message) }
  }

  const rejectTrade = async (id) => {
    try {
      await api.rejectTrade(id).catch(() => fetch(`/api/autotrade/reject/${id}`, { method: 'POST' }))
      fetchData()
    } catch (e) { console.error(e) }
  }

  const connectBroker = async () => {
    try {
      // If broker exists, try to remove first to allow update (fixes duplicate id bug)
      if (brokers[brokerForm.broker_id]) {
        try {
          await api.removeBroker(brokerForm.broker_id).catch(() => fetch(`/api/brokers/${brokerForm.broker_id}/remove`, { method: 'DELETE' }))
        } catch {}
      }
      const data = await api.connectBroker(brokerForm).catch(async () => {
        const res = await fetch('/api/brokers/connect', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(brokerForm)
        })
        const j = await res.json()
        if (!res.ok) throw new Error(j.detail || 'Failed')
        return j
      })
      setShowBrokerForm(false)
      fetchData()
      alert(data.message || `Connected ${brokerForm.broker_id}`)
    } catch (e) { alert(e.message) }
  }

  if (loading) return <div className="p-6 text-center">Loading automated trading engine - extensive controls...</div>
  if (!config) return <div className="p-6 text-center">Loading config... If this persists, check backend /autotrade/config</div>

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 font-poppins space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3 flex-wrap">
            <Bot className="text-emerald-600" /> Automated Real Trading - CoinDCX
            <span className="px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-black/5 dark:border-white/5 text-emerald-600 text-sm font-bold">COINDCX REAL MONEY</span>
            <span className="px-3 py-1 rounded-full bg-red-500/10 border border-red-500/10 text-red-500 text-sm font-bold animate-pulse">ACTUAL INR</span>
            {status?.real_trading && <span className="px-3 py-1 rounded-full bg-red-500/10 border border-red-500/10 text-red-500 text-sm font-bold animate-pulse">REAL MONEY</span>}
          </h1>
          <p className="text-zinc-500 mt-1">Automate REAL trades with CoinDCX - actual INR from your account - no paper simulation - extensive user control - broker integration, risk guards, emergency stop</p>
        </div>
        <div className="flex gap-2">
          <button onClick={emergencyStop} className="px-4 py-2 rounded-xl bg-red-500 text-white font-bold flex items-center gap-2 hover:bg-red-400">
            <AlertTriangle size={16} /> Emergency Stop
          </button>
          {status?.is_running ? (
            <button onClick={stopTrading} className="px-4 py-2 rounded-xl ui-card border border-black/5 dark:border-white/5 flex items-center gap-2">
              <Square size={16} /> Stop
            </button>
          ) : (
            <button onClick={startTrading} className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-bold flex items-center gap-2 hover:bg-emerald-400">
              <Play size={16} /> Start Auto
            </button>
          )}
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Status</div>
          <div className={`text-lg font-black flex items-center gap-2 ${status?.is_running ? 'text-emerald-600' : 'text-zinc-500'}`}>
            {status?.is_running ? <><div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div> Running</> : 'Stopped'}
          </div>
          <div className="text-xs text-zinc-500 mt-1">Mode: {status?.mode || config?.mode}</div>
        </div>
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Broker</div>
          <div className="text-sm font-bold">{status?.broker_id || config?.execution?.broker_id || 'coindcx'}</div>
          <div className="text-xs text-zinc-500 mt-1">{status?.broker_connected ? 'Connected' : 'Not connected'}</div>
        </div>
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Open Positions</div>
          <div className="text-lg font-black">{status?.open_positions ?? 0} / {status?.config?.risk?.max_positions ?? config?.risk?.max_positions ?? 5}</div>
          <div className="text-xs text-zinc-500 mt-1">Max {config?.risk?.max_positions ?? 5}</div>
        </div>
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Daily Trades</div>
          <div className="text-lg font-black">{status?.daily_trades ?? 0} / {config?.max_daily_trades ?? 10}</div>
          <div className="text-xs text-zinc-500 mt-1">Today</div>
        </div>
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Pending Approvals</div>
          <div className="text-lg font-black text-zinc-500">{status?.pending_approvals ?? pending.length ?? 0}</div>
          <div className="text-xs text-zinc-500 mt-1">Semi-auto</div>
        </div>
        <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <div className="text-[10px] text-zinc-500 uppercase">Risk/Trade</div>
          <div className="text-lg font-black">{config?.risk?.risk_per_trade_pct ?? 2}%</div>
          <div className="text-xs text-zinc-500 mt-1">${((config?.account_balance||10000) * ((config?.risk?.risk_per_trade_pct||2) / 100)).toFixed(0)} risk</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1 rounded-xl ui-card border border-black/5 dark:border-white/5 w-fit overflow-x-auto">
        {[
          { id: 'control', label: 'Control Panel', icon: Settings },
          { id: 'brokers', label: 'Brokers', icon: Wallet },
          { id: 'risk', label: 'Risk Guard', icon: Shield },
          { id: 'trades', label: 'Trades', icon: TrendingUp },
          { id: 'pending', label: `Pending (${pending.length})`, icon: Clock }
        ].map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition whitespace-nowrap ${activeTab === t.id ? 'bg-white text-black' : 'text-zinc-500 hover:text-white'}`}>
            <t.icon size={14} /> {t.label}
          </button>
        ))}
      </div>

      {/* Control Panel */}
      {activeTab === 'control' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Main Controls */}
          <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5 space-y-5">
            <h3 className="font-bold flex items-center gap-2"><Zap size={16} className="text-emerald-600" /> Main Controls - Extensive User Control</h3>
            
            <div className="flex items-center justify-between p-3 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
              <div>
                <div className="font-medium">Auto Trading Enabled</div>
                <div className="text-xs text-zinc-500">Master switch for automation</div>
              </div>
              <button onClick={toggleEnabled} className={`w-12 h-6 rounded-full transition flex items-center ${config.enabled ? 'bg-emerald-500 justify-end' : 'ui-card justify-start'} p-1`}>
                <div className="w-4 h-4 bg-white rounded-full"></div>
              </button>
            </div>

            <div>
              <label className="text-xs text-zinc-500 uppercase">Trading Mode - Extensive Control</label>
              <div className="grid grid-cols-3 gap-2 mt-2">
                {[
                  { id: 'full_auto', label: 'CoinDCX Real', desc: 'Actual INR, real trades', color: 'emerald' },
                  { id: 'semi_auto', label: 'Semi-Auto', desc: 'CoinDCX + approval', color: 'amber' },
                  { id: 'paper', label: 'Paper (Test)', desc: 'Testing only, no real', color: 'blue' }
                ].map(m => (
                  <button key={m.id} onClick={() => changeMode(m.id)} className={`p-3 rounded-xl border text-left transition ${config.mode === m.id ? (m.color === 'emerald' ? 'bg-zinc-100 dark:bg-zinc-800 border-emerald-500/30 text-emerald-600' : m.color === 'amber' ? 'bg-amber-500/10 border-amber-500/30 text-zinc-500' : 'bg-blue-500/10 border-blue-500/30 text-blue-400') : 'bg-transparent border-black/5 dark:border-white/5/50 text-zinc-500 hover:border-black/5 dark:border-white/5'}`}>
                    <div className="font-bold text-sm">{m.label}</div>
                    <div className="text-[10px] mt-1">{m.desc}</div>
                  </button>
                ))}
              </div>
              <div className="mt-2 p-2 rounded-lg bg-emerald-500/5 border border-black/5 dark:border-white/5 text-xs">
                <div className="font-bold text-emerald-600">CoinDCX Real Money - No Paper Simulation</div>
                <div className="text-zinc-500 mt-1">Uses actual INR and crypto from your CoinDCX account. BTCINR, ETHINR, etc. Real trades, real P&L. No paper simulation as requested.</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-zinc-500">Account Balance $</label>
                <input type="number" value={config.account_balance||10000} onChange={e => updateConfig({ ...config, account_balance: parseFloat(e.target.value)||10000 })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div>
                <label className="text-xs text-zinc-500">Max Daily Trades</label>
                <input type="number" value={config.max_daily_trades||10} onChange={e => updateConfig({ ...config, max_daily_trades: parseInt(e.target.value)||10 })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
            </div>

            <div className="p-3 rounded-xl bg-emerald-500/5 border border-black/5 dark:border-white/5">
              <div className="text-xs font-bold text-emerald-600">💰 CoinDCX Real Money - No Paper Simulation</div>
              <div className="text-xs text-zinc-500 mt-1">This uses ACTUAL INR from your CoinDCX account - real trades, real P&L, no paper simulation as you requested. Connect CoinDCX API keys (trading permission only). Markets: BTCINR, ETHINR, BNBINR, SOLINR, etc. Risk guards protect your capital.</div>
            </div>
          </div>

          {/* Strategy & Execution Controls */}
          <div className="space-y-6">
            <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
              <h3 className="font-bold mb-3">Strategy Controls - Toggle Strategies</h3>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { key: 'use_ai_ensemble', label: 'AI Ensemble' },
                  { key: 'use_breakout', label: 'Breakout' },
                  { key: 'use_rsi_signals', label: 'RSI Signals' },
                  { key: 'use_volume_spikes', label: 'Volume Spikes' },
                  { key: 'use_dca_bot', label: 'DCA Bot' },
                  { key: 'use_grid_bot', label: 'Grid Bot' }
                ].map(s => (
                  <label key={s.key} className="flex items-center gap-2 p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5/50 cursor-pointer">
                    <input type="checkbox" checked={!!config.strategies?.[s.key]} onChange={e => updateConfig({ ...config, strategies: { ...(config.strategies||{}), [s.key]: e.target.checked } })} className="rounded" />
                    <span className="text-sm">{s.label}</span>
                  </label>
                ))}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-zinc-500">Confidence Threshold %</label>
                  <input type="number" value={config.strategies?.ai_confidence_threshold||70} onChange={e => updateConfig({ ...config, strategies: { ...(config.strategies||{}), ai_confidence_threshold: parseFloat(e.target.value)||70 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                </div>
                <div>
                  <label className="text-xs text-zinc-500">Min RR Ratio</label>
                  <input type="number" step="0.1" value={config.strategies?.min_risk_reward||1.5} onChange={e => updateConfig({ ...config, strategies: { ...(config.strategies||{}), min_risk_reward: parseFloat(e.target.value)||1.5 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                </div>
              </div>
            </div>

            <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
              <h3 className="font-bold mb-3">Symbol Controls - Whitelist/Blacklist</h3>
              <div>
                <label className="text-xs text-zinc-500">Whitelist (comma separated, empty = all)</label>
                <input value={(config.symbols?.whitelist||[]).join(',')} onChange={e => updateConfig({ ...config, symbols: { ...(config.symbols||{}), whitelist: e.target.value.split(',').map(s => s.trim()).filter(Boolean) } })} placeholder="BTC-USD,ETH-USD,BNB-USD,SOL-USD" className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div className="mt-3">
                <label className="text-xs text-zinc-500">Blacklist</label>
                <input value={(config.symbols?.blacklist||[]).join(',')} onChange={e => updateConfig({ ...config, symbols: { ...(config.symbols||{}), blacklist: e.target.value.split(',').map(s => s.trim()).filter(Boolean) } })} placeholder="DOGE-USD,SHIB-USD" className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div className="mt-3">
                <label className="text-xs text-zinc-500">Max Positions Per Symbol</label>
                <input type="number" value={config.symbols?.max_positions_per_symbol||1} onChange={e => updateConfig({ ...config, symbols: { ...(config.symbols||{}), max_positions_per_symbol: parseInt(e.target.value)||1 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Brokers Tab */}
      {activeTab === 'brokers' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <h3 className="font-bold">Broker Integration - CoinDCX REAL MONEY</h3>
              <p className="text-xs text-zinc-500">No paper simulation - actual INR from CoinDCX account</p>
            </div>
            <button onClick={() => setShowBrokerForm(true)} className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-bold">Connect CoinDCX Real Account</button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(brokers).map(([id, broker]) => (
              <div key={id} className={`p-4 rounded-2xl border ${broker.paper_mode ? 'bg-blue-500/5 border-blue-500/20' : 'bg-emerald-500/5 border-black/5 dark:border-white/5'}`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold">{broker.name || id}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${broker.paper_mode ? 'bg-blue-500 text-white' : 'bg-emerald-500 text-black'}`}>{broker.paper_mode ? 'PAPER' : 'REAL'}</span>
                </div>
                <div className="mt-3 space-y-1 text-xs">
                  <div className="flex justify-between"><span className="text-zinc-500">Type</span><span>{broker.type}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">Connected</span><span className={broker.connected ? 'text-emerald-600' : 'text-red-500'}>{broker.connected ? 'Yes' : 'No'}</span></div>
                  <div className="flex justify-between"><span className="text-zinc-500">Has Keys</span><span>{broker.has_keys ? 'Yes (secure)' : 'No (paper)'}</span></div>
                  {broker.balances && Object.keys(broker.balances).length > 0 && (
                    <div className="mt-2 p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5/50">
                      <div className="text-[10px] text-zinc-500 uppercase">Balances</div>
                      {Object.entries(broker.balances).slice(0, 3).map(([asset, bal]) => (
                        <div key={asset} className="flex justify-between text-xs"><span>{asset}</span><span>{safeFixed(bal.total ?? bal.free, 4)}</span></div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="mt-3 flex gap-2">
                  <button onClick={async () => { 
                    try {
                      const data = await api.testBroker(id).catch(() => fetch(`/api/brokers/${id}/test`).then(r=>r.json()))
                      alert(JSON.stringify(data, null, 2))
                    } catch(e){ alert(e.message) }
                  }} className="flex-1 py-1.5 rounded-lg bg-transparent border border-black/5 dark:border-white/5 text-xs">Test</button>
                  <button onClick={async () => { 
                    if (confirm(`Remove broker ${id}?`)) { 
                      await api.removeBroker(id).catch(()=> fetch(`/api/brokers/${id}/remove`, { method: 'DELETE' }))
                      fetchData() 
                    }
                  }} className="flex-1 py-1.5 rounded-lg bg-red-500/10 text-red-500 border border-red-500/10 text-xs">Remove</button>
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 rounded-2xl bg-emerald-500/5 border border-black/5 dark:border-white/5">
            <h4 className="font-bold text-sm text-emerald-600">CoinDCX Real Money Integration - No Paper Simulation</h4>
            <div className="mt-2 text-xs text-zinc-500 space-y-1">
              <div>• <span className="text-emerald-600 font-bold">CoinDCX REAL MONEY</span>: Uses ACTUAL INR and crypto from your CoinDCX account - no paper simulation as you requested</div>
              <div>• <span className="text-emerald-600">Markets</span>: BTCINR, ETHINR, BNBINR, SOLINR, XRPINR, ADAINR, DOGEINR, AVAXINR, MATICINR, DOTINR, etc. - INR pairs</div>
              <div>• <span className="text-zinc-500">How to get API keys</span>: CoinDCX → Profile → API Dashboard → Create API Key → Enter label, check Bind IP if needed → Email + SMS OTP → Store Key & Secret</div>
              <div>• <span className="text-red-500">Security</span>: Enable trading permission only, NEVER withdrawal. Use IP whitelist. Keys base64 encoded locally in data/brokers.json, never shared</div>
              <div>• <span className="text-blue-400">Real Trading</span>: When connected, all trades use actual CoinDCX INR balance - real P&L, real execution. No paper money stimulation</div>
              <div>• <span className="text-zinc-500">Risk Guards</span>: Max daily loss 6%, max positions 5, max drawdown 10%, confidence threshold 70%, RR filter, cooldowns - protects your real capital</div>
            </div>
          </div>
        </div>
      )}

      {/* Risk Tab */}
      {activeTab === 'risk' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5 space-y-4">
            <h3 className="font-bold flex items-center gap-2"><Shield size={16} className="text-zinc-500" /> Risk Controls - Extensive Protection</h3>
            
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-zinc-500">Risk Per Trade %</label>
                <input type="number" step="0.1" value={config.risk?.risk_per_trade_pct||2} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), risk_per_trade_pct: parseFloat(e.target.value)||2 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                <div className="text-[10px] text-zinc-500 mt-1">Recommended 1-2%</div>
              </div>
              <div>
                <label className="text-xs text-zinc-500">Max Daily Loss %</label>
                <input type="number" step="0.1" value={config.risk?.max_daily_loss_pct||6} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), max_daily_loss_pct: parseFloat(e.target.value)||6 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                <div className="text-[10px] text-zinc-500 mt-1">Halt if exceeded</div>
              </div>
              <div>
                <label className="text-xs text-zinc-500">Max Positions</label>
                <input type="number" value={config.risk?.max_positions||5} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), max_positions: parseInt(e.target.value)||5 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div>
                <label className="text-xs text-zinc-500">Max Drawdown %</label>
                <input type="number" value={config.risk?.max_drawdown_pct||10} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), max_drawdown_pct: parseFloat(e.target.value)||10 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div>
                <label className="text-xs text-zinc-500">Max Leverage</label>
                <input type="number" value={config.risk?.max_leverage||5} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), max_leverage: parseInt(e.target.value)||5 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <div>
                <label className="text-xs text-zinc-500">Max Consecutive Losses</label>
                <input type="number" value={config.risk?.max_consecutive_losses||3} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), max_consecutive_losses: parseInt(e.target.value)||3 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
            </div>

            <div>
              <label className="text-xs text-zinc-500">Position Size Method</label>
              <select value={config.risk?.position_size_method||'risk_based'} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), position_size_method: e.target.value } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                <option value="risk_based">Risk Based (risk% / |entry-SL|)</option>
                <option value="fixed">Fixed $ amount</option>
                <option value="percent_balance">% of Balance</option>
                <option value="kelly">Kelly Criterion (advanced)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2 p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5/50 cursor-pointer">
                <input type="checkbox" checked={!!config.risk?.use_trailing_stop} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), use_trailing_stop: e.target.checked } })} />
                <span className="text-sm">Use Trailing Stop</span>
              </label>
              <label className="flex items-center gap-2 p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5/50 cursor-pointer">
                <input type="checkbox" checked={!!config.risk?.move_sl_to_breakeven_at_tp1} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), move_sl_to_breakeven_at_tp1: e.target.checked } })} />
                <span className="text-sm">Move SL to Breakeven at TP1</span>
              </label>
              <label className="flex items-center gap-2 p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5/50 cursor-pointer">
                <input type="checkbox" checked={!!config.risk?.daily_loss_halt} onChange={e => updateConfig({ ...config, risk: { ...(config.risk||{}), daily_loss_halt: e.target.checked } })} />
                <span className="text-sm">Halt Trading if Daily Loss Exceeded</span>
              </label>
            </div>
          </div>

          <div className="space-y-6">
            <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
              <h3 className="font-bold mb-3">Execution Controls</h3>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-zinc-500">Order Type</label>
                  <select value={config.execution?.order_type||'MARKET'} onChange={e => updateConfig({ ...config, execution: { ...(config.execution||{}), order_type: e.target.value } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                    <option value="MARKET">Market (instant)</option>
                    <option value="LIMIT">Limit (better price)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-zinc-500">Broker</label>
                  <select value={config.execution?.broker_id||'coindcx'} onChange={e => updateConfig({ ...config, execution: { ...(config.execution||{}), broker_id: e.target.value } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                    {Object.keys(brokers).length>0 ? Object.keys(brokers).map(id => <option key={id} value={id}>{id} - {brokers[id].type}</option>) : <option value="coindcx">coindcx - CoinDCX REAL</option>}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-zinc-500">Slippage Tolerance %</label>
                  <input type="number" step="0.1" value={config.execution?.slippage_tolerance_pct||0.5} onChange={e => updateConfig({ ...config, execution: { ...(config.execution||{}), slippage_tolerance_pct: parseFloat(e.target.value)||0.5 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                </div>
                <div>
                  <label className="text-xs text-zinc-500">Cooldown Between Trades (min)</label>
                  <input type="number" value={config.trading_hours?.cooldown_between_trades_minutes||30} onChange={e => updateConfig({ ...config, trading_hours: { ...(config.trading_hours||{}), cooldown_between_trades_minutes: parseInt(e.target.value)||30 } })} className="w-full mt-1 px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                </div>
              </div>
              <div className="mt-3 space-y-2">
                <label className="flex items-center gap-2 p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5/50 cursor-pointer">
                  <input type="checkbox" checked={!!config.execution?.auto_sl_tp} onChange={e => updateConfig({ ...config, execution: { ...(config.execution||{}), auto_sl_tp: e.target.checked } })} />
                  <span className="text-sm">Auto SL/TP (OCO)</span>
                </label>
                <label className="flex items-center gap-2 p-2 rounded-lg bg-transparent border border-black/5 dark:border-white/5/50 cursor-pointer">
                  <input type="checkbox" checked={!!config.execution?.multiple_tp} onChange={e => updateConfig({ ...config, execution: { ...(config.execution||{}), multiple_tp: e.target.checked } })} />
                  <span className="text-sm">Multiple TP (50/30/20)</span>
                </label>
                <label className="flex items-center gap-2 p-2 rounded-lg bg-red-500/5 border border-red-500/10 cursor-pointer">
                  <input type="checkbox" checked={!!config.execution?.enable_real_trading} onChange={e => updateConfig({ ...config, execution: { ...(config.execution||{}), enable_real_trading: e.target.checked } })} />
                  <span className="text-sm text-red-500 font-bold">Enable REAL Trading (requires API keys + safety flag)</span>
                </label>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-black dark:bg-white/5 border border-black/5 dark:border-white/5">
              <h4 className="font-bold text-sm text-zinc-500">Risk Guard - How It Protects You</h4>
              <div className="mt-2 text-xs text-zinc-500 space-y-1">
                <div>• Checks emergency stop, enabled, trading hours, daily loss, max positions, max drawdown, consecutive losses, daily trades, cooldown, symbol whitelist/blacklist, confidence, RR, position size</div>
                <div>• Position sizing: risk_based = (balance * risk%) / |entry-SL|, capped by max leverage</div>
                <div>• Daily loss halt: stops trading if daily P&L &lt; -max_daily_loss%</div>
                <div>• Cooldown: prevents over-trading, waits between trades and after losses</div>
                <div>• All checks must pass to allow trade - extensive user control</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Trades Tab */}
      {activeTab === 'trades' && (
        <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <h3 className="font-bold mb-4">Auto Trading History - Real & Paper Trades</h3>
          {trades.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">No auto trades yet - start auto trading or execute manual trades</div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-auto">
              {trades.slice().reverse().map((trade, i) => (
                <div key={i} className={`p-3 rounded-xl border flex items-center justify-between ${trade.real_trading ? 'bg-red-500/5 border-red-500/10' : 'bg-transparent border-black/5 dark:border-white/5/50'}`}>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-bold">{trade.symbol||'Unknown'}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${trade.side === 'BUY' ? 'bg-zinc-100 dark:bg-zinc-800 text-emerald-600' : 'bg-red-500/10 text-red-500'}`}>{trade.side||'BUY'}</span>
                    <span className="text-xs text-zinc-500">{safeFixed(trade.quantity,4)} @ ${safeFixed(trade.entry_price,2)}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full ${trade.real_trading ? 'bg-red-500 text-white' : 'bg-blue-500 text-white'}`}>{trade.real_trading ? 'REAL' : 'PAPER'}</span>
                    <span className="text-xs text-zinc-500">{trade.signal||''} {safeFixed(trade.confidence,0)}%</span>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-zinc-500">{trade.timestamp ? new Date(trade.timestamp).toLocaleString() : 'Unknown time'}</div>
                    <div className="text-xs">{trade.mode||'auto'} • {trade.broker||'paper'}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Pending Tab */}
      {activeTab === 'pending' && (
        <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
          <h3 className="font-bold mb-4 flex items-center gap-2"><Clock size={16} className="text-zinc-500" /> Pending Approvals - Semi-Auto Mode</h3>
          {pending.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">No pending approvals - semi-auto mode queues trades here for your approval</div>
          ) : (
            <div className="space-y-3">
              {pending.map((approval) => (
                <div key={approval.id} className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-lg">{approval.symbol}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${approval.call?.signal?.includes('BUY') ? 'bg-emerald-500 text-black' : 'bg-red-500 text-white'}`}>{approval.call?.signal||'BUY'}</span>
                        <span className="text-xs text-zinc-500">{safeFixed(approval.quantity,4)} @ ${safeFixed(approval.call?.entry_price,2)} • {safeFixed(approval.call?.confidence,0)}% conf</span>
                      </div>
                      <div className="text-xs text-zinc-500 mt-1">SL ${safeFixed(approval.call?.stop_loss,2)} • TP1 ${safeFixed(approval.call?.take_profits?.tp1,2)} • RR {safeFixed(approval.call?.risk_reward,2)}</div>
                      <div className="text-[10px] text-zinc-500 mt-1">ID: {approval.id} • {approval.timestamp ? new Date(approval.timestamp).toLocaleString() : ''}</div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => approveTrade(approval.id)} className="px-4 py-2 rounded-xl bg-emerald-500 text-black font-bold flex items-center gap-1"><CheckCircle size={14} /> Approve & Execute</button>
                      <button onClick={() => rejectTrade(approval.id)} className="px-4 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5 flex items-center gap-1"><XCircle size={14} /> Reject</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Broker Form Modal */}
      {showBrokerForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur p-4">
          <div className="p-6 rounded-2xl ui-card border border-black/5 dark:border-white/5 w-full max-w-md">
            <h3 className="font-bold text-lg mb-4">Connect CoinDCX - Real Money Trading</h3>
            <div className="space-y-3">
              <input placeholder="Broker ID e.g. coindcx" value={brokerForm.broker_id} onChange={e => setBrokerForm({ ...brokerForm, broker_id: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              <select value={brokerForm.broker_type} onChange={e => setBrokerForm({ ...brokerForm, broker_type: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                <option value="coindcx">CoinDCX REAL MONEY - Actual INR</option>
                <option value="binance">Binance (Real/Testnet)</option>
                <option value="paper">Paper (Testing Only - Not Real)</option>
              </select>
              {(brokerForm.broker_type === 'coindcx' || brokerForm.broker_type === 'binance') && (
                <>
                  <input placeholder={brokerForm.broker_type === 'coindcx' ? 'CoinDCX API Key (from API Dashboard)' : 'API Key (trading permission only)'} value={brokerForm.api_key} onChange={e => setBrokerForm({ ...brokerForm, api_key: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                  <input placeholder={brokerForm.broker_type === 'coindcx' ? 'CoinDCX API Secret' : 'API Secret'} type="password" value={brokerForm.api_secret} onChange={e => setBrokerForm({ ...brokerForm, api_secret: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                  {brokerForm.broker_type === 'binance' && (
                    <label className="flex items-center gap-2 text-sm">
                      <input type="checkbox" checked={brokerForm.testnet} onChange={e => setBrokerForm({ ...brokerForm, testnet: e.target.checked })} />
                      Use Testnet (Binance only)
                    </label>
                  )}
                  {brokerForm.broker_type === 'coindcx' && (
                    <div className="text-xs text-emerald-600">CoinDCX: Profile → API Dashboard → Create API Key → Label + IP bind optional → OTP → Store Key/Secret</div>
                  )}
                </>
              )}
              {brokerForm.broker_type === 'paper' && (
                <input type="number" placeholder="Initial Balance (testing only)" value={brokerForm.initial_balance} onChange={e => setBrokerForm({ ...brokerForm, initial_balance: parseFloat(e.target.value)||10000 })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              )}
              <div className="p-3 rounded-xl bg-emerald-500/5 border border-black/5 dark:border-white/5 text-xs">
                <div className="font-bold text-emerald-600">CoinDCX Real Money - No Paper Simulation</div>
                <div className="text-zinc-500 mt-1">As requested, this uses ACTUAL INR from your CoinDCX account - no paper money. Real trades, real P&L. Markets: BTCINR, ETHINR, etc. API keys: trading permission only, no withdrawal, IP whitelist recommended. Keys encoded locally.</div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setShowBrokerForm(false)} className="flex-1 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">Cancel</button>
                <button onClick={connectBroker} className="flex-1 py-2 rounded-xl bg-emerald-500 text-black font-bold">Connect CoinDCX Real</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Manual Execute Quick Panel */}
      <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
        <h4 className="font-bold text-sm mb-3">Quick Manual Execute - Test Auto Trading</h4>
        <div className="flex flex-wrap gap-2">
          {['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD'].map(sym => (
            <button key={sym} onClick={() => executeManual(sym)} className="px-3 py-1.5 rounded-lg bg-transparent border border-black/5 dark:border-white/5 hover:border-emerald-500/30 text-sm">
              Execute {sym}
            </button>
          ))}
        </div>
        <div className="text-xs text-zinc-500 mt-2">Executes trade via auto engine with risk checks - respects mode (paper/semi/full auto)</div>
      </div>
    </div>
  )
}
