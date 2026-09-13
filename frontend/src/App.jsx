import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from './components/Navbar'
import MarketTicker from './components/MarketTicker'
import Dashboard from './pages/Dashboard'
import Forecast from './pages/Forecast'
import Sentiment from './pages/Sentiment'
import Realtime from './pages/Realtime'
import Backtest from './pages/Backtest'
import Models from './pages/Models'
import TradingCalls from './pages/TradingCalls'
import Settings from './pages/Settings'
import Training from './pages/Training'
import Portfolio from './pages/Portfolio'
import Strategies from './pages/Strategies'
import Scanner from './pages/Scanner'
import Analytics from './pages/Analytics'
import Alerts from './pages/Alerts'
import Journal from './pages/Journal'
import AutoTrading from './pages/AutoTrading'
import CrashDetector from './pages/CrashDetector'
import { useSettingsStore, THEMES } from './store/useSettingsStore'

export default function App() {
  const { theme, accent, font, density, animations, blur, showMarketTicker } = useSettingsStore()

  useEffect(() => {
    const html = document.documentElement
    // Remove all theme classes
    Object.keys(THEMES).forEach(t => html.classList.remove(t))
    html.classList.remove('light', 'dark')
    const themeId = THEMES[theme] ? theme : 'dark'
    html.classList.add(themeId)
    const isLight = ['light', 'sakura', 'mono'].includes(themeId)
    html.classList.add(isLight ? 'light' : 'dark')
    html.setAttribute('data-theme', themeId)
    html.setAttribute('data-accent', accent || 'emerald')
    html.setAttribute('data-font', font || 'poppins')
    html.setAttribute('data-density', density || 'comfortable')
    html.setAttribute('data-animations', animations ? 'true' : 'false')
    html.setAttribute('data-blur', blur ? 'true' : 'false')
    
    // Apply font
    const fontMap = {
      poppins: "'Poppins', sans-serif",
      inter: "'Inter', sans-serif",
      space: "'Space Grotesk', sans-serif",
      outfit: "'Outfit', sans-serif"
    }
    document.body.style.fontFamily = fontMap[font] || fontMap.poppins
  }, [theme, accent, font, density, animations, blur])

  const isLight = ['light', 'sakura', 'mono'].includes(theme)
  const currentTheme = THEMES[theme] || THEMES.dark

  return (
    <BrowserRouter>
      <div className={`min-h-screen font-poppins selection:bg-[var(--accent)] selection:text-[var(--bg)] theme-bg ${isLight ? '' : ''}`} style={{ fontFamily: `var(--font, 'Poppins')` }}>
        {showMarketTicker && <MarketTicker />}
        <Navbar />
        <main className="min-h-[calc(100vh-200px)] relative">
          {/* Subtle background pattern */}
          <div className="absolute inset-0 pointer-events-none opacity-[0.02]">
            <div className="absolute inset-0" style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, var(--text) 1px, transparent 0)`,
              backgroundSize: '40px 40px'
            }} />
          </div>
          <div className="relative z-10">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/trading" element={<TradingCalls />} />
              <Route path="/crash" element={<CrashDetector />} />
              <Route path="/autotrade" element={<AutoTrading />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/strategies" element={<Strategies />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/journal" element={<Journal />} />
              <Route path="/training" element={<Training />} />
              <Route path="/forecast" element={<Forecast />} />
              <Route path="/sentiment" element={<Sentiment />} />
              <Route path="/realtime" element={<Realtime />} />
              <Route path="/backtest" element={<Backtest />} />
              <Route path="/models" element={<Models />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </div>
        </main>
        
        {/* Enhanced Footer */}
        <footer className={`mt-16 border-t backdrop-blur-xl relative overflow-hidden ${isLight ? 'bg-white/80 border-black/5' : 'bg-[var(--card)]/80 border-[var(--border)]'} glass`}>
          <div className="absolute inset-0 bg-gradient-to-r from-[var(--accent)]/5 via-transparent to-[var(--accent)]/5 pointer-events-none" />
          <div className="max-w-[1600px] mx-auto px-6 py-8 relative z-10">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-black text-[14px] shadow-lg ${isLight ? 'bg-black text-white' : 'bg-white text-black'}`}>₿</div>
                  <span className={`font-black text-[16px] ${isLight ? 'text-black' : 'text-white'}`}>CryptoPred</span>
                  <span className="ui-pill-accent text-[9px] font-black px-2 py-1">V7</span>
                </div>
                <p className={`text-[12px] leading-relaxed ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>Real trading intelligence • CoinDCX real money • {Object.keys(THEMES).length} themes • Endless learning</p>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] px-2 py-1 rounded-full border font-bold ${currentTheme.preview}`}>{currentTheme.icon} {currentTheme.name}</span>
                  <span className="ui-pill text-[10px]">{currentTheme.category}</span>
                </div>
              </div>
              
              <div>
                <div className={`font-bold text-[12px] uppercase tracking-wide mb-3 ${isLight ? 'text-black' : 'text-white'}`}>Trading</div>
                <div className={`space-y-2 text-[12px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>
                  <div>• Live Binance + CoinDCX</div>
                  <div>• Real entry/SL/TP</div>
                  <div>• No simulation</div>
                  <div>• Auto trading bots</div>
                </div>
              </div>
              
              <div>
                <div className={`font-bold text-[12px] uppercase tracking-wide mb-3 ${isLight ? 'text-black' : 'text-white'}`}>AI Models</div>
                <div className={`space-y-2 text-[12px] ${isLight ? 'text-zinc-600' : 'text-zinc-400'}`}>
                  <div className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-violet-500" /> LSTM v3 + Attention</div>
                  <div className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-cyan-500" /> Transformer Learnable PE</div>
                  <div className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-emerald-500" /> XGBoost 1500 trees</div>
                  <div className="flex items-center gap-2"><span className="w-1 h-1 rounded-full bg-orange-500" /> ARIMA 2.57% MAPE</div>
                </div>
              </div>
              
              <div>
                <div className={`font-bold text-[12px] uppercase tracking-wide mb-3 ${isLight ? 'text-black' : 'text-white'}`}>Themes</div>
                <div className="grid grid-cols-4 gap-1.5">
                  {Object.values(THEMES).slice(0, 8).map(t => (
                    <div key={t.id} className={`w-8 h-8 rounded-lg border flex items-center justify-center text-[14px] hover:scale-110 transition-transform cursor-pointer ${t.preview}`} title={`${t.name} - ${t.desc}`}>
                      {t.icon}
                    </div>
                  ))}
                </div>
                <div className={`text-[10px] mt-2 ${isLight ? 'text-zinc-500' : 'text-zinc-500'}`}>{Object.keys(THEMES).length} themes • Minimal to Cyberpunk</div>
              </div>
            </div>
            
            <div className={`pt-6 border-t flex flex-col md:flex-row items-center justify-between gap-3 text-[11px] ${isLight ? 'border-black/5 text-zinc-500' : 'border-white/5 text-zinc-500'}`}>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="flex items-center gap-2">
                  <span className="live-dot"></span> LIVE • REAL DATA • NO SIMULATION
                </span>
                <span className="hidden md:inline w-1 h-1 rounded-full bg-[var(--border)]" />
                <span className="hidden md:inline">182 features • RobustScaler • Dynamic ensemble</span>
              </div>
              <div className="flex items-center gap-2">
                <span>Built for real traders • CoinDCX INR • Endless learning</span>
                <span className="ui-pill-accent text-[9px]">V7 • {new Date().getFullYear()}</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}
