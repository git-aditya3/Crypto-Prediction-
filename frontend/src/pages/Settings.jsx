import { useState, useEffect } from 'react'
import GlassCard from '../components/GlassCard'
import { useSettingsStore, THEMES, THEME_CATEGORIES, VISUAL_STYLES } from '../store/useSettingsStore'
import { api } from '../api/client'
import { Settings as SettingsIcon, DollarSign, Palette, Save, RotateCcw, Eye, Layout, Zap, Paintbrush, Droplets, Sparkles, Layers, Box } from 'lucide-react'

export default function SettingsPage() {
  const settings = useSettingsStore()
  const [activeTab, setActiveTab] = useState('visual')
  const [saved, setSaved] = useState(false)
  const [themeCategory, setThemeCategory] = useState('All')
  const currentTheme = THEMES[settings.theme] || THEMES.dark
  const currentVisual = VISUAL_STYLES[settings.visualStyle] || VISUAL_STYLES.liquid

  useEffect(() => { api.getSettings().catch(() => null) }, [])

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }

  const tabs = [
    { id: 'visual', label: 'iOS 26 Materials', icon: Sparkles, desc: 'Liquid Glass materials' },
    { id: 'themes', label: 'iOS 26 Themes', icon: Palette, desc: `${Object.keys(THEMES).length} liquid glass` },
    { id: 'appearance', label: 'Appearance', icon: Eye, desc: 'Motion & effects' },
    { id: 'trading', label: 'Trading', icon: DollarSign, desc: 'Risk & balance' },
  ]

  const filteredThemes = themeCategory === 'All' ? Object.values(THEMES) : Object.values(THEMES).filter(t => t.category === themeCategory)

  return (
    <div className="min-h-screen theme-bg">
      <div className="max-w-[1400px] mx-auto p-4 md:p-6 space-y-5">
        <div className="liquid-glass-card p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 gpu-accelerated relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent-soft)] to-transparent pointer-events-none opacity-60" />
          <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--accent)]/08 rounded-full blur-[60px] -translate-y-32 translate-x-32 pointer-events-none" />
          <div className="flex items-center gap-3 relative z-10">
            <div className="w-10 h-10 rounded-xl bg-[var(--accent)] text-white flex items-center justify-center shadow-[var(--glow)]" style={{ borderRadius: '12px' }}>
              <SettingsIcon size={18} />
            </div>
            <div>
              <h1 className="text-[20px] font-semibold tracking-tight text-[var(--text)] flex items-center gap-2" style={{ letterSpacing: '-0.45px', fontFamily: "-apple-system, 'SF Pro Display', sans-serif" }}>
                iOS 26 Settings
                <span className="px-2.5 py-1 rounded-full bg-[var(--accent)] text-white text-[10px] font-bold shadow-[var(--glow)]">iOS 26 • {Object.keys(THEMES).length} LIQUID GLASS</span>
                <span className="px-2.5 py-1 rounded-full bg-[var(--glass-bg)] backdrop-blur-xl border border-[var(--glass-border)] text-[var(--text-sec)] text-[10px] font-bold">{Object.keys(VISUAL_STYLES).length} MATERIALS</span>
                <span className="hidden md:inline-flex text-[10px] px-2.5 py-1 rounded-full border font-medium bg-[var(--glass-bg)] backdrop-blur-xl" style={{ border: '0.5px solid var(--glass-border)' }}>{currentTheme.icon} {currentTheme.name}</span>
              </h1>
              <p className="text-[12px] mt-0.5 text-[var(--text-sec)]" style={{ letterSpacing: '-0.08px' }}>{currentTheme.desc} • {currentVisual.ios} • {currentVisual.vibe} • blur 40px saturate 180% • SF Pro</p>
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
                  <span className="text-[var(--text-muted)]">Style</span>
                  <span className="font-medium px-2 py-0.5 rounded-full bg-[var(--accent)] text-white text-[11px] shadow-sm">{currentVisual.icon} {currentVisual.name}</span>
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[var(--text-muted)]">Balance</span>
                  <span className="font-medium mono text-[var(--text)]">${settings.accountBalance}</span>
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-[var(--text-muted)]">Risk</span>
                  <span className="font-medium px-2 py-0.5 rounded-full bg-[var(--buy)] text-white text-[11px] shadow-sm">{settings.riskPerTrade*100}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-9 space-y-4">
            {activeTab === 'visual' && (
              <>
                <GlassCard className="p-5">
                  <h3 className="font-medium text-[14px] text-[var(--text)] flex items-center gap-2 mb-1">
                    <Sparkles size={16} className="text-[var(--accent)]" /> Visual Styles Guide
                    <span className="px-2 py-0.5 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] text-[10px] text-[var(--accent)]">Clay, Glass & Beyond</span>
                  </h3>
                  <p className="text-[12px] text-[var(--text-muted)] mb-4">Choose a design language. Each has distinct triggers, contrast, and vibe. Colors adapt to your selected theme.</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 stagger-children">
                    {Object.values(VISUAL_STYLES).map(v => {
                      const active = settings.visualStyle === v.id
                      return (
                        <div
                          key={v.id}
                          onClick={() => settings.updateVisualStyle(v.id)}
                          className={`group p-4 rounded-xl border cursor-pointer transition-all duration-200 hover:scale-[1.02] gpu-accelerated relative overflow-hidden ${
                            active 
                              ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)] ring-2 ring-[var(--accent-ring)]' 
                              : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)]'
                          }`}
                        >
                          <div className={`w-full h-20 rounded-xl border mb-3 flex items-center justify-center relative overflow-hidden ${
                            active ? 'bg-white/10 border-white/20' : 
                            v.id === 'clay' ? 'clay-card !h-20 !p-0' :
                            v.id === 'liquid' ? 'liquid-glass-card !h-20 !p-0' :
                            v.id === 'brutal' ? 'brutal-card !h-20 !p-0 !rounded-lg' :
                            v.id === 'neo' ? 'neo-card !h-20 !p-0 !rounded-xl' :
                            'flat-card !h-20 !p-0'
                          }`}>
                            <span className="text-[28px] group-hover:scale-125 transition-transform duration-300">{v.icon}</span>
                            {v.id === 'liquid' && <div className="glass-blob w-16 h-16 bg-[var(--accent-soft)] top-0 right-4" />}
                            {v.id === 'clay' && <div className="absolute bottom-1 left-1 right-1 h-1 rounded-full bg-[var(--accent)]/20" />}
                          </div>
                          <div className="font-semibold text-[13px] flex items-center gap-2">
                            {v.name}
                            {active && <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
                            <span className={`ml-auto px-1.5 py-0.5 rounded-full text-[8px] font-bold uppercase ${active ? 'bg-white/20 text-white' : 'bg-[var(--bg-secondary)] text-[var(--text-muted)] border border-[var(--border)]'}`}>{v.vibe.split(',')[0]}</span>
                          </div>
                          <div className={`text-[11px] mt-1 ${active ? 'text-white/70' : 'text-[var(--text-muted)]'}`}>{v.desc} • {v.bestFor}</div>
                        </div>
                      )
                    })}
                  </div>

                  <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="clay-card p-4 !rounded-2xl">
                      <div className="font-semibold text-[12px] text-[var(--text)] flex items-center gap-1.5"><Box size={12} /> Claymorphism</div>
                      <div className="text-[11px] text-[var(--text-muted)] mt-1 leading-relaxed">Inner shadows + outer soft shadow + 24-40px radius. Playful, friendly, 3D. Best for crypto wallets & onboarding.</div>
                      <div className="mt-2 flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-[var(--accent)]" />
                        <div className="w-2 h-2 rounded-full bg-[var(--buy)]" />
                        <div className="w-2 h-2 rounded-full bg-[var(--sell)]" />
                      </div>
                    </div>
                    <div className="liquid-glass-card p-4">
                      <div className="font-semibold text-[12px] text-[var(--text)] flex items-center gap-1.5"><Droplets size={12} className="text-[var(--accent)]" /> Liquid Glass</div>
                      <div className="text-[11px] text-[var(--text-muted)] mt-1 leading-relaxed">backdrop-filter: blur(20px) + vibrant blobs + specular border. Premium, sleek, high-tech. Best for OS-level & trading.</div>
                      <div className="mt-2 h-1 rounded-full bg-gradient-to-r from-[var(--accent)] via-[var(--buy)] to-[var(--sell)] opacity-60" />
                    </div>
                    <div className="brutal-card p-4 !rounded-lg">
                      <div className="font-bold text-[12px] text-[var(--text)] uppercase">Brutalism</div>
                      <div className="text-[11px] text-[var(--text-muted)] mt-1 leading-relaxed">Thick #000 borders + hard 100% shadows + neon. Edgy, memorable. Popular in Figma, Gumroad.</div>
                      <div className="mt-2 px-2 py-1 brutal-pill !text-[8px] w-fit">EDGY • RAW</div>
                    </div>
                  </div>
                </GlassCard>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <GlassCard className="p-5">
                    <h4 className="font-medium text-[13px] text-[var(--text)] mb-3 flex items-center gap-2"><Layers size={14} className="text-[var(--accent)]" /> Current Style: {currentVisual.name}</h4>
                    <div className="space-y-2.5 text-[12px]">
                      <div className="flex justify-between"><span className="text-[var(--text-muted)]">Vibe</span><span className="font-medium text-[var(--text)]">{currentVisual.vibe}</span></div>
                      <div className="flex justify-between"><span className="text-[var(--text-muted)]">Best For</span><span className="font-medium text-[var(--text)]">{currentVisual.bestFor}</span></div>
                      <div className="flex justify-between"><span className="text-[var(--text-muted)]">Contrast</span><span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${currentVisual.id === 'neo' ? 'bg-amber-500/15 text-amber-600 border border-amber-500/20' : currentVisual.id === 'brutal' ? 'bg-[var(--accent)] text-white' : 'bg-[var(--buy-soft)] text-[var(--buy)] border border-[var(--buy-border)]'}`}>{currentVisual.id === 'neo' ? 'Low' : currentVisual.id === 'brutal' ? 'Very High' : 'Medium-High'}</span></div>
                    </div>
                  </GlassCard>
                  <GlassCard className="p-5">
                    <h4 className="font-medium text-[13px] text-[var(--text)] mb-3">Theme + Style Combo</h4>
                    <div className="text-[12px] text-[var(--text-sec)] leading-relaxed">
                      <span className="font-medium text-[var(--text)]">{currentTheme.name} + {currentVisual.name}</span> = {currentTheme.desc} meets {currentVisual.desc.toLowerCase()}. Colors adapt: accent {currentTheme.colors.accent}, buy {currentTheme.id === 'cyberpunk' ? '#00ff9f' : 'emerald'}, sell {currentTheme.id === 'cyberpunk' ? 'hot pink' : 'red'}.
                    </div>
                    <div className="mt-3 flex gap-1.5">
                      <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm" style={{ background: currentTheme.colors.accent }} />
                      <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm" style={{ background: currentTheme.colors.bg }} />
                      <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm bg-[var(--buy)]" />
                      <div className="w-6 h-6 rounded-full border-2 border-white shadow-sm bg-[var(--sell)]" />
                    </div>
                  </GlassCard>
                </div>
              </>
            )}

            {activeTab === 'themes' && (
              <>
                <GlassCard className="p-4">
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2">
                      <Paintbrush size={14} className="text-[var(--accent)]" /> Theme Gallery • {Object.keys(THEMES).length} themes
                      <span className="px-2 py-0.5 rounded-full bg-[var(--accent-soft)] border border-[var(--border)] text-[10px] text-[var(--accent)]">Colors suit theme + {currentVisual.name}</span>
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
                        } ${settings.visualStyle === 'clay' ? '!rounded-2xl' : settings.visualStyle === 'brutal' ? '!rounded-sm !border-[3px]' : ''}`}
                      >
                        <div className={`w-full h-20 rounded-lg border mb-3 relative overflow-hidden flex items-center justify-center text-[22px] transition-transform duration-200 group-hover:scale-[1.02] ${active ? 'bg-white/10 border-white/20' : t.preview} ${settings.visualStyle === 'clay' ? '!rounded-2xl' : ''}`}>
                          <span className="relative z-10 group-hover:scale-125 transition-transform duration-300">{t.icon}</span>
                          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
                          <div className="absolute top-2 left-2 w-1.5 h-1.5 rounded-full bg-[var(--buy)] animate-pulse shadow-[0_0_8px_var(--buy)]" />
                          <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded-full bg-black/20 text-white text-[8px] font-bold">{t.category}</div>
                          {settings.visualStyle === 'liquid' && <div className="glass-blob w-12 h-12 bg-white/20 top-1 right-6" />}
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
              </>
            )}

            {activeTab === 'appearance' && (
              <GlassCard className="p-5">
                <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2 mb-4">
                  <Eye size={14} className="text-[var(--accent)]" /> Motion & Effects • {currentVisual.name}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2.5">
                    {[
                      { key: 'animations', label: '120fps Animations', desc: 'GPU accelerated transform+opacity', icon: Zap },
                      { key: 'blur', label: 'Glass Blur', desc: 'backdrop-filter: blur(20px)', icon: Droplets },
                      { key: 'showMarketTicker', label: 'Market Ticker', desc: '90s linear ticker with mask', icon: Layout },
                    ].map(item => (
                      <div key={item.key} className="p-3 rounded-xl border bg-[var(--card)] border-[var(--border)] flex items-center justify-between hover:border-[var(--border-strong)] transition-colors">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-[var(--accent)] text-white flex items-center justify-center shadow-[var(--glow)]">
                            <item.icon size={14} />
                          </div>
                          <div>
                            <div className="text-[12px] font-medium text-[var(--text)]">{item.label}</div>
                            <div className="text-[11px] text-[var(--text-muted)]">{item.desc}</div>
                          </div>
                        </div>
                        <button onClick={() => useSettingsStore.setState({ [item.key]: !settings[item.key] })} className={`w-10 h-6 rounded-full p-0.5 transition-all duration-200 gpu-accelerated ${settings[item.key] ? 'bg-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--bg-tertiary)]'}`}>
                          <div className={`w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200 gpu-accelerated ${settings[item.key] ? 'translate-x-4' : ''}`} style={{ willChange: 'transform' }} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-3">
                    <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                      <div className="font-medium text-[12px] text-[var(--text)]">Visual Style CSS</div>
                      <div className="text-[11px] mt-2 font-mono text-[var(--text-muted)] leading-relaxed bg-[var(--bg-tertiary)] p-2 rounded-lg border border-[var(--border)]">
                        {settings.visualStyle === 'clay' && `.clay-card { box-shadow: 0 20px 40px rgba(0,0,0,0.07), inset -8px -8px 16px rgba(0,0,0,0.1), inset 8px 8px 16px rgba(255,255,255,0.8); border-radius: 32px; }`}
                        {settings.visualStyle === 'liquid' && `.liquid-glass { background: rgba(255,255,255,0.15); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.25); box-shadow: 0 8px 32px rgba(31,38,135,0.15); }`}
                        {settings.visualStyle === 'brutal' && `.brutal-card { border: 3px solid #000; box-shadow: 6px 6px 0px #000; border-radius: 8px; }`}
                        {settings.visualStyle === 'neo' && `.neo-card { background: var(--bg); box-shadow: 8px 8px 16px rgba(0,0,0,0.15), -8px -8px 16px rgba(255,255,255,0.05); }`}
                        {settings.visualStyle === 'flat' && `.flat-card { border: 1px solid var(--border); box-shadow: var(--shadow-sm); border-radius: 12px; }`}
                      </div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            )}

            {activeTab === 'trading' && (
              <GlassCard className="p-5">
                <h3 className="font-medium text-[13px] text-[var(--text)] flex items-center gap-2 mb-4">
                  <DollarSign size={14} className="text-[var(--buy)]" /> Trading • Real Money • {currentVisual.name}
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
                          <button key={r} onClick={() => settings.updateRiskPerTrade(r)} className={`py-2.5 rounded-xl text-[12px] font-bold border transition-all duration-200 hover:scale-105 gpu-accelerated ${settings.riskPerTrade===r ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-[var(--glow)]' : 'bg-[var(--card)] border-[var(--border)] hover:border-[var(--border-strong)]'} ${settings.visualStyle === 'clay' ? '!rounded-full' : settings.visualStyle === 'brutal' ? '!rounded-sm !border-[3px]' : ''}`}>
                            {r*100}%
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className={`p-4 rounded-xl border bg-[var(--bg-secondary)] border-[var(--border)] ${settings.visualStyle === 'clay' ? 'clay-card !rounded-2xl' : settings.visualStyle === 'liquid' ? 'liquid-glass-card' : ''}`}>
                    <div className="font-medium text-[12px] text-[var(--text)] flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] shadow-[var(--glow)]" /> Position Sizing • {currentVisual.name}</div>
                    <div className="text-[11px] mt-2 space-y-1 text-[var(--text-muted)] leading-relaxed">
                      <div>Risk = ${settings.accountBalance} × {settings.riskPerTrade*100}% = ${(settings.accountBalance*settings.riskPerTrade).toFixed(0)}</div>
                      <div>Qty = Risk ÷ |Entry - SL|</div>
                      <div className="flex items-center gap-1.5 mt-2">
                        <span className={`px-2 py-1 rounded-full text-[10px] font-bold border ${settings.visualStyle === 'clay' ? 'clay-pill !px-2.5' : settings.visualStyle === 'brutal' ? 'brutal-pill !text-[9px]' : 'bg-[var(--buy)] text-white border-[var(--buy)] shadow-sm'}`}>BUY</span>
                        <span className={`px-2 py-1 rounded-full text-[10px] font-bold border ${settings.visualStyle === 'clay' ? 'clay-pill' : settings.visualStyle === 'brutal' ? 'brutal-pill !bg-[var(--sell)]' : 'bg-[var(--sell-soft)] text-[var(--sell)] border-[var(--sell-border)]'}`}>SELL</span>
                        <span className="text-[10px] text-[var(--text-muted)]">themed • {currentVisual.vibe}</span>
                      </div>
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
