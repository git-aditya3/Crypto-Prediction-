import { useState, useEffect } from 'react'
import GlassCard from '../components/GlassCard'
import { useSettingsStore } from '../store/useSettingsStore'
import { api } from '../api/client'
import { Settings as SettingsIcon, DollarSign, Shield, Brain, BarChart3, Bell, Palette, Key, Save, RotateCcw, AlertTriangle, Zap, TrendingUp, Sliders, Sun, Moon, Sparkles } from 'lucide-react'

export default function SettingsPage() {
  const settings = useSettingsStore()
  const [activeTab, setActiveTab] = useState('display')
  const [serverConfig, setServerConfig] = useState(null)
  const [saved, setSaved] = useState(false)

  const isDark = settings.theme === 'dark'

  useEffect(() => {
    api.getSettings().then(setServerConfig).catch(() => null)
  }, [])

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const tabs = [
    { id: 'display', label: 'Clay Theme', icon: Palette, desc: 'Light & True Dark Mode', highlight: true },
    { id: 'trading', label: 'Trading', icon: DollarSign, desc: 'Risk & position management' },
    { id: 'models', label: 'Models', icon: Brain, desc: 'AI model weights & config' },
    { id: 'notifications', label: 'Alerts', icon: Bell, desc: 'Notification settings' },
    { id: 'advanced', label: 'Advanced', icon: Sliders, desc: 'System configuration' },
  ]

  return (
    <div className="min-h-screen relative font-poppins transition-colors duration-500">
      <div className="relative max-w-[1400px] mx-auto p-6 space-y-6">
        {/* Header - Clay */}
        <div className="clay-card p-6 flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3 font-poppins">
              <span className="w-12 h-12 rounded-[20px] bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg clay-float"
                style={isDark ? {
                  boxShadow: '0px 12px 24px rgba(0,0,0,0.5), inset 3px 3px 6px rgba(255,255,255,0.2)',
                  border: '1px solid rgba(255,255,255,0.08)'
                } : {
                  boxShadow: '0px 12px 24px rgba(31,38,135,0.08), inset 4px 4px 8px rgba(255,255,255,0.9)',
                  border: '1px solid rgba(255,255,255,0.4)'
                }}>
                <SettingsIcon size={22} className="text-white" />
              </span>
              <span style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>Claymorphism Settings</span>
              <span className="clay-pill px-4 py-1 text-xs font-black tracking-widest">V7 CLAY • PUFFY 3D</span>
            </h1>
            <p className="text-sm mt-2 font-poppins" style={{ color: isDark ? '#E5E7EB' : '#475569' }}>
              True Dark #000000 • Light Gradient #FFCFDF→#BBE1FA • Soft puffy 3D floating clay • Poppins • Dual inner shadows
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <button onClick={() => { settings.resetSettings(); handleSave() }} className="clay-card px-5 py-3 flex items-center gap-2 font-bold text-sm hover:scale-105 transition-all font-poppins">
              <RotateCcw size={16} />
              Reset Defaults
            </button>
            <button onClick={handleSave} className={`clay-btn-accent px-6 py-3 flex items-center gap-2 transition-all font-poppins ${saved ? 'scale-105' : ''}`}>
              <Save size={16} />
              {saved ? 'Saved! Clay' : 'Save Clay Config'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Tabs Sidebar - Clay */}
          <div className="lg:col-span-3 space-y-3">
            {tabs.map(tab => {
              const Icon = tab.icon
              const active = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left p-5 rounded-[24px] border transition-all duration-300 flex items-center gap-4 font-poppins hover:scale-[1.02] ${
                    active 
                      ? isDark
                        ? 'bg-white text-black shadow-[0px_12px_24px_rgba(0,0,0,0.3),inset_4px_4px_8px_rgba(255,255,255,0.9)] scale-[1.02]'
                        : 'bg-white text-black shadow-[0px_12px_24px_rgba(31,38,135,0.08),inset_4px_4px_8px_rgba(255,255,255,0.9)] scale-[1.02]'
                      : 'clay-card hover:scale-[1.01]'
                  } ${tab.highlight ? 'border-violet-500/20' : ''}`}
                >
                  <div className={`w-12 h-12 rounded-[16px] flex items-center justify-center transition-all ${
                    active ? 'bg-black text-white' : isDark ? 'bg-black/30 border border-white/10 text-[#9CA3AF]' : 'bg-white border border-white/40 text-[#64748b] shadow-sm'
                  }`}>
                    <Icon size={20} />
                  </div>
                  <div>
                    <div className="font-bold text-sm flex items-center gap-2">
                      {tab.label}
                      {tab.highlight && <span className="clay-pill px-2 py-0.5 bg-violet-500 text-white text-[9px]">NEW CLAY</span>}
                    </div>
                    <div className={`text-xs ${active ? 'text-black/60' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>{tab.desc}</div>
                  </div>
                </button>
              )
            })}

            <GlassCard className="p-5 mt-6">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles size={16} className="text-violet-500" />
                <span className="text-xs font-bold tracking-widest uppercase font-poppins" style={{ color: isDark ? '#a78bfa' : '#7c3aed' }}>Claymorphism Rules</span>
              </div>
              <div className="text-[11px] leading-relaxed font-poppins space-y-2" style={{ color: isDark ? '#E5E7EB' : '#475569' }}>
                <div>• <span className="font-bold">Rule 1:</span> True Dark uses off-white #F3F4F6, never pure #FFFFFF for long text</div>
                <div>• <span className="font-bold">Rule 2:</span> Hover → inner highlight 0.12→0.2, moves closer to light</div>
                <div>• <span className="font-bold">Rule 3:</span> Flat pure black walls #000000, clay only for widgets/CTA/cards</div>
                <div>• <span className="font-bold">Rule 4:</span> Poppins/Inter/Quicksand rounded fonts, 24-40px radius</div>
              </div>
            </GlassCard>
          </div>

          {/* Content */}
          <div className="lg:col-span-9 space-y-6">
            {activeTab === 'display' && (
              <>
                <GlassCard className="p-8">
                  <h3 className="font-black text-xl flex items-center gap-3 mb-8 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                    <span className="w-10 h-10 rounded-[16px] bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                      <Palette size={20} className="text-white" />
                    </span>
                    Claymorphism Theme • Light & True Dark Mode
                    <span className="clay-pill px-3 py-1 bg-violet-500 text-white text-xs">V7 NEW</span>
                  </h3>
                  
                  {/* Theme Toggle Showcase */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                    {/* Light Mode Card Preview */}
                    <div className="clay-card-light p-6 cursor-pointer group" onClick={() => settings.updateTheme('light')}>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-[16px] bg-gradient-to-br from-[#FFCFDF] to-[#BBE1FA] flex items-center justify-center shadow-lg">
                            <Sun size={20} className="text-[#1e293b]" />
                          </div>
                          <div>
                            <div className="font-black text-[#1e293b] font-poppins">Light Mode</div>
                            <div className="text-xs text-[#64748b] font-poppins">Pastel Canvas</div>
                          </div>
                        </div>
                        <div className={`w-14 h-8 rounded-full p-1 transition-all ${settings.theme === 'light' ? 'bg-emerald-500' : 'bg-gray-200'}`}>
                          <div className={`w-6 h-6 rounded-full bg-white shadow-md transition-all ${settings.theme === 'light' ? 'translate-x-6' : ''}`}></div>
                        </div>
                      </div>
                      <div className="text-xs text-[#475569] font-poppins leading-relaxed">
                        Canvas: linear-gradient(135deg, #FFCFDF 0%, #BBE1FA 100%) or solid #E3EDF7 • 
                        Card: #ffffff • Border: rgba(255,255,255,0.4) • 
                        Shadow: 0px 20px 40px rgba(31,38,135,0.08) + dual inset
                      </div>
                      <div className="mt-4 flex gap-2">
                        <span className="px-3 py-1 rounded-full bg-[#FFCFDF]/30 text-[#be185d] text-[10px] font-bold">#FFCFDF</span>
                        <span className="px-3 py-1 rounded-full bg-[#BBE1FA]/50 text-[#1e40af] text-[10px] font-bold">#BBE1FA</span>
                      </div>
                    </div>

                    {/* True Dark Mode Card Preview */}
                    <div className="clay-card-dark p-6 cursor-pointer group" onClick={() => settings.updateTheme('dark')}>
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-[16px] bg-[#000000] border border-white/10 flex items-center justify-center shadow-lg">
                            <Moon size={20} className="text-[#F3F4F6]" />
                          </div>
                          <div>
                            <div className="font-black text-[#F3F4F6] font-poppins">True Dark Mode</div>
                            <div className="text-xs text-[#9CA3AF] font-poppins">Pure Black #000000</div>
                          </div>
                        </div>
                        <div className={`w-14 h-8 rounded-full p-1 transition-all ${settings.theme === 'dark' ? 'bg-emerald-500' : 'bg-gray-700'}`}>
                          <div className={`w-6 h-6 rounded-full bg-white shadow-md transition-all ${settings.theme === 'dark' ? 'translate-x-6' : ''}`}></div>
                        </div>
                      </div>
                      <div className="text-xs text-[#E5E7EB] font-poppins leading-relaxed">
                        Canvas: #000000 pure black • Card: rgba(28,28,30,0.7) translucent slate • 
                        Border: rgba(255,255,255,0.08) • 
                        Shadow: 0px 20px 40px rgba(0,0,0,0.6) + inset 4px highlight 0.12 + inset -4px volume 0.5
                      </div>
                      <div className="mt-4 flex gap-2">
                        <span className="px-3 py-1 rounded-full bg-black border border-white/10 text-[#F3F4F6] text-[10px] font-bold">#000000</span>
                        <span className="px-3 py-1 rounded-full bg-[#1c1c1e] border border-white/10 text-[#9CA3AF] text-[10px] font-bold">rgba(28,28,30,0.7)</span>
                      </div>
                    </div>
                  </div>

                  {/* Shadow Blueprint */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="p-6 rounded-[24px]" style={{ 
                      background: isDark ? 'rgba(0,0,0,0.3)' : '#f8fafc',
                      border: isDark ? '1px solid rgba(255,255,255,0.06)' : '1px solid rgba(255,255,255,0.4)'
                    }}>
                      <div className="text-xs font-black tracking-widest uppercase mb-3 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>Light Mode Shadow Blueprint</div>
                      <pre className="text-[11px] p-4 rounded-[16px] overflow-x-auto font-mono" style={{ 
                        background: isDark ? '#000000' : '#ffffff',
                        color: isDark ? '#E5E7EB' : '#1e293b',
                        border: isDark ? '1px solid rgba(255,255,255,0.06)' : '1px solid rgba(0,0,0,0.05)'
                      }}>
{`box-shadow: 
  0px 20px 40px rgba(31,38,135,0.08),
  inset 6px 6px 12px rgba(255,255,255,0.9),
  inset -6px -6px 12px rgba(0,0,0,0.1);`}
                      </pre>
                      <div className="mt-3 text-[11px] font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
                        • Outer: lifts off canvas • Inner highlight top-left matte reflection • Inner shadow bottom-right thickness
                      </div>
                    </div>

                    <div className="p-6 rounded-[24px]" style={{ 
                      background: isDark ? 'rgba(0,0,0,0.3)' : '#f8fafc',
                      border: isDark ? '1px solid rgba(255,255,255,0.06)' : '1px solid rgba(255,255,255,0.4)'
                    }}>
                      <div className="text-xs font-black tracking-widest uppercase mb-3 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>True Dark Shadow Blueprint</div>
                      <pre className="text-[11px] p-4 rounded-[16px] overflow-x-auto font-mono" style={{ 
                        background: '#000000',
                        color: '#E5E7EB',
                        border: '1px solid rgba(255,255,255,0.08)'
                      }}>
{`background: rgba(28,28,30,0.7);
backdrop-filter: blur(8px);
box-shadow: 
  0px 20px 40px rgba(0,0,0,0.6),
  inset 4px 4px 8px rgba(255,255,255,0.12),
  inset -4px -4px 8px rgba(0,0,0,0.5);`}
                      </pre>
                      <div className="mt-3 text-[11px] font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
                        • Pure black canvas needs translucent slate + glowing ambient outer + crisp inner edge • Hover: highlight 0.12→0.2
                      </div>
                    </div>
                  </div>

                  <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { title: 'Corner Radius', desc: '24px to 40px • Heavily rounded or full pills • Sharp corners destroy squishy effect', icon: '◐' },
                      { title: 'Typography', desc: 'Poppins, Inter, Quicksand • Bold, rounded, clean geometric sans-serif • Modern fluid', icon: 'Aa' },
                      { title: 'Visual Hierarchy', desc: 'Flat pure black walls #000000 • Clay only for widgets, CTA, data cards • Restrain style', icon: '◧' },
                    ].map((item, i) => (
                      <div key={i} className="clay-card p-5">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">{item.icon}</span>
                          <span className="font-bold text-sm font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>{item.title}</span>
                        </div>
                        <div className="text-xs leading-relaxed font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>{item.desc}</div>
                      </div>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard className="p-6">
                  <h3 className="font-bold flex items-center gap-2 mb-6 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                    <Palette size={20} className="text-violet-500" />
                    Display & Chart Preferences • Claymorphism
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="text-xs font-bold tracking-widest uppercase mb-2 block font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Default Symbol • Clay</label>
                      <select value={settings.defaultSymbol} onChange={e => useSettingsStore.setState({ defaultSymbol: e.target.value })} className="clay-input w-full px-4 py-3">
                        <option value="BTC-USD">BTC-USD • Bitcoin • Clay 3D</option>
                        <option value="ETH-USD">ETH-USD • Ethereum • Puffy</option>
                        <option value="SOL-USD">SOL-USD • Solana • Clay</option>
                        <option value="BNB-USD">BNB-USD • Binance • 3D</option>
                        <option value="XRP-USD">XRP-USD • Ripple • Clay</option>
                        <option value="ADA-USD">ADA-USD • Cardano • Puffy</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="text-xs font-bold tracking-widest uppercase mb-2 block font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Chart Type • Clay</label>
                      <select value={settings.chartType} onChange={e => useSettingsStore.setState({ chartType: e.target.value })} className="clay-input w-full px-4 py-3">
                        <option value="candlestick">Candlestick • Clay Professional</option>
                        <option value="line">Line • Minimal Clay</option>
                        <option value="area">Area • Gradient Clay</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-6">
                    {[
                      { key: 'showVolume', label: 'Show Volume • Clay', desc: 'Display volume bars • Puffy 3D' },
                      { key: 'showForecast', label: 'Show Forecast • Clay', desc: 'AI prediction line • Clay' },
                      { key: 'showAdvanced', label: 'Advanced Mode • Clay', desc: 'Show all indicators • 3D' },
                      { key: 'autoRefresh', label: 'Auto Refresh • Clay', desc: 'Live data updates • Clay' },
                    ].map(item => (
                      <div key={item.key} className="clay-card p-4 flex items-center justify-between">
                        <div>
                          <div className="font-bold text-sm font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>{item.label}</div>
                          <div className="text-xs mt-1 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>{item.desc}</div>
                        </div>
                        <button 
                          onClick={() => useSettingsStore.setState({ [item.key]: !settings[item.key] })}
                          className={`w-14 h-8 rounded-full p-1 transition-all duration-300 ${settings[item.key] ? 'bg-emerald-500 shadow-lg' : isDark ? 'bg-black border border-white/10' : 'bg-gray-200'}`}
                        >
                          <div className={`w-6 h-6 rounded-full bg-white shadow-md transition-all duration-300 ${settings[item.key] ? 'translate-x-6' : ''}`}></div>
                        </button>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </>
            )}

            {activeTab === 'trading' && (
              <>
                <GlassCard className="p-6">
                  <h3 className="font-bold flex items-center gap-2 mb-6 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                    <DollarSign size={20} className="text-emerald-500" />
                    Account & Risk Management • Clay 3D
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="text-xs font-bold tracking-widest uppercase mb-2 block font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Account Balance (USDT) • Clay</label>
                      <div className="relative">
                        <DollarSign size={16} className="absolute left-4 top-1/2 -translate-y-1/2" style={{ color: isDark ? '#9CA3AF' : '#64748b' }} />
                        <input 
                          type="number"
                          value={settings.accountBalance}
                          onChange={e => settings.updateAccountBalance(parseFloat(e.target.value) || 0)}
                          className="clay-input w-full pl-12 pr-4 py-3 font-bold mono"
                        />
                      </div>
                      <div className="text-[11px] mt-2 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Used for position size calculation • Clay 3D</div>
                    </div>
                    
                    <div>
                      <label className="text-xs font-bold tracking-widest uppercase mb-2 block font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Risk Per Trade • Clay Puffy</label>
                      <div className="grid grid-cols-4 gap-3">
                        {[0.01, 0.02, 0.03, 0.05].map(risk => (
                          <button
                            key={risk}
                            onClick={() => settings.updateRiskPerTrade(risk)}
                            className={`py-3 rounded-[20px] border font-bold text-sm transition-all duration-300 font-poppins hover:scale-105 ${
                              settings.riskPerTrade === risk
                                ? 'bg-white text-black border-white shadow-[0px_8px_16px_rgba(0,0,0,0.15),inset_3px_3px_6px_rgba(255,255,255,0.9)] scale-105'
                                : 'clay-card hover:scale-105'
                            }`}
                          >
                            {risk * 100}%
                          </button>
                        ))}
                      </div>
                      <div className="text-[11px] mt-2 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
                        ${settings.accountBalance * settings.riskPerTrade} risk per trade • Clay
                      </div>
                    </div>
                  </div>

                  <div className="mt-6">
                    <label className="text-xs font-bold tracking-widest uppercase mb-3 block font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Risk Tolerance Preset • Claymorphism</label>
                    <div className="grid grid-cols-3 gap-4">
                      {[
                        { id: 'conservative', label: 'Conservative • Clay', desc: '1% risk • Stable models • Puffy', risk: '1% CLAY', color: 'emerald' },
                        { id: 'moderate', label: 'Moderate • Clay 3D', desc: '2% risk • Balanced • Clay', risk: '2% CLAY', color: 'blue' },
                        { id: 'aggressive', label: 'Aggressive • Puffy', desc: '5% risk • High growth • 3D', risk: '5% CLAY', color: 'red' },
                      ].map(preset => (
                        <button
                          key={preset.id}
                          onClick={() => settings.setRiskPreset(preset.id)}
                          className={`p-5 rounded-[24px] border text-left transition-all duration-300 font-poppins hover:scale-[1.02] ${
                            settings.riskTolerance === preset.id
                              ? 'bg-white border-white text-black shadow-[0px_12px_24px_rgba(0,0,0,0.15),inset_4px_4px_8px_rgba(255,255,255,0.9)] scale-[1.02]'
                              : 'clay-card hover:scale-[1.02]'
                          }`}
                        >
                          <div className="font-bold text-sm">{preset.label}</div>
                          <div className={`text-xs mt-1 ${settings.riskTolerance === preset.id ? 'text-black/60' : isDark ? 'text-[#9CA3AF]' : 'text-[#64748b]'}`}>{preset.desc}</div>
                          <div className="mt-3 clay-pill px-3 py-1 text-[10px] font-black inline-block bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
                            {preset.risk} RISK • CLAY
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </GlassCard>
              </>
            )}

            {activeTab === 'models' && (
              <GlassCard className="p-6">
                <h3 className="font-bold flex items-center gap-2 mb-6 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                  <Brain size={20} className="text-violet-500" />
                  AI Model Configuration • Clay Ensemble v3
                </h3>
                <div className="text-sm font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
                  Claymorphism styling applied to all model cards • Puffy 3D • True Dark #000000 • Light Pastel
                </div>
              </GlassCard>
            )}

            {activeTab === 'notifications' && (
              <GlassCard className="p-6">
                <h3 className="font-bold flex items-center gap-2 mb-6 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                  <Bell size={20} className="text-amber-500" />
                  Notifications & Alerts • Clay 3D
                </h3>
                <div className="text-sm font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>
                  Claymorphic notification cards • Puffy • True Dark #000000
                </div>
              </GlassCard>
            )}

            {activeTab === 'advanced' && (
              <GlassCard className="p-6">
                <h3 className="font-bold flex items-center gap-2 mb-6 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>
                  <Sliders size={20} className="text-violet-500" />
                  Advanced Configuration • Claymorphism v7
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="clay-card p-5 text-center">
                    <div className="text-xs uppercase tracking-widest font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Version • Clay</div>
                    <div className="font-black mt-2 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>v7.0 • Claymorphism Edition</div>
                    <div className="text-xs mt-1 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>True Dark #000000 • Light #FFCFDF→#BBE1FA • Puffy 3D</div>
                  </div>
                  <div className="clay-card p-5 text-center">
                    <div className="text-xs uppercase tracking-widest font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Design System • Clay</div>
                    <div className="font-black mt-2 font-poppins" style={{ color: isDark ? '#F3F4F6' : '#1e293b' }}>Poppins • 32px Radius • Dual Shadows</div>
                    <div className="text-xs mt-1 font-poppins" style={{ color: isDark ? '#9CA3AF' : '#64748b' }}>Outer 20px/40px • Inner 6px highlight • Volume -6px</div>
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
