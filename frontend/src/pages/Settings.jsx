import { useState, useEffect } from 'react'
import GlassCard from '../components/GlassCard'
import { useSettingsStore, THEMES, THEME_CATEGORIES } from '../store/useSettingsStore'
import { api } from '../api/client'
import { Settings as SettingsIcon, DollarSign, Palette, Save, RotateCcw, Eye, Type, Layout, Zap, Paintbrush, Droplets } from 'lucide-react'

export default function SettingsPage() {
  const settings = useSettingsStore()
  const [activeTab, setActiveTab] = useState('themes')
  const [saved, setSaved] = useState(false)
  const [themeCategory, setThemeCategory] = useState('All')
  const currentTheme = THEMES[settings.theme] || THEMES.dark

  useEffect(() => { api.getSettings().catch(() => null) }, [])

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }

  const tabs = [
    { id: 'themes', label: 'Themes', icon: Palette, desc: `${Object.keys(THEMES).length} themes` },
    { id: 'appearance', label: 'Appearance', icon: Eye, desc: 'Visual & motion' },
    { id: 'trading', label: 'Trading', icon: DollarSign, desc: 'Risk & balance' },
    { id: 'interface', label: 'Interface', icon: Layout, desc: 'Layout' },
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
    <div className="min-h-screen theme-bg">
      <div className="max-w-[1400px] mx-auto p-4 md:p-6 space-y-5">
        <div className="rounded-xl border bg-[var(--card)] border-[var(--border)] p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 gpu-accelerated relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent-soft)] to-transparent pointer-events-none" />
          <div className="flex items-center gap-3 relative z-10">
            <div className="w-10 h-10 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center shadow-[var(--glow)]">
              <SettingsIcon size={18} />
            </div>
            <div>
              <h1 className="text-[18px] font-semibold tracking-tight text-[var(--text)] flex items-center gap-2">
                Settings
                <span className="px-2.5 py-0.5 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold shadow-sm">{Object.keys(THEMES).length} THEMES</span>
                <span className={`hidden md:inline-flex text-[10px] px-2.5 py-1 rounded-full border font-medium ${currentTheme.preview}`}>{currentTheme.icon} {currentTheme.name}</span>
              </h1>
              <p className="text-[12px] mt-0.5 text-[var(--text-sec)]">{currentTheme.desc} • Themed colors • 120fps • Real trading</p>
            </div>
          </div>
          <div className="flex items-center gap-2 relative z-10">
            <button onClick={() => { settings.resetSettings(); handleSave() }} className="px-3 py-1.5 rounded-full border border-[var(--border)] text-[12px] font-medium text-[var(--text-sec)] hover:bg-[var(--bg-secondary)] transition-all duration-200 flex items-center gap-1.5 gpu-accelerated hover:scale-[1.02]">
              <RotateCcw size={12} /> Reset
            </button>
            <button onClick={handleSave} className="px-4 py-1.5 rounded-full bg-[var(--accent)] text-white text-[12px] font-medium hover:scale-[1.02] shadow-[var(--glow)] transition-all duration-200 gpu-accelerated flex items-center gap-1.5">
              <Save size={12} /> {saved ? 'Saved ✓' : 'Save'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-3 space-y-2">
            {tabs.map(tab => {
              const active = activeTab === tab.id
              return (
                <button 
                  key={tab.id} 
                  onClick={() => setActiveTab(tab.id)} 
                  className={`w-full text-left p-3 rounded-xl border flex items-center gap-2.5 transition-all duration-200 gpu-accelerated hover:scale-[1.01] ${
                    active 
                      ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' 
                      : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] text-[var(--text-sec)] hover:bg-[var(--bg-secondary)]'
                  }`}
                >
                  <tab.icon size={14} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-[13px]">{tab.label}</div>
                    <div className={`text-[11px] ${active ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>{tab.desc}</div>
                  </div>
                </button>
              )
            })}

            <div className="rounded-xl border bg-[var(--card)] border-[var(--border)] p-4">
              <div className="text-[10px] font-medium uppercase tracking-wide text-[var(--text-muted)] mb-3">Current Setup</div>
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[var(--text-muted)]">Theme</span>
                  <span className={`font-medium px-2 py-0.5 rounded-full border text-[11px] ${currentTheme.preview}`}>{currentTheme.icon} {currentTheme.name}</span>
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[var(--text-muted)]">Balance</span>
                  <span className="font-medium mono text-[var(--text)]">${settings.accountBalance}</span>
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[var(--text-muted)]">Risk</span>
                  <span className="font-medium px-2 py-0.5 rounded-full bg-[var(--buy)] text-white text-[11px] shadow-sm">{settings.riskPerTrade*100}%</span>
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[var(--text-muted)]">Accent</span>
                  <span className="w-4 h-4 rounded-full border border-[var(--border)] shadow-sm" style={{ background: currentTheme.colors.accent }} />
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-9 space-y-4">
            {activeTab === 'themes' && (
              <>
                <GlassCard className="p-4">
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2">
                      <Paintbrush size={14} className="text-[var(--accent)]" /> Theme Gallery • {Object.keys(THEMES).length} themes
                      <span className="px-2 py-0.5 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] text-[10px] text-[var(--accent)]">Colors suit theme</span>
                    </h3>
                    <div className="flex gap-1 p-1 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)]">
                      {THEME_CATEGORIES.map(cat => (
                        <button
                          key={cat}
                          onClick={() => setThemeCategory(cat)}
                          className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all ${themeCategory === cat ? 'bg-[var(--accent)] text-white shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text)]'}`}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  </div>
                </GlassCard>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 stagger-children">
                  {filteredThemes.map(t => {
                    const active = settings.theme === t.id
                    return (
                      <div
                        key={t.id}
                        onClick={() => settings.updateTheme(t.id)}
                        className={`group p-4 rounded-xl border cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:translate-y-[-1px] gpu-accelerated relative overflow-hidden ${
                          active 
                            ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)] ring-2 ring-[var(--accent-ring)]' 
                            : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)]'
                        }`}
                      >
                        <div className={`w-full h-20 rounded-lg border mb-3 relative overflow-hidden flex items-center justify-center text-[22px] transition-transform duration-200 group-hover:scale-[1.02] ${active ? 'bg-white/10 border-white/20' : t.preview} `}>
                          <span className="relative z-10 group-hover:scale-125 transition-transform duration-300">{t.icon}</span>
                          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
                          <div className="absolute top-2 left-2 w-1.5 h-1.5 rounded-full bg-[var(--buy)] animate-pulse" />
                          <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded-full bg-black/20 text-white text-[8px] font-bold">{t.category}</div>
                        </div>

                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-[13px] flex items-center gap-1.5">
                              {t.name}
                              {active && <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
                            </div>
                            <div className={`text-[11px] mt-1 truncate ${active ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>{t.desc}</div>
                            <div className="flex gap-1 mt-2">
                              {Object.values(t.colors).slice(0, 4).map((c, i) => (
                                <div key={i} className="w-4 h-4 rounded-full border border-white/20 shadow-sm" style={{ background: c }} />
                              ))}
                            </div>
                          </div>
                          <div className={`w-7 h-7 rounded-lg flex items-center justify-center transition-all ${active ? 'bg-white/20 text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-muted)] group-hover:bg-[var(--accent)] group-hover:text-white'}`}>
                            <Palette size={12} />
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>

                <GlassCard className="p-5">
                  <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2 mb-3">
                    <Droplets size={14} className="text-[var(--accent)]" /> Accent Color
                  </h3>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2.5">
                    {accentColors.map(a => (
                      <button
                        key={a.id}
                        onClick={() => settings.updateAccent(a.id)}
                        className={`group p-3 rounded-xl border text-center transition-all duration-200 hover:scale-105 gpu-accelerated ${settings.accent === a.id ? 'border-[var(--accent)] ring-2 ring-[var(--accent-ring)] shadow-[var(--glow)] scale-105' : 'border-[var(--border)] hover:border-[var(--border-strong)] bg-[var(--card)]'}`}
                      >
                        <div className="w-8 h-8 rounded-full mx-auto mb-1.5 shadow-md group-hover:scale-110 transition-transform duration-200" style={{ background: a.color, boxShadow: `0 0 20px ${a.color}40` }} />
                        <div className="text-[11px] font-medium text-[var(--text)]">{a.name}</div>
                      </button>
                    ))}
                  </div>
                </GlassCard>
              </>
            )}

            {activeTab === 'appearance' && (
              <>
                <GlassCard className="p-5">
                  <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2 mb-4">
                    <Eye size={14} className="text-[var(--accent)]" /> Visual Preferences
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div>
                        <label className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wide">Font</label>
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          {[
                            { id: 'poppins', name: 'Geist', desc: 'Modern' },
                            { id: 'inter', name: 'Inter', desc: 'Clean' },
                          ].map(f => (
                            <button key={f.id} onClick={() => settings.updateFont(f.id)} className={`p-3 rounded-xl border text-left transition-all duration-200 hover:scale-[1.02] gpu-accelerated ${settings.font === f.id ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)]'}`}>
                              <div className="font-medium text-[12px]">{f.name}</div>
                              <div className={`text-[10px] ${settings.font === f.id ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>{f.desc}</div>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2.5">
                      {[
                        { key: 'animations', label: '120fps Animations', desc: 'GPU accelerated', icon: Zap },
                        { key: 'blur', label: 'Glass Blur', desc: 'Backdrop blur', icon: Droplets },
                        { key: 'showMarketTicker', label: 'Market Ticker', desc: 'Top price scroll', icon: Layout },
                      ].map(item => (
                        <div key={item.key} className="p-3 rounded-lg border bg-[var(--card)] border-[var(--border)] flex items-center justify-between hover:border-[var(--border-strong)] transition-colors">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center shadow-sm">
                              <item.icon size={12} />
                            </div>
                            <div>
                              <div className="text-[12px] font-medium text-[var(--text)]">{item.label}</div>
                              <div className="text-[11px] text-[var(--text-muted)]">{item.desc}</div>
                            </div>
                          </div>
                          <button onClick={() => useSettingsStore.setState({ [item.key]: !settings[item.key] })} className={`w-9 h-5 rounded-full p-0.5 transition-all duration-200 gpu-accelerated ${settings[item.key] ? 'bg-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--bg-tertiary)]'}`}>
                            <div className={`w-4 h-4 rounded-full bg-white shadow-sm transition-transform duration-200 gpu-accelerated ${settings[item.key] ? 'translate-x-4' : ''}`} style={{ willChange: 'transform' }} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </GlassCard>
              </>
            )}

            {activeTab === 'trading' && (
              <GlassCard className="p-5">
                <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2 mb-4">
                  <DollarSign size={14} className="text-[var(--buy)]" /> Trading • Real Money
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <label className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wide">Account Balance (USDT)</label>
                      <input type="number" value={settings.accountBalance} onChange={e => settings.updateAccountBalance(parseFloat(e.target.value)||0)} className="ui-input mt-1.5 mono font-medium" />
                    </div>
                    <div>
                      <label className="text-[11px] font-medium text-[var(--text-muted)] uppercase tracking-wide">Risk Per Trade</label>
                      <div className="grid grid-cols-4 gap-2 mt-1.5">
                        {[0.01,0.02,0.03,0.05].map(r => (
                          <button key={r} onClick={() => settings.updateRiskPerTrade(r)} className={`py-2.5 rounded-lg text-[12px] font-medium border transition-all duration-200 hover:scale-105 gpu-accelerated ${settings.riskPerTrade===r ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)]'}`}>
                            {r*100}%
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)]">
                    <div className="font-medium text-[12px] text-[var(--text)] flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)]" /> Position Sizing</div>
                    <div className="text-[11px] mt-2 space-y-1 text-[var(--text-muted)] leading-relaxed">
                      <div>Risk = ${settings.accountBalance} × {settings.riskPerTrade*100}% = ${(settings.accountBalance*settings.riskPerTrade).toFixed(0)}</div>
                      <div>Qty = Risk ÷ |Entry - SL|</div>
                      <div className="flex items-center gap-1 mt-2"><span className="px-1.5 py-0.5 rounded-full bg-[var(--buy-soft)] text-[var(--buy)] border border-[var(--buy-border)] text-[10px]">BUY</span> <span className="px-1.5 py-0.5 rounded-full bg-[var(--sell-soft)] text-[var(--sell)] border border-[var(--sell-border)] text-[10px]">SELL</span> themed</div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            )}

            {activeTab === 'interface' && (
              <GlassCard className="p-5">
                <h3 className="font-medium text-[13px] text-[var(--text)] mb-3">Interface</h3>
                <div className="text-[12px] text-[var(--text-sec)] leading-relaxed">
                  Themed design with {Object.keys(THEMES).length} themes. Each theme has its own accent color, buy/sell colors, and glow effects. All animations use transform and opacity only for 120fps GPU acceleration.
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {[
                    { name: '120fps', desc: 'GPU accelerated', color: 'var(--accent)' },
                    { name: 'Themed', desc: 'Colors suit theme', color: 'var(--buy)' },
                    { name: 'Smooth', desc: 'No jank', color: 'var(--sell)' },
                  ].map(item => (
                    <div key={item.name} className="p-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-center">
                      <div className="w-2 h-2 rounded-full mx-auto mb-1.5" style={{ background: item.color }} />
                      <div className="font-medium text-[12px] text-[var(--text)]">{item.name}</div>
                      <div className="text-[10px] text-[var(--text-muted)] mt-1">{item.desc}</div>
                    </div>
                  ))}
                </div>
              </GlassCard>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
