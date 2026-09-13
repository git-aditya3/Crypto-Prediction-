import { useState, useEffect } from 'react'
import GlassCard, { FeatureCard, MetricCard } from '../components/GlassCard'
import { useSettingsStore, THEMES, THEME_CATEGORIES } from '../store/useSettingsStore'
import { api } from '../api/client'
import { Settings as SettingsIcon, DollarSign, Brain, Bell, Palette, Save, RotateCcw, Sliders, Sun, Moon, Sparkles, Monitor, Zap, Eye, Layers, Type, Droplets, Wand2, Check, Paintbrush, Layout, MousePointer } from 'lucide-react'

export default function SettingsPage() {
  const settings = useSettingsStore()
  const [activeTab, setActiveTab] = useState('themes')
  const [saved, setSaved] = useState(false)
  const [themeCategory, setThemeCategory] = useState('All')
  const currentTheme = THEMES[settings.theme] || THEMES.dark
  const isLight = ['light', 'sakura', 'mono'].includes(settings.theme)

  useEffect(() => { api.getSettings().catch(() => null) }, [])

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }

  const tabs = [
    { id: 'themes', label: 'Themes', icon: Palette, desc: `${Object.keys(THEMES).length} themes`, color: 'from-violet-500 to-pink-500' },
    { id: 'appearance', label: 'Appearance', icon: Eye, desc: 'Visual tweaks', color: 'from-cyan-500 to-blue-500' },
    { id: 'trading', label: 'Trading', icon: DollarSign, desc: 'Risk & balance', color: 'from-emerald-500 to-teal-500' },
    { id: 'models', label: 'Models', icon: Brain, desc: 'AI weights', color: 'from-orange-500 to-red-500' },
    { id: 'interface', label: 'Interface', icon: Layout, desc: 'Layout & UX', color: 'from-blue-500 to-violet-500' },
    { id: 'advanced', label: 'Advanced', icon: Sliders, desc: 'System', color: 'from-zinc-500 to-zinc-700' },
  ]

  const filteredThemes = themeCategory === 'All' ? Object.values(THEMES) : Object.values(THEMES).filter(t => t.category === themeCategory)

  const accentColors = [
    { id: 'emerald', name: 'Emerald', color: '#10b981' },
    { id: 'violet', name: 'Violet', color: '#8b5cf6' },
    { id: 'cyan', name: 'Cyan', color: '#06b6d4' },
    { id: 'orange', name: 'Orange', color: '#f97316' },
    { id: 'pink', name: 'Pink', color: '#ec4899' },
    { id: 'blue', name: 'Blue', color: '#3b82f6' },
  ]

  return (
    <div className={`min-h-screen font-poppins theme-bg ${isLight ? '' : ''}`}>
      <div className="max-w-[1600px] mx-auto p-4 md:p-6 space-y-6">
        {/* Header */}
        <div className="ui-card p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-4 overflow-hidden relative">
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent)]/5 via-transparent to-transparent pointer-events-none" />
          <div className="flex items-center gap-4 relative z-10">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center shadow-lg ${isLight ? 'bg-black text-white' : 'bg-white text-black'} animate-pulse`}>
              <SettingsIcon size={20} />
            </div>
            <div>
              <h1 className={`text-2xl font-black tracking-tight flex items-center gap-3 ${isLight ? 'text-black' : 'text-white'}`}>
                Settings
                <span className="ui-pill-accent text-[10px] px-2.5 py-1 font-black">{Object.keys(THEMES).length} THEMES</span>
                <span className={`hidden md:inline-flex text-[10px] px-2.5 py-1 rounded-full border font-bold ${currentTheme.preview}`}>{currentTheme.icon} {currentTheme.name}</span>
              </h1>
              <p className={`text-[13px] mt-1 ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Customize everything • {currentTheme.desc} • Real trading preferences</p>
            </div>
          </div>
          <div className="flex items-center gap-2 relative z-10">
            <button onClick={() => { settings.resetSettings(); handleSave() }} className="ui-btn ui-btn-ghost px-4 py-2.5 text-[12px] font-semibold flex items-center gap-2">
              <RotateCcw size={14} /> Reset
            </button>
            <button onClick={handleSave} className={`px-5 py-2.5 rounded-xl text-[12px] font-bold flex items-center gap-2 shadow-lg hover:shadow-xl hover:scale-105 transition-all ${isLight ? 'bg-black text-white' : 'bg-white text-black'}`}>
              <Save size={14} /> {saved ? 'Saved ✓' : 'Save Changes'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-3 space-y-3">
            {tabs.map(tab => {
              const active = activeTab === tab.id
              return (
                <button 
                  key={tab.id} 
                  onClick={() => setActiveTab(tab.id)} 
                  className={`w-full text-left p-4 rounded-xl border flex items-center gap-3 transition-all group hover:scale-[1.02] hover:shadow-lg relative overflow-hidden ${
                    active 
                      ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)] shadow-lg shadow-[var(--accent)]/20 scale-[1.02]' 
                      : 'ui-card hover:border-[var(--accent)]/30'
                  }`}
                >
                  {active && <div className="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent pointer-events-none" />}
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all group-hover:scale-110 group-hover:rotate-3 shrink-0 ${active ? 'bg-black/20 text-white' : `bg-gradient-to-br ${tab.color} text-white shadow-md`}`}>
                    <tab.icon size={18} />
                  </div>
                  <div className="flex-1 min-w-0 relative z-10">
                    <div className="font-bold text-[13px] flex items-center gap-2">
                      {tab.label}
                      {active && <Check size={12} className="bg-white text-black rounded-full p-0.5 w-4 h-4" />}
                    </div>
                    <div className={`text-[11px] ${active ? 'text-white/70' : isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>{tab.desc}</div>
                  </div>
                </button>
              )
            })}

            {/* Quick stats */}
            <GlassCard className="p-4">
              <div className={`text-[10px] font-bold uppercase tracking-wide mb-3 ${isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>Current Setup</div>
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className={`text-[12px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Theme</span>
                  <span className={`text-[12px] font-bold px-2 py-1 rounded-full border ${currentTheme.preview}`}>{currentTheme.icon} {currentTheme.name}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`text-[12px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Balance</span>
                  <span className={`text-[12px] font-bold mono ${isLight ? 'text-black' : 'text-white'}`}>${settings.accountBalance}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={`text-[12px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Risk</span>
                  <span className="text-[12px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">{settings.riskPerTrade*100}%</span>
                </div>
              </div>
            </GlassCard>
          </div>

          {/* Content */}
          <div className="lg:col-span-9 space-y-5">
            {activeTab === 'themes' && (
              <>
                {/* Category filter */}
                <GlassCard className="p-4">
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <h3 className={`font-bold flex items-center gap-2 ${isLight ? 'text-black' : 'text-white'}`}>
                      <Paintbrush size={16} className="text-[var(--accent)]" /> Theme Gallery • {Object.keys(THEMES).length} themes
                    </h3>
                    <div className="flex gap-1.5 p-1 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                      {THEME_CATEGORIES.map(cat => (
                        <button
                          key={cat}
                          onClick={() => setThemeCategory(cat)}
                          className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all ${themeCategory === cat ? 'bg-[var(--accent)] text-[var(--bg)] shadow-md' : isLight ? 'text-zinc-600 hover:text-black hover:bg-white' : 'text-zinc-400 hover:text-white hover:bg-white/10'}`}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  </div>
                </GlassCard>

                {/* Theme grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredThemes.map(t => {
                    const active = settings.theme === t.id
                    return (
                      <div
                        key={t.id}
                        onClick={() => settings.updateTheme(t.id)}
                        className={`group p-5 rounded-2xl border cursor-pointer transition-all duration-300 hover:scale-[1.02] hover:shadow-xl relative overflow-hidden ${
                          active 
                            ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)] shadow-xl shadow-[var(--accent)]/20 scale-[1.02] ring-2 ring-[var(--accent)]/30' 
                            : 'ui-card hover:border-[var(--accent)]/30'
                        }`}
                      >
                        {/* Preview */}
                        <div className={`w-full h-24 rounded-xl border-2 mb-4 relative overflow-hidden transition-all group-hover:scale-[1.02] ${t.preview} flex items-center justify-center`}>
                          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
                          <div className="text-2xl relative z-10 group-hover:scale-125 transition-transform">{t.icon}</div>
                          <div className="absolute top-2 left-2 w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                          <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded-full bg-black/20 text-white text-[8px] font-bold">{t.category}</div>
                          <div className="absolute bottom-2 left-2 right-2 h-1 rounded-full bg-white/20 overflow-hidden">
                            <div className="h-full w-2/3 bg-white/60 rounded-full animate-pulse" />
                          </div>
                        </div>

                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="font-bold text-[14px] flex items-center gap-2">
                              {t.name}
                              {active && <Check size={14} className="bg-white text-black rounded-full p-0.5 w-5 h-5 animate-scaleIn" />}
                            </div>
                            <div className={`text-[12px] mt-1 ${active ? 'text-white/70' : isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>{t.desc}</div>
                            <div className="flex gap-1 mt-2">
                              {Object.values(t.colors).slice(0, 4).map((c, i) => (
                                <div key={i} className="w-4 h-4 rounded-full border border-white/20 shadow-sm" style={{ background: c }} />
                              ))}
                            </div>
                          </div>
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${active ? 'bg-black/20 text-white rotate-12' : 'bg-[var(--accent-soft)] text-[var(--text-muted)] group-hover:bg-[var(--accent)] group-hover:text-[var(--bg)] group-hover:rotate-12'}`}>
                            <Palette size={14} />
                          </div>
                        </div>

                        {active && <div className="absolute inset-0 bg-gradient-to-r from-white/5 to-transparent pointer-events-none" />}
                      </div>
                    )
                  })}
                </div>

                {/* Accent colors */}
                <GlassCard className="p-6">
                  <h3 className={`font-bold flex items-center gap-2 mb-4 ${isLight ? 'text-black' : 'text-white'}`}>
                    <Droplets size={16} className="text-[var(--accent)]" /> Accent Color
                  </h3>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                    {accentColors.map(a => (
                      <button
                        key={a.id}
                        onClick={() => settings.updateAccent(a.id)}
                        className={`group p-4 rounded-xl border transition-all hover:scale-105 hover:shadow-lg text-center relative overflow-hidden ${settings.accent === a.id ? 'border-[var(--accent)] ring-2 ring-[var(--accent)]/20 shadow-lg scale-105' : 'border-[var(--border)] hover:border-[var(--accent)]/30'}`}
                      >
                        <div className="w-8 h-8 rounded-full mx-auto mb-2 shadow-md group-hover:scale-110 transition-transform" style={{ background: a.color, boxShadow: `0 0 20px ${a.color}40` }} />
                        <div className={`text-[11px] font-bold ${isLight ? 'text-black' : 'text-white'}`}>{a.name}</div>
                        {settings.accent === a.id && <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />}
                      </button>
                    ))}
                  </div>
                </GlassCard>
              </>
            )}

            {activeTab === 'appearance' && (
              <>
                <GlassCard className="p-6">
                  <h3 className={`font-bold flex items-center gap-2 mb-6 ${isLight ? 'text-black' : 'text-white'}`}><Eye size={16} className="text-[var(--accent)]" /> Visual Preferences</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wide ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>Font Family</label>
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          {[
                            { id: 'poppins', name: 'Poppins', desc: 'Modern' },
                            { id: 'inter', name: 'Inter', desc: 'Clean' },
                            { id: 'space', name: 'Space Grotesk', desc: 'Tech' },
                            { id: 'outfit', name: 'Outfit', desc: 'Soft' },
                          ].map(f => (
                            <button key={f.id} onClick={() => settings.updateFont(f.id)} className={`p-3 rounded-xl border text-left transition-all hover:scale-[1.02] ${settings.font === f.id ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)] shadow-md' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--accent)]/30'}`}>
                              <div className="font-bold text-[13px]">{f.name}</div>
                              <div className={`text-[10px] ${settings.font === f.id ? 'text-white/70' : 'text-zinc-500'}`}>{f.desc}</div>
                            </button>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className={`text-[11px] font-bold uppercase tracking-wide ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>Density</label>
                        <div className="grid grid-cols-3 gap-2 mt-2">
                          {[
                            { id: 'compact', name: 'Compact', icon: '◫' },
                            { id: 'comfortable', name: 'Comfortable', icon: '◧' },
                            { id: 'spacious', name: 'Spacious', icon: '◩' },
                          ].map(d => (
                            <button key={d.id} onClick={() => settings.updateDensity(d.id)} className={`p-3 rounded-xl border text-center transition-all hover:scale-105 ${settings.density === d.id ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)]' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--accent)]/30'}`}>
                              <div className="text-[16px]">{d.icon}</div>
                              <div className="text-[11px] font-bold mt-1">{d.name}</div>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      {[
                        { key: 'animations', label: 'Animations', desc: 'Smooth transitions & micro-interactions', icon: Zap },
                        { key: 'blur', label: 'Blur Effects', desc: 'Glass morphism & backdrop blur', icon: Droplets },
                        { key: 'showMarketTicker', label: 'Market Ticker', desc: 'Top scrolling price ticker', icon: Monitor },
                        { key: 'sidebarCollapsed', label: 'Compact Sidebar', desc: 'Collapsed navigation', icon: Layout },
                      ].map(item => (
                        <div key={item.key} className={`p-4 rounded-xl border flex items-center justify-between group hover:border-[var(--accent)]/30 transition-all hover:shadow-md ${isLight ? 'bg-white border-black/5' : 'bg-zinc-900 border-white/5'}`}>
                          <div className="flex items-center gap-3">
                            <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${isLight ? 'bg-black text-white' : 'bg-white text-black'} group-hover:scale-110 transition-transform`}>
                              <item.icon size={16} />
                            </div>
                            <div>
                              <div className={`text-[13px] font-semibold ${isLight ? 'text-black' : 'text-white'}`}>{item.label}</div>
                              <div className={`text-[11px] ${isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>{item.desc}</div>
                            </div>
                          </div>
                          <button onClick={() => useSettingsStore.setState({ [item.key]: !settings[item.key] })} className={`w-11 h-6 rounded-full p-1 transition-all duration-300 ${settings[item.key] ? 'bg-[var(--accent)] shadow-lg' : 'bg-zinc-300 dark:bg-zinc-700'} hover:scale-105`}>
                            <div className={`w-4 h-4 rounded-full bg-white shadow-md transition-transform duration-300 ${settings[item.key] ? 'translate-x-5' : ''}`} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </GlassCard>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <MetricCard label="Themes" value={`${Object.keys(THEMES).length}`} change="+4 new" icon={Palette} />
                  <MetricCard label="Current" value={currentTheme.name} change={currentTheme.category} icon={Sparkles} />
                  <MetricCard label="Accent" value={settings.accent} change="Custom" icon={Droplets} />
                </div>
              </>
            )}

            {activeTab === 'trading' && (
              <GlassCard className="p-6">
                <h3 className={`font-bold flex items-center gap-2 mb-6 ${isLight ? 'text-black' : 'text-white'}`}><DollarSign size={16} className="text-emerald-500" /> Trading Preferences • Real Money</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <label className={`text-[11px] font-bold uppercase tracking-wide ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>Account Balance (USDT)</label>
                      <input type="number" value={settings.accountBalance} onChange={e => settings.updateAccountBalance(parseFloat(e.target.value)||0)} className="ui-input mt-2 font-bold mono text-lg" />
                      <div className={`text-[10px] mt-1 ${isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>Used for position sizing • Real trading</div>
                    </div>
                    <div>
                      <label className={`text-[11px] font-bold uppercase tracking-wide ${isLight ? 'text-zinc-500' : 'text-zinc-400'}`}>Risk Per Trade</label>
                      <div className="grid grid-cols-4 gap-2 mt-2">
                        {[0.01,0.02,0.03,0.05].map(r => (
                          <button key={r} onClick={() => settings.updateRiskPerTrade(r)} className={`py-3 rounded-xl text-[12px] font-bold border transition-all hover:scale-105 ${settings.riskPerTrade===r ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)] shadow-lg scale-105' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--accent)]/30'}`}>
                            {r*100}%
                            <div className={`text-[9px] mt-0.5 ${settings.riskPerTrade===r ? 'text-white/70' : 'text-zinc-500'}`}>${(settings.accountBalance*r).toFixed(0)}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className={`p-4 rounded-xl border ${isLight ? 'bg-amber-50 border-amber-200' : 'bg-amber-500/5 border-amber-500/20'}`}>
                    <div className={`font-bold text-[13px] flex items-center gap-2 ${isLight ? 'text-amber-800' : 'text-amber-400'}`}>
                      <MousePointer size={14} /> How Position Sizing Works
                    </div>
                    <div className={`text-[11px] mt-2 space-y-1 ${isLight ? 'text-amber-700' : 'text-amber-300/70'}`}>
                      <div>• Risk = Balance × Risk% = ${settings.accountBalance} × {settings.riskPerTrade*100}% = ${(settings.accountBalance*settings.riskPerTrade).toFixed(0)}</div>
                      <div>• Quantity = Risk / |Entry - SL|</div>
                      <div>• Never risk more than 2% per trade</div>
                      <div>• Max 6% daily loss recommended</div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            )}

            {activeTab === 'interface' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FeatureCard icon={Layout} title="Layout" desc="Density & spacing" badge="NEW">
                  <div className="grid grid-cols-3 gap-2">
                    {['compact','comfortable','spacious'].map(d => (
                      <button key={d} onClick={() => settings.updateDensity(d)} className={`p-2 rounded-lg border text-[11px] font-bold capitalize ${settings.density===d ? 'bg-[var(--accent)] text-[var(--bg)] border-[var(--accent)]' : 'border-[var(--border)]'}`}>{d}</button>
                    ))}
                  </div>
                </FeatureCard>
                <FeatureCard icon={Wand2} title="Effects" desc="Visual enhancements">
                  <div className="space-y-2">
                    <label className="flex items-center justify-between p-2 rounded-lg bg-[var(--accent-soft)] border border-[var(--border)]">
                      <span className="text-[12px] font-medium">Animations</span>
                      <input type="checkbox" checked={settings.animations} onChange={() => settings.toggleAnimations()} />
                    </label>
                    <label className="flex items-center justify-between p-2 rounded-lg bg-[var(--accent-soft)] border border-[var(--border)]">
                      <span className="text-[12px] font-medium">Blur</span>
                      <input type="checkbox" checked={settings.blur} onChange={() => settings.toggleBlur()} />
                    </label>
                  </div>
                </FeatureCard>
              </div>
            )}

            {activeTab !== 'themes' && activeTab !== 'appearance' && activeTab !== 'trading' && activeTab !== 'interface' && (
              <GlassCard className="p-8 text-center">
                <div className={`w-16 h-16 rounded-2xl mx-auto flex items-center justify-center mb-4 ${isLight ? 'bg-black text-white' : 'bg-white text-black'}`}>
                  <Sliders size={24} />
                </div>
                <h3 className={`font-bold text-lg ${isLight ? 'text-black' : 'text-white'}`}>{activeTab} settings</h3>
                <p className={`text-[13px] mt-2 max-w-md mx-auto ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Advanced configuration for {activeTab} will appear here. More customization options coming soon with additional themes and layouts.</p>
                <div className="mt-6 flex justify-center gap-2">
                  <span className="ui-pill">Coming Soon</span>
                  <span className="ui-pill-accent">V8 Roadmap</span>
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
