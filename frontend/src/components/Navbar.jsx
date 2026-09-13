import { Link, useLocation } from 'react-router-dom'
import { TrendingUp, Brain, Radio, BarChart3, Home, Sparkles } from 'lucide-react'

export default function Navbar() {
  const loc = useLocation()
  const nav = [
    { path: '/', label: 'Dashboard', icon: Home },
    { path: '/forecast', label: 'Forecast', icon: TrendingUp },
    { path: '/sentiment', label: 'Sentiment', icon: Sparkles },
    { path: '/realtime', label: 'Realtime', icon: Radio },
    { path: '/backtest', label: 'Backtest', icon: BarChart3 },
    { path: '/models', label: 'Models', icon: Brain },
  ]

  return (
    <nav className="border-b border-crypto-border bg-crypto-card/50 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-crypto-accent rounded-lg flex items-center justify-center font-bold text-black">₿</div>
          <span className="font-bold text-lg">CryptoPred <span className="text-crypto-accent">v2</span></span>
        </Link>
        <div className="flex gap-1">
          {nav.map(item => {
            const active = loc.pathname === item.path
            return (
              <Link key={item.path} to={item.path} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${active ? 'bg-crypto-accent text-black' : 'text-gray-400 hover:text-white hover:bg-crypto-border'}`}>
                <item.icon size={16} />
                {item.label}
              </Link>
            )
          })}
        </div>
        <div className="text-xs text-gray-500 mono">LSTM • Transformer • XGB • ARIMA • Sentiment</div>
      </div>
    </nav>
  )
}
