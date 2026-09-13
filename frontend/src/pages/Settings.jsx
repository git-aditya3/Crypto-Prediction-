import { useState, useEffect } from 'react'
import GlassCard from '../components/GlassCard'
import { useSettingsStore } from '../store/useSettingsStore'
import { api } from '../api/client'
import { Settings as SettingsIcon, DollarSign, Shield, Brain, BarChart3, Bell, Palette, Key, Save, RotateCcw, AlertTriangle, Zap, TrendingUp, Sliders } from 'lucide-react'

export default function SettingsPage() {
  const settings = useSettingsStore()
  const [activeTab, setActiveTab] = useState('trading')
  const [serverConfig, setServerConfig] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.getSettings().then(setServerConfig).catch(() => null)
  }, [])

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const tabs = [
    { id: 'trading', label: 'Trading', icon: DollarSign, desc: 'Risk & position management' },
    { id: 'models', label: 'Models', icon: Brain, desc: 'AI model weights & config' },
    { id: 'display', label: 'Display', icon: Palette, desc: 'Theme & chart preferences' },
    { id: 'notifications', label: 'Alerts', icon: Bell, desc: 'Notification settings' },
    { id: 'advanced', label: 'Advanced', icon: Sliders, desc: 'System configuration' },
  ]

  return (
    <div className="min-h-screen bg-crypto-bg relative">
      <div className="absolute inset-0 bg-gradient-mesh opacity-20 pointer-events-none"></div>
      
      <div className="relative max-w-[1400px] mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-crypto-accent to-crypto-accent2 flex items-center justify-center shadow-lg">
                <SettingsIcon size={20} className="text-black" />
              </span>
              <span className="text-white">Settings</span>
              <span className="px-3 py-1 rounded-full bg-crypto-card border border-crypto-border text-crypto-muted text-xs font-bold tracking-widest">PRO CONFIG</span>
            </h1>
            <p className="text-crypto-muted text-sm mt-2">
              Configure trading preferences, model weights, and display options • Changes saved automatically
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            <button onClick={() => { settings.resetSettings(); handleSave() }} className="btn-ghost flex items-center gap-2">
              <RotateCcw size={14} />
              Reset Defaults
            </button>
            <button onClick={handleSave} className={`btn-primary flex items-center gap-2 transition ${saved ? 'bg-emerald-500 text-black' : ''}`}>
              <Save size={14} />
              {saved ? 'Saved!' : 'Save'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Tabs Sidebar */}
          <div className="lg:col-span-3 space-y-2">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left p-4 rounded-2xl border transition flex items-center gap-3 ${
                    activeTab === tab.id 
                      ? 'bg-white border-white text-black shadow-xl' 
                      : 'bg-crypto-card/50 border-crypto-border/50 text-crypto-muted hover:text-white hover:border-crypto-borderLight'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${activeTab === tab.id ? 'bg-black text-white' : 'bg-crypto-bg border border-crypto-border'}`}>
                    <Icon size={18} />
                  </div>
                  <div>
                    <div className="font-bold text-sm">{tab.label}</div>
                    <div className={`text-xs ${activeTab === tab.id ? 'text-black/60' : 'text-crypto-muted'}`}>{tab.desc}</div>
                  </div>
                </button>
              )
            })}

            <GlassCard className="p-4 mt-6">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={14} className="text-amber-400" />
                <span className="text-xs font-bold tracking-widest text-amber-400 uppercase">Risk Notice</span>
              </div>
              <div className="text-[11px] text-crypto-muted leading-relaxed">
                Trading cryptocurrencies involves substantial risk. Never risk more than you can afford to lose. 
                AI predictions are probabilistic, not guaranteed. Always use stop losses.
              </div>
            </GlassCard>
          </div>

          {/* Content */}
          <div className="lg:col-span-9 space-y-6">
            {activeTab === 'trading' && (
              <>
                <GlassCard className="p-6">
                  <h3 className="font-bold text-white flex items-center gap-2 mb-6">
                    <DollarSign size={18} className="text-crypto-accent" />
                    Account & Risk Management
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-2 block">Account Balance (USDT)</label>
                      <div className="relative">
                        <DollarSign size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-crypto-muted" />
                        <input 
                          type="number"
                          value={settings.accountBalance}
                          onChange={e => settings.updateAccountBalance(parseFloat(e.target.value) || 0)}
                          className="w-full pl-10 pr-4 py-3 rounded-xl bg-crypto-bg border border-crypto-border text-white font-bold mono focus:border-crypto-accent outline-none"
                        />
                      </div>
                      <div className="text-[11px] text-crypto-muted mt-2">Used for position size calculation</div>
                    </div>
                    
                    <div>
                      <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-2 block">Risk Per Trade</label>
                      <div className="grid grid-cols-4 gap-2">
                        {[0.01, 0.02, 0.03, 0.05].map(risk => (
                          <button
                            key={risk}
                            onClick={() => settings.updateRiskPerTrade(risk)}
                            className={`py-3 rounded-xl border font-bold text-sm transition ${
                              settings.riskPerTrade === risk
                                ? 'bg-white text-black border-white shadow-lg'
                                : 'bg-crypto-bg border-crypto-border text-crypto-muted hover:text-white'
                            }`}
                          >
                            {risk * 100}%
                          </button>
                        ))}
                      </div>
                      <div className="text-[11px] text-crypto-muted mt-2">
                        ${settings.accountBalance * settings.riskPerTrade} risk per trade
                      </div>
                    </div>
                  </div>

                  <div className="mt-6">
                    <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-3 block">Risk Tolerance Preset</label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { id: 'conservative', label: 'Conservative', desc: '1% risk • Stable models', risk: '1%', color: 'emerald' },
                        { id: 'moderate', label: 'Moderate', desc: '2% risk • Balanced', risk: '2%', color: 'blue' },
                        { id: 'aggressive', label: 'Aggressive', desc: '5% risk • High growth', risk: '5%', color: 'red' },
                      ].map(preset => (
                        <button
                          key={preset.id}
                          onClick={() => settings.setRiskPreset(preset.id)}
                          className={`p-4 rounded-xl border text-left transition ${
                            settings.riskTolerance === preset.id
                              ? 'bg-white border-white text-black shadow-lg'
                              : 'bg-crypto-bg/50 border-crypto-border/50 text-white hover:border-crypto-borderLight'
                          }`}
                        >
                          <div className="font-bold text-sm">{preset.label}</div>
                          <div className={`text-xs mt-1 ${settings.riskTolerance === preset.id ? 'text-black/60' : 'text-crypto-muted'}`}>{preset.desc}</div>
                          <div className={`mt-2 px-2 py-1 rounded-full text-[10px] font-black inline-block ${
                            preset.color === 'emerald' ? 'bg-emerald-500/10 text-emerald-400' :
                            preset.color === 'blue' ? 'bg-blue-500/10 text-blue-400' :
                            'bg-red-500/10 text-red-400'
                          }`}>
                            {preset.risk} RISK
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                    <div>
                      <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-2 block">Timeframe</label>
                      <select value={settings.timeframe} onChange={e => settings.updateTimeframe(e.target.value)} className="w-full px-4 py-3 rounded-xl bg-crypto-bg border border-crypto-border text-white">
                        <option value="1h">1 Hour • Scalping</option>
                        <option value="4h">4 Hours • Intraday</option>
                        <option value="1d">1 Day • Swing</option>
                        <option value="1w">1 Week • Position</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-2 block">Trading Style</label>
                      <select value={settings.tradingStyle} onChange={e => settings.updateTradingStyle(e.target.value)} className="w-full px-4 py-3 rounded-xl bg-crypto-bg border border-crypto-border text-white">
                        <option value="scalping">Scalping (1H)</option>
                        <option value="day">Day Trading (4H)</option>
                        <option value="swing">Swing Trading (1D)</option>
                        <option value="position">Position (1W)</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-2 block">Leverage Preference</label>
                      <select value={settings.leveragePreference} onChange={e => settings.updateLeveragePreference(e.target.value)} className="w-full px-4 py-3 rounded-xl bg-crypto-bg border border-crypto-border text-white">
                        <option value="low">Low (1x-3x) • Safe</option>
                        <option value="medium">Medium (3x-5x) • Balanced</option>
                        <option value="high">High (5x-10x) • Aggressive</option>
                      </select>
                    </div>
                  </div>
                </GlassCard>

                <GlassCard className="p-6">
                  <h3 className="font-bold text-white flex items-center gap-2 mb-4">
                    <Shield size={18} className="text-crypto-accent2" />
                    Risk Visualization
                  </h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border text-center">
                      <div className="text-xs text-crypto-muted uppercase tracking-widest">Max Loss</div>
                      <div className="mono font-black text-xl text-red-400 mt-1">${(settings.accountBalance * settings.riskPerTrade).toFixed(0)}</div>
                      <div className="text-[11px] text-crypto-muted mt-1">Per trade</div>
                    </div>
                    <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border text-center">
                      <div className="text-xs text-crypto-muted uppercase tracking-widest">Daily Risk</div>
                      <div className="mono font-black text-xl text-amber-400 mt-1">${(settings.accountBalance * settings.riskPerTrade * 3).toFixed(0)}</div>
                      <div className="text-[11px] text-crypto-muted mt-1">3 trades max</div>
                    </div>
                    <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border text-center">
                      <div className="text-xs text-crypto-muted uppercase tracking-widest">To Recover</div>
                      <div className="mono font-black text-xl text-emerald-400 mt-1">{(settings.riskPerTrade * 100 * 2).toFixed(0)}%</div>
                      <div className="text-[11px] text-crypto-muted mt-1">Needed gain</div>
                    </div>
                  </div>
                </GlassCard>
              </>
            )}

            {activeTab === 'models' && (
              <>
                <GlassCard className="p-6">
                  <h3 className="font-bold text-white flex items-center gap-2 mb-6">
                    <Brain size={18} className="text-crypto-accent" />
                    AI Model Configuration • Ensemble v3
                  </h3>
                  
                  <div className="space-y-6">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase">Model Weights • Inverse MAPE Weighted</label>
                        <span className="text-xs px-2 py-1 rounded-full bg-crypto-accent/10 text-crypto-accent border border-crypto-accent/20">
                          Accuracy: ARIMA 2.57% best
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(settings.modelWeights).map(([model, weight]) => (
                          <div key={model} className="p-4 rounded-xl bg-crypto-bg border border-crypto-border">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-bold text-sm text-white uppercase tracking-wide">{model}</span>
                              <span className="mono font-black text-sm text-crypto-accent">{(weight * 100).toFixed(0)}%</span>
                            </div>
                            <input 
                              type="range" 
                              min={0} 
                              max={1} 
                              step={0.05} 
                              value={weight}
                              onChange={e => {
                                const newWeights = { ...settings.modelWeights, [model]: parseFloat(e.target.value) }
                                // Normalize to 100%
                                const total = Object.values(newWeights).reduce((a, b) => a + b, 0)
                                Object.keys(newWeights).forEach(k => newWeights[k] = newWeights[k] / total)
                                settings.updateModelWeights(newWeights)
                              }}
                              className="w-full accent-white h-2 bg-crypto-border rounded-lg appearance-none"
                            />
                            <div className="text-[11px] text-crypto-muted mt-2">
                              {model === 'arima' && '2.57% MAPE • Best accuracy • Time series'}
                              {model === 'transformer' && '6.1% MAPE • Attention • Seq2Seq'}
                              {model === 'lstm' && '6.8% MAPE • Recurrent • Memory'}
                              {model === 'xgboost' && '8.2% MAPE • Gradient boosting • Fast'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border flex items-center justify-between">
                        <div>
                          <div className="font-bold text-sm text-white">Stacking Ensemble</div>
                          <div className="text-xs text-crypto-muted mt-1">Meta-learner combination</div>
                        </div>
                        <button 
                          onClick={() => useSettingsStore.setState({ useStacking: !settings.useStacking })}
                          className={`w-12 h-6 rounded-full p-1 transition ${settings.useStacking ? 'bg-white' : 'bg-crypto-border'}`}
                        >
                          <div className={`w-4 h-4 rounded-full bg-black transition ${settings.useStacking ? 'translate-x-6' : ''}`}></div>
                        </button>
                      </div>
                      
                      <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border flex items-center justify-between">
                        <div>
                          <div className="font-bold text-sm text-white">Dynamic Weights</div>
                          <div className="text-xs text-crypto-muted mt-1">Inverse MAPE weighting</div>
                        </div>
                        <button 
                          onClick={() => useSettingsStore.setState({ useDynamicWeights: !settings.useDynamicWeights })}
                          className={`w-12 h-6 rounded-full p-1 transition ${settings.useDynamicWeights ? 'bg-white' : 'bg-crypto-border'}`}
                        >
                          <div className={`w-4 h-4 rounded-full bg-black transition ${settings.useDynamicWeights ? 'translate-x-6' : ''}`}></div>
                        </button>
                      </div>
                    </div>

                    {serverConfig && (
                      <div className="p-4 rounded-xl bg-crypto-accent/5 border border-crypto-accent/20">
                        <div className="text-xs font-bold tracking-widest text-crypto-accent uppercase mb-3">Server Configuration • v3</div>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div className="flex justify-between"><span className="text-crypto-muted">LSTM Layers</span><span className="text-white mono">{serverConfig.models?.lstm?.units} x {serverConfig.models?.lstm?.layers}</span></div>
                          <div className="flex justify-between"><span className="text-crypto-muted">Transformer d_model</span><span className="text-white mono">{serverConfig.models?.transformer?.d_model}</span></div>
                          <div className="flex justify-between"><span className="text-crypto-muted">Seq Length</span><span className="text-white mono">{serverConfig.data?.sequence_length}</span></div>
                          <div className="flex justify-between"><span className="text-crypto-muted">Test Size</span><span className="text-white mono">{serverConfig.data?.test_size}</span></div>
                        </div>
                      </div>
                    )}
                  </div>
                </GlassCard>

                <GlassCard className="p-6">
                  <h3 className="font-bold text-white flex items-center gap-2 mb-4">
                    <TrendingUp size={18} className="text-emerald-400" />
                    Performance Metrics • Past Week Backtest
                  </h3>
                  <div className="grid grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-center">
                      <div className="text-[10px] text-emerald-400 uppercase font-bold">Best Model</div>
                      <div className="font-black text-white mt-1">ARIMA</div>
                      <div className="text-xs text-emerald-400 mono">2.57% MAPE</div>
                    </div>
                    <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border text-center">
                      <div className="text-[10px] text-crypto-muted uppercase font-bold">Ensemble</div>
                      <div className="font-black text-white mt-1">6.30%</div>
                      <div className="text-xs text-crypto-muted mono">MAPE</div>
                    </div>
                    <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border text-center">
                      <div className="text-[10px] text-crypto-muted uppercase font-bold">SOL Best</div>
                      <div className="font-black text-white mt-1">2.37%</div>
                      <div className="text-xs text-crypto-muted mono">MAPE • R² 0.77</div>
                    </div>
                    <div className="p-3 rounded-xl bg-crypto-bg border border-crypto-border text-center">
                      <div className="text-[10px] text-crypto-muted uppercase font-bold">Dir Accuracy</div>
                      <div className="font-black text-white mt-1">83.3%</div>
                      <div className="text-xs text-crypto-muted mono">SOL • 6/6 symbols</div>
                    </div>
                  </div>
                </GlassCard>
              </>
            )}

            {activeTab === 'display' && (
              <GlassCard className="p-6">
                <h3 className="font-bold text-white flex items-center gap-2 mb-6">
                  <Palette size={18} className="text-crypto-accent" />
                  Display & Chart Preferences
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-2 block">Default Symbol</label>
                    <select value={settings.defaultSymbol} onChange={e => useSettingsStore.setState({ defaultSymbol: e.target.value })} className="w-full px-4 py-3 rounded-xl bg-crypto-bg border border-crypto-border text-white">
                      <option value="BTC-USD">BTC-USD • Bitcoin</option>
                      <option value="ETH-USD">ETH-USD • Ethereum</option>
                      <option value="SOL-USD">SOL-USD • Solana</option>
                      <option value="BNB-USD">BNB-USD • Binance</option>
                      <option value="XRP-USD">XRP-USD • Ripple</option>
                      <option value="ADA-USD">ADA-USD • Cardano</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="text-xs font-bold tracking-widest text-crypto-muted uppercase mb-2 block">Chart Type</label>
                    <select value={settings.chartType} onChange={e => useSettingsStore.setState({ chartType: e.target.value })} className="w-full px-4 py-3 rounded-xl bg-crypto-bg border border-crypto-border text-white">
                      <option value="candlestick">Candlestick • Professional</option>
                      <option value="line">Line • Minimal</option>
                      <option value="area">Area • Gradient</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-6">
                  {[
                    { key: 'showVolume', label: 'Show Volume', desc: 'Display volume bars' },
                    { key: 'showForecast', label: 'Show Forecast', desc: 'AI prediction line' },
                    { key: 'showAdvanced', label: 'Advanced Mode', desc: 'Show all indicators' },
                    { key: 'autoRefresh', label: 'Auto Refresh', desc: 'Live data updates' },
                  ].map(item => (
                    <div key={item.key} className="p-4 rounded-xl bg-crypto-bg border border-crypto-border flex items-center justify-between">
                      <div>
                        <div className="font-bold text-sm text-white">{item.label}</div>
                        <div className="text-xs text-crypto-muted mt-1">{item.desc}</div>
                      </div>
                      <button 
                        onClick={() => useSettingsStore.setState({ [item.key]: !settings[item.key] })}
                        className={`w-12 h-6 rounded-full p-1 transition ${settings[item.key] ? 'bg-white' : 'bg-crypto-border'}`}
                      >
                        <div className={`w-4 h-4 rounded-full bg-black transition ${settings[item.key] ? 'translate-x-6' : ''}`}></div>
                      </button>
                    </div>
                  ))}
                </div>
              </GlassCard>
            )}

            {activeTab === 'notifications' && (
              <GlassCard className="p-6">
                <h3 className="font-bold text-white flex items-center gap-2 mb-6">
                  <Bell size={18} className="text-crypto-accent" />
                  Notifications & Alerts
                </h3>
                
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-crypto-accent/10 flex items-center justify-center">
                        <Bell size={16} className="text-crypto-accent" />
                      </div>
                      <div>
                        <div className="font-bold text-sm text-white">Enable Notifications</div>
                        <div className="text-xs text-crypto-muted mt-1">Browser push notifications for signals</div>
                      </div>
                    </div>
                    <button 
                      onClick={() => settings.toggleNotifications()}
                      className={`w-12 h-6 rounded-full p-1 transition ${settings.enableNotifications ? 'bg-white' : 'bg-crypto-border'}`}
                    >
                      <div className={`w-4 h-4 rounded-full bg-black transition ${settings.enableNotifications ? 'translate-x-6' : ''}`}></div>
                    </button>
                  </div>

                  {[
                    { key: 'notifyOnBuy', label: 'Buy Signals', desc: 'Notify on STRONG_BUY and BUY', icon: TrendingUp, color: 'emerald' },
                    { key: 'notifyOnSell', label: 'Sell Signals', desc: 'Notify on STRONG_SELL and SELL', icon: TrendingUp, color: 'red' },
                    { key: 'notifyOnHighConfidence', label: 'High Confidence Only', desc: 'Only >80% confidence signals', icon: Zap, color: 'amber' },
                  ].map(item => {
                    const Icon = item.icon
                    return (
                      <div key={item.key} className="p-4 rounded-xl bg-crypto-bg/50 border border-crypto-border/50 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                            item.color === 'emerald' ? 'bg-emerald-500/10' :
                            item.color === 'red' ? 'bg-red-500/10' :
                            'bg-amber-500/10'
                          }`}>
                            <Icon size={16} className={
                              item.color === 'emerald' ? 'text-emerald-400' :
                              item.color === 'red' ? 'text-red-400' :
                              'text-amber-400'
                            } />
                          </div>
                          <div>
                            <div className="font-bold text-sm text-white">{item.label}</div>
                            <div className="text-xs text-crypto-muted mt-1">{item.desc}</div>
                          </div>
                        </div>
                        <button 
                          onClick={() => useSettingsStore.setState({ [item.key]: !settings[item.key] })}
                          className={`w-12 h-6 rounded-full p-1 transition ${settings[item.key] ? 'bg-white' : 'bg-crypto-border'}`}
                        >
                          <div className={`w-4 h-4 rounded-full bg-black transition ${settings[item.key] ? 'translate-x-6' : ''}`}></div>
                        </button>
                      </div>
                    )
                  })}
                </div>
              </GlassCard>
            )}

            {activeTab === 'advanced' && (
              <GlassCard className="p-6">
                <h3 className="font-bold text-white flex items-center gap-2 mb-6">
                  <Sliders size={18} className="text-crypto-accent" />
                  Advanced Configuration
                </h3>
                
                <div className="space-y-6">
                  <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border">
                    <div className="flex items-center gap-2 mb-3">
                      <Key size={14} className="text-crypto-accent" />
                      <span className="text-xs font-bold tracking-widest text-crypto-muted uppercase">API Configuration</span>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs text-crypto-muted mb-1 block">Binance API Base URL</label>
                        <input type="text" value="https://api.binance.com" disabled className="w-full px-3 py-2.5 rounded-xl bg-crypto-card border border-crypto-border text-crypto-muted text-sm" />
                      </div>
                      <div>
                        <label className="text-xs text-crypto-muted mb-1 block">Backend API URL</label>
                        <input type="text" value="http://localhost:8000" disabled className="w-full px-3 py-2.5 rounded-xl bg-crypto-card border border-crypto-border text-crypto-muted text-sm" />
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
                    <div className="flex gap-3">
                      <AlertTriangle size={16} className="text-amber-400 mt-0.5" />
                      <div>
                        <div className="text-sm font-bold text-amber-400">Professional Disclaimer</div>
                        <div className="text-xs text-amber-400/70 mt-1 leading-relaxed">
                          This platform provides AI-generated predictions and trading calls for educational purposes. 
                          Not financial advice. Crypto trading is high risk. Past performance (2.57% MAPE ARIMA) does not guarantee future results. 
                          Always do your own research and risk management.
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border">
                      <div className="text-xs text-crypto-muted uppercase tracking-widest">Version</div>
                      <div className="font-black text-white mt-1">v3.0 • Trading Calls Edition</div>
                      <div className="text-xs text-crypto-muted mt-1">ARIMA 2.57% • Ensemble 6.30% • SOL 2.37%</div>
                    </div>
                    <div className="p-4 rounded-xl bg-crypto-bg border border-crypto-border">
                      <div className="text-xs text-crypto-muted uppercase tracking-widest">Storage</div>
                      <div className="font-black text-white mt-1">{(JSON.stringify(settings).length / 1024).toFixed(1)} KB</div>
                      <div className="text-xs text-crypto-muted mt-1">LocalStorage • Zustand Persist</div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
