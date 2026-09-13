import { useState, useEffect } from 'react'
import GlassCard from '../components/GlassCard'
import { useSettingsStore, THEMES } from '../store/useSettingsStore'
import { api } from '../api/client'
import { Settings as SettingsIcon, DollarSign, Palette, Save, RotateCcw, Eye, Type, Layout, Zap } from 'lucide-react'

export default function SettingsPage() {
  const settings = useSettingsStore()
  const [activeTab, setActiveTab] = useState('appearance')
  const [saved, setSaved] = useState(false)
  const currentTheme = THEMES[settings.theme] || THEMES.dark
  const isLight = settings.theme === 'light' || settings.theme === 'mono'

  useEffect(() => { api.getSettings().catch(() => null) }, [])

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }

  const tabs = [
    { id: 'appearance', label: 'Appearance', icon: Eye, desc: 'Theme & visuals' },
    { id: 'trading', label: 'Trading', icon: DollarSign, desc: 'Risk & balance' },
    { id: 'interface', label: 'Interface', icon: Layout, desc: 'Layout' },
  ]

  const minimalThemes = Object.values(THEMES).slice(0, 4) // Only show minimal ones

  return (
    <div className="min-h-screen theme-bg">
      <div className="max-w-[1200px] mx-auto p-4 md:p-6 space-y-5">
        <div className="rounded-xl border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 gpu-accelerated">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-black flex items-center justify-center">
              <SettingsIcon size={16} />
            </div>
            <div>
              <h1 className="text-[18px] font-semibold tracking-tight text-zinc-900 dark:text-white flex items-center gap-2">
                Settings
                <span className="px-2 py-0.5 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black text-[10px] font-medium">MINIMAL</span>
              </h1>
              <p className="text-[12px] mt-0.5 text-zinc-500">Minimal monochrome • 120fps • No colors</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => { settings.resetSettings(); handleSave() }} className="px-3 py-1.5 rounded-full border border-zinc-200 dark:border-zinc-700 text-[12px] font-medium text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-all duration-200 flex items-center gap-1.5 gpu-accelerated hover:scale-[1.02]">
              <RotateCcw size={12} /> Reset
            </button>
            <button onClick={handleSave} className="px-4 py-1.5 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-black text-[12px] font-medium hover:scale-[1.02] transition-transform duration-200 gpu-accelerated flex items-center gap-1.5">
              <Save size={12} /> {saved ? 'Saved' : 'Save'}
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
                      ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white shadow-sm' 
                      : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 text-zinc-600 dark:text-zinc-400'
                  }`}
                >
                  <tab.icon size={14} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-[13px]">{tab.label}</div>
                    <div className={`text-[11px] ${active ? 'text-white/60 dark:text-black/60' : 'text-zinc-500'}`}>{tab.desc}</div>
                  </div>
                </button>
              )
            })}

            <div className="rounded-xl border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 p-4">
              <div className="text-[10px] font-medium uppercase tracking-wide text-zinc-500 mb-3">Current</div>
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-zinc-500">Theme</span>
                  <span className="font-medium px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 flex items-center gap-1">
                    {currentTheme.icon} {currentTheme.name}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-zinc-500">Balance</span>
                  <span className="font-medium mono text-zinc-900 dark:text-white">${settings.accountBalance}</span>
                </div>
                <div className="flex items-center justify-between text-[12px]">
                  <span className="text-zinc-500">Risk</span>
                  <span className="font-medium px-2 py-0.5 rounded-full bg-zinc-900 text-white dark:bg-white dark:text-black text-[11px]">{settings.riskPerTrade*100}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-9 space-y-4">
            {activeTab === 'appearance' && (
              <>
                <GlassCard className="p-5">
                  <h3 className="font-medium text-[13px] tracking-tight text-zinc-900 dark:text-white flex items-center gap-2 mb-4">
                    <Palette size={14} /> Minimal Themes
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-zinc-500">Monochrome only</span>
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {minimalThemes.map(t => {
                      const active = settings.theme === t.id
                      return (
                        <div
                          key={t.id}
                          onClick={() => settings.updateTheme(t.id)}
                          className={`group p-4 rounded-xl border cursor-pointer transition-all duration-200 gpu-accelerated hover:scale-[1.01] hover:translate-y-[-1px] ${
                            active 
                              ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white shadow-sm' 
                              : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700'
                          }`}
                        >
                          <div className={`w-full h-16 rounded-lg border mb-3 flex items-center justify-center text-[20px] ${active ? 'bg-white/10 dark:bg-black/5 border-white/20 dark:border-black/10' : 'bg-zinc-50 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700'}`}>
                            {t.icon}
                          </div>
                          <div className="font-medium text-[13px]">{t.name}</div>
                          <div className={`text-[11px] mt-1 ${active ? 'text-white/60 dark:text-black/60' : 'text-zinc-500'}`}>{t.desc}</div>
                        </div>
                      )
                    })}
                  </div>
                  <div className="mt-4 p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800">
                    <div className="text-[11px] text-zinc-600 dark:text-zinc-400 leading-relaxed">
                      <strong>Minimal design:</strong> No colors, only black/white/gray. Reduced visual noise for focus. 120fps animations using transform/opacity only, GPU accelerated.
                    </div>
                  </div>
                </GlassCard>

                <GlassCard className="p-5">
                  <h3 className="font-medium text-[13px] tracking-tight text-zinc-900 dark:text-white flex items-center gap-2 mb-4">
                    <Type size={14} /> Typography & Motion
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div>
                        <label className="text-[11px] font-medium text-zinc-500 uppercase tracking-wide">Font</label>
                        <div className="grid grid-cols-2 gap-2 mt-2">
                          {[
                            { id: 'poppins', name: 'Geist' },
                            { id: 'inter', name: 'Inter' },
                          ].map(f => (
                            <button key={f.id} onClick={() => settings.updateFont(f.id)} className={`p-2.5 rounded-lg border text-left transition-all duration-200 hover:scale-[1.02] gpu-accelerated ${settings.font === f.id ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300'}`}>
                              <div className="font-medium text-[12px]">{f.name}</div>
                              <div className="text-[10px] text-zinc-500">Minimal</div>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2.5">
                      {[
                        { key: 'animations', label: '120fps Animations', desc: 'GPU accelerated', icon: Zap },
                        { key: 'blur', label: 'Subtle Blur', desc: 'Minimal glass', icon: Eye },
                        { key: 'showMarketTicker', label: 'Ticker', desc: 'Market scroll', icon: Layout },
                      ].map(item => (
                        <div key={item.key} className="p-3 rounded-lg border bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-lg bg-zinc-900 dark:bg-white text-white dark:text-black flex items-center justify-center">
                              <item.icon size={12} />
                            </div>
                            <div>
                              <div className="text-[12px] font-medium text-zinc-900 dark:text-white">{item.label}</div>
                              <div className="text-[11px] text-zinc-500">{item.desc}</div>
                            </div>
                          </div>
                          <button onClick={() => useSettingsStore.setState({ [item.key]: !settings[item.key] })} className={`w-9 h-5 rounded-full p-0.5 transition-all duration-200 gpu-accelerated ${settings[item.key] ? 'bg-zinc-900 dark:bg-white' : 'bg-zinc-200 dark:bg-zinc-700'}`}>
                            <div className={`w-4 h-4 rounded-full bg-white dark:bg-black shadow-sm transition-transform duration-200 gpu-accelerated ${settings[item.key] ? 'translate-x-4' : ''}`} style={{ willChange: 'transform' }} />
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
                <h3 className="font-medium text-[13px] tracking-tight text-zinc-900 dark:text-white flex items-center gap-2 mb-4">
                  <DollarSign size={14} /> Trading
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <label className="text-[11px] font-medium text-zinc-500 uppercase tracking-wide">Balance</label>
                      <input type="number" value={settings.accountBalance} onChange={e => settings.updateAccountBalance(parseFloat(e.target.value)||0)} className="ui-input mt-1.5 mono font-medium" />
                    </div>
                    <div>
                      <label className="text-[11px] font-medium text-zinc-500 uppercase tracking-wide">Risk</label>
                      <div className="grid grid-cols-4 gap-2 mt-1.5">
                        {[0.01,0.02,0.03,0.05].map(r => (
                          <button key={r} onClick={() => settings.updateRiskPerTrade(r)} className={`py-2.5 rounded-lg text-[12px] font-medium border transition-all duration-200 hover:scale-105 gpu-accelerated ${settings.riskPerTrade===r ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white' : 'bg-white dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300'}`}>
                            {r*100}%
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800">
                    <div className="font-medium text-[12px] text-zinc-900 dark:text-white">Position Sizing</div>
                    <div className="text-[11px] mt-2 space-y-1 text-zinc-500 leading-relaxed">
                      <div>Risk = ${settings.accountBalance} × {settings.riskPerTrade*100}% = ${(settings.accountBalance*settings.riskPerTrade).toFixed(0)}</div>
                      <div>Qty = Risk ÷ |Entry - SL|</div>
                      <div>Minimal UI • No colors • 120fps</div>
                    </div>
                  </div>
                </div>
              </GlassCard>
            )}

            {activeTab === 'interface' && (
              <GlassCard className="p-5">
                <h3 className="font-medium text-[13px] text-zinc-900 dark:text-white mb-3">Interface</h3>
                <div className="text-[12px] text-zinc-500 leading-relaxed">
                  Minimal monochrome design. Only black, white, and zinc grays. No bright colors. All animations use transform and opacity only for 120fps GPU acceleration. Reduced motion support.
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {[
                    { name: '120fps', desc: 'GPU accelerated' },
                    { name: 'Minimal', desc: 'No colors' },
                    { name: 'Focus', desc: 'Content first' },
                  ].map(item => (
                    <div key={item.name} className="p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-center">
                      <div className="font-medium text-[12px] text-zinc-900 dark:text-white">{item.name}</div>
                      <div className="text-[10px] text-zinc-500 mt-1">{item.desc}</div>
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
