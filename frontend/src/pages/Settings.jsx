import { useState, useEffect } from 'react'
import GlassCard from '../components/GlassCard'
import { useSettingsStore } from '../store/useSettingsStore'
import { api } from '../api/client'
import { Settings as SettingsIcon, DollarSign, Brain, Bell, Palette, Save, RotateCcw, Sliders, Sun, Moon } from 'lucide-react'

export default function SettingsPage() {
  const settings = useSettingsStore()
  const [activeTab, setActiveTab] = useState('display')
  const [saved, setSaved] = useState(false)
  const isDark = settings.theme === 'dark'

  useEffect(() => { api.getSettings().catch(() => null) }, [])

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }

  const tabs = [
    { id: 'display', label: 'Display', icon: Palette, desc: 'Theme & appearance' },
    { id: 'trading', label: 'Trading', icon: DollarSign, desc: 'Risk & position' },
    { id: 'models', label: 'Models', icon: Brain, desc: 'AI configuration' },
    { id: 'notifications', label: 'Alerts', icon: Bell, desc: 'Notifications' },
    { id: 'advanced', label: 'Advanced', icon: Sliders, desc: 'System' },
  ]

  return (
    <div className={`min-h-screen font-poppins ${isDark ? 'bg-black' : 'bg-[#E3EDF7]'}`}>
      <div className="max-w-[1400px] mx-auto p-4 md:p-6 space-y-5">
        <div className="ui-card p-5 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isDark ? 'bg-white text-black' : 'bg-black text-white'}`}><SettingsIcon size={18} /></div>
            <div>
              <h1 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-black'}`}>Settings</h1>
              <p className={`text-[12px] ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Appearance & trading preferences</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => { settings.resetSettings(); handleSave() }} className="ui-card px-4 py-2 text-[12px] font-semibold flex items-center gap-1.5"><RotateCcw size={14} /> Reset</button>
            <button onClick={handleSave} className={`px-4 py-2 rounded-xl text-[12px] font-bold flex items-center gap-1.5 ${isDark ? 'bg-white text-black' : 'bg-black text-white'}`}><Save size={14} /> {saved ? 'Saved!' : 'Save'}</button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-3 space-y-2">
            {tabs.map(tab => {
              const active = activeTab === tab.id
              return (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`w-full text-left p-4 rounded-xl border flex items-center gap-3 transition-colors ${active ? (isDark ? 'bg-white text-black border-white' : 'bg-black text-white border-black') : 'ui-card'}`}>
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${active ? 'bg-black text-white' : isDark ? 'bg-zinc-900 text-zinc-400' : 'bg-zinc-100 text-zinc-500'}`}><tab.icon size={16} /></div>
                  <div><div className="font-semibold text-[13px]">{tab.label}</div><div className={`text-[11px] ${active ? 'opacity-70' : isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>{tab.desc}</div></div>
                </button>
              )
            })}
          </div>

          <div className="lg:col-span-9 space-y-4">
            {activeTab === 'display' && (
              <>
                <GlassCard className="p-6">
                  <h3 className={`font-semibold flex items-center gap-2 mb-6 ${isDark ? 'text-white' : 'text-black'}`}><Palette size={16} /> Theme</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div onClick={() => settings.updateTheme('light')} className={`p-5 rounded-xl border cursor-pointer transition-all ${settings.theme === 'light' ? 'bg-black text-white border-black' : 'ui-card hover:border-black/10'}`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-[#E3EDF7] border flex items-center justify-center"><Sun size={14} className="text-black" /></div><span className="font-semibold text-[13px]">Light</span></div>
                        <div className={`w-10 h-5 rounded-full p-0.5 ${settings.theme === 'light' ? 'bg-white' : 'bg-zinc-300'}`}><div className={`w-4 h-4 rounded-full bg-black transition-all ${settings.theme === 'light' ? 'translate-x-5' : ''}`}></div></div>
                      </div>
                      <div className="text-[11px] opacity-70">Light background • Minimal</div>
                    </div>
                    <div onClick={() => settings.updateTheme('dark')} className={`p-5 rounded-xl border cursor-pointer transition-all ${settings.theme === 'dark' ? 'bg-white text-black border-white' : 'ui-card hover:border-white/10'}`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2"><div className="w-8 h-8 rounded-lg bg-black border border-white/10 flex items-center justify-center"><Moon size={14} className="text-white" /></div><span className="font-semibold text-[13px]">Dark</span></div>
                        <div className={`w-10 h-5 rounded-full p-0.5 ${settings.theme === 'dark' ? 'bg-black' : 'bg-zinc-700'}`}><div className={`w-4 h-4 rounded-full bg-white transition-all ${settings.theme === 'dark' ? 'translate-x-5' : ''}`}></div></div>
                      </div>
                      <div className="text-[11px] opacity-70">Dark background • Minimal</div>
                    </div>
                  </div>
                </GlassCard>

                <GlassCard className="p-6">
                  <h3 className={`font-semibold mb-4 text-[13px] ${isDark ? 'text-white' : 'text-black'}`}>Preferences</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div><label className={`text-[10px] font-bold uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>Default Symbol</label><select value={settings.defaultSymbol} onChange={e => useSettingsStore.setState({ defaultSymbol: e.target.value })} className="ui-input mt-1"><option>BTC-USD</option><option>ETH-USD</option><option>SOL-USD</option><option>BNB-USD</option></select></div>
                    <div><label className={`text-[10px] font-bold uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>Chart Type</label><select value={settings.chartType} onChange={e => useSettingsStore.setState({ chartType: e.target.value })} className="ui-input mt-1"><option value="candlestick">Candlestick</option><option value="line">Line</option><option value="area">Area</option></select></div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 mt-4">
                    {[
                      { key: 'showVolume', label: 'Show Volume' },
                      { key: 'showForecast', label: 'Show Forecast' },
                      { key: 'showAdvanced', label: 'Advanced Mode' },
                      { key: 'autoRefresh', label: 'Auto Refresh' },
                    ].map(item => (
                      <div key={item.key} className={`p-3 rounded-xl border flex items-center justify-between ${isDark ? 'bg-zinc-900 border-white/5' : 'bg-zinc-50 border-black/5'}`}>
                        <span className={`text-[12px] font-medium ${isDark ? 'text-white' : 'text-black'}`}>{item.label}</span>
                        <button onClick={() => useSettingsStore.setState({ [item.key]: !settings[item.key] })} className={`w-9 h-5 rounded-full p-0.5 transition-colors ${settings[item.key] ? 'bg-black dark:bg-white' : 'bg-zinc-300 dark:bg-zinc-700'}`}><div className={`w-4 h-4 rounded-full bg-white dark:bg-black shadow transition-transform ${settings[item.key] ? 'translate-x-4' : ''}`}></div></button>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </>
            )}

            {activeTab === 'trading' && (
              <GlassCard className="p-6">
                <h3 className={`font-semibold flex items-center gap-2 mb-4 ${isDark ? 'text-white' : 'text-black'}`}><DollarSign size={16} /> Risk Management</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div><label className={`text-[10px] font-bold uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>Balance (USDT)</label><input type="number" value={settings.accountBalance} onChange={e => settings.updateAccountBalance(parseFloat(e.target.value)||0)} className="ui-input mt-1 font-bold mono" /></div>
                  <div><label className={`text-[10px] font-bold uppercase ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>Risk Per Trade</label><div className="grid grid-cols-4 gap-2 mt-1">{[0.01,0.02,0.03,0.05].map(r => <button key={r} onClick={() => settings.updateRiskPerTrade(r)} className={`py-2 rounded-xl text-[12px] font-bold border ${settings.riskPerTrade===r ? (isDark ? 'bg-white text-black border-white' : 'bg-black text-white border-black') : 'ui-card'}`}>{r*100}%</button>)}</div></div>
                </div>
              </GlassCard>
            )}

            {activeTab !== 'display' && activeTab !== 'trading' && (
              <GlassCard className="p-6">
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-black'}`}>{activeTab} settings</h3>
                <p className={`text-[12px] mt-2 ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>Configuration for {activeTab} will appear here.</p>
              </GlassCard>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
