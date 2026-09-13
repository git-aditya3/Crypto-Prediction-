import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const THEMES = {
  light: {
    id: 'light',
    name: 'Light',
    desc: 'iOS 26 Liquid Glass Light',
    category: 'iOS 26',
    colors: { bg: '#FBFBFD', card: 'rgba(255,255,255,0.72)', accent: '#007AFF', text: '#000000' },
    preview: 'bg-[#FBFBFD] text-black border-black/10',
    icon: '☀️',
    ios: { material: 'thin', accent: 'systemBlue #007AFF', background: 'systemGroupedBackground #F2F2F7', blur: '40px saturate 180%' }
  },
  dark: {
    id: 'dark',
    name: 'Dark',
    desc: 'iOS 26 Liquid Glass Dark',
    category: 'iOS 26',
    colors: { bg: '#000000', card: 'rgba(28,28,30,0.72)', accent: '#0A84FF', text: '#FFFFFF' },
    preview: 'bg-black text-white border-white/10',
    icon: '🌙',
    ios: { material: 'thin dark', accent: 'systemBlue dark #0A84FF', background: '#000000', blur: '40px saturate 180%' }
  },
  midnight: {
    id: 'midnight',
    name: 'Midnight',
    desc: 'iOS 26 Indigo Liquid Glass',
    category: 'iOS 26 Dark',
    colors: { bg: '#0A0A12', card: 'rgba(21,21,37,0.75)', accent: '#5E5CE6', text: '#E9E9FF' },
    preview: 'bg-[#0A0A12] text-violet-300 border-violet-500/20',
    icon: '🌌',
    ios: { material: 'indigo tint', accent: 'systemIndigo #5856D6 / #5E5CE6 dark', blur: '40px saturate 180%' }
  },
  ocean: {
    id: 'ocean',
    name: 'Ocean',
    desc: 'iOS 26 Teal Liquid Glass',
    category: 'iOS 26 Dark',
    colors: { bg: '#050A14', card: 'rgba(14,30,46,0.75)', accent: '#64D2FF', text: '#C7F0FF' },
    preview: 'bg-[#050A14] text-cyan-300 border-cyan-500/20',
    icon: '🌊',
    ios: { material: 'teal tint', accent: 'systemTeal #5AC8FA / #64D2FF dark', blur: '40px saturate 180%' }
  },
  forest: {
    id: 'forest',
    name: 'Forest',
    desc: 'iOS 26 Green Liquid Glass',
    category: 'iOS 26 Dark',
    colors: { bg: '#040A06', card: 'rgba(15,34,20,0.75)', accent: '#30D158', text: '#D1FAE5' },
    preview: 'bg-[#040A06] text-emerald-300 border-emerald-500/20',
    icon: '🌲',
    ios: { material: 'green tint', accent: 'systemGreen #34C759 / #30D158 dark', blur: '40px saturate 180%' }
  },
  sunset: {
    id: 'sunset',
    name: 'Sunset',
    desc: 'iOS 26 Orange Liquid Glass',
    category: 'iOS 26 Dark',
    colors: { bg: '#0F0600', card: 'rgba(42,21,21,0.75)', accent: '#FF9F0A', text: '#FFEAD0' },
    preview: 'bg-[#0F0600] text-orange-300 border-orange-500/20',
    icon: '🌅',
    ios: { material: 'orange tint', accent: 'systemOrange #FF9500 / #FF9F0A dark', blur: '40px saturate 180%' }
  },
  neon: {
    id: 'neon',
    name: 'Neon',
    desc: 'iOS 26 Pink Liquid Glass',
    category: 'iOS 26 Dark',
    colors: { bg: '#0A0014', card: 'rgba(26,10,46,0.75)', accent: '#FF375F', text: '#FFE0EB' },
    preview: 'bg-[#0A0014] text-pink-300 border-pink-500/20',
    icon: '💜',
    ios: { material: 'pink tint', accent: 'systemPink #FF2D55 / #FF375F dark', blur: '40px saturate 180%' }
  },
  nord: {
    id: 'nord',
    name: 'Nord',
    desc: 'iOS 26 Frost Liquid Glass',
    category: 'iOS 26',
    colors: { bg: '#242933', card: 'rgba(46,52,64,0.75)', accent: '#88C0D0', text: '#ECEFF4' },
    preview: 'bg-[#242933] text-slate-200 border-slate-500/20',
    icon: '❄️',
    ios: { material: 'frost', accent: '#88C0D0', blur: '40px saturate 150%' }
  },
  dracula: {
    id: 'dracula',
    name: 'Dracula',
    desc: 'iOS 26 Purple Liquid Glass',
    category: 'iOS 26 Dark',
    colors: { bg: '#1E1F2E', card: 'rgba(40,42,54,0.75)', accent: '#BF5AF2', text: '#F8F8F2' },
    preview: 'bg-[#1E1F2E] text-purple-200 border-purple-500/20',
    icon: '🧛',
    ios: { material: 'purple tint', accent: 'systemPurple #AF52DE / #BF5AF2 dark', blur: '40px saturate 180%' }
  },
  cyberpunk: {
    id: 'cyberpunk',
    name: 'Cyberpunk',
    desc: 'iOS 26 Neon Liquid Glass',
    category: 'iOS 26 Dark',
    colors: { bg: '#050510', card: 'rgba(15,15,30,0.78)', accent: '#30D158', text: '#E0FFE0' },
    preview: 'bg-[#050510] text-green-300 border-green-400/20',
    icon: '🤖',
    ios: { material: 'neon green tint prominent', accent: '#30D158', glow: '0 0 36px rgba(48,209,88,0.4)', blur: '40px saturate 180%' }
  },
  sakura: {
    id: 'sakura',
    name: 'Sakura',
    desc: 'iOS 26 Pink Light Liquid Glass',
    category: 'iOS 26 Light',
    colors: { bg: '#FFF0F5', card: 'rgba(255,255,255,0.75)', accent: '#FF2D55', text: '#4A0A1F' },
    preview: 'bg-[#FFF0F5] text-pink-800 border-pink-300',
    icon: '🌸',
    ios: { material: 'pink light', accent: 'systemPink #FF2D55', background: '#FFF0F5', blur: '40px saturate 180%' }
  },
  mono: {
    id: 'mono',
    name: 'Mono',
    desc: 'iOS 26 Mono Liquid Glass',
    category: 'iOS 26',
    colors: { bg: '#F5F5F7', card: 'rgba(255,255,255,0.80)', accent: '#000000', text: '#000000' },
    preview: 'bg-[#F5F5F7] text-black border-black',
    icon: '◐',
    ios: { material: 'mono high contrast', accent: 'label #000000', blur: '30px saturate 160%' }
  }
}

export const THEME_CATEGORIES = ['All', 'iOS 26', 'iOS 26 Dark', 'iOS 26 Light']

export const VISUAL_STYLES = {
  liquid: { id: 'liquid', name: 'Liquid Glass', desc: 'iOS 26 translucent liquid glass - reflects surroundings, specular highlights', icon: '💎', vibe: 'iOS 26 Premium, translucent, depth', bestFor: 'iOS 26 Trading dashboards', ios: 'Liquid Glass material - blur 40px saturate 180%, translucent floats above content' },
  clay: { id: 'clay', name: 'Elevated Liquid', desc: 'iOS 26 elevated liquid glass - prominent material', icon: '🧸', vibe: 'iOS 26 Elevated, prominent, soft', bestFor: 'iOS 26 Wallets', ios: 'Thick material - blur 60px saturate 200%' },
  flat: { id: 'flat', name: 'Flat Liquid', desc: 'iOS 26 flat liquid - clean system backgrounds', icon: '◧', vibe: 'iOS 26 Clean, content-first', bestFor: 'iOS 26 Enterprise', ios: 'System background, separator 0.5px, thin material' },
  neo: { id: 'neo', name: 'Soft Liquid', desc: 'iOS 26 soft liquid - secondary backgrounds', icon: '◫', vibe: 'iOS 26 Minimalist, tactile', bestFor: 'iOS 26 Minimal', ios: 'Secondary system background, soft extruded' },
  brutal: { id: 'brutal', name: 'Neon Liquid', desc: 'iOS 26 neon liquid - vibrant accent glow', icon: '◩', vibe: 'iOS 26 Edgy, neon glow', bestFor: 'iOS 26 Creative', ios: 'Neon glow + liquid glass, accent glow 36px' },
}

export const useSettingsStore = create(
  persist(
    (set, get) => ({
      // Trading settings
      accountBalance: 10000,
      riskPerTrade: 0.02,
      timeframe: '1d',
      riskTolerance: 'moderate',
      autoRefresh: true,
      refreshInterval: 30,
      
      // Model settings
      modelWeights: {
        lstm: 0.25,
        transformer: 0.30,
        xgboost: 0.20,
        arima: 0.25
      },
      useStacking: true,
      useDynamicWeights: true,
      
      // Display settings
      theme: 'dark',
      visualStyle: 'liquid',
      accent: 'emerald',
      font: 'poppins',
      density: 'comfortable',
      animations: true,
      blur: true,
      showAdvanced: false,
      defaultSymbol: 'BTC-USD',
      chartType: 'candlestick',
      showVolume: true,
      showForecast: true,
      
      // Notifications
      enableNotifications: false,
      notifyOnBuy: true,
      notifyOnSell: true,
      notifyOnHighConfidence: true,
      
      // Trading preferences
      tradingStyle: 'swing',
      leveragePreference: 'low',
      stopLossType: 'atr',
      takeProfitType: 'risk_reward',
      
      // UI preferences
      sidebarCollapsed: false,
      showMarketTicker: true,
      
      // Actions
      updateAccountBalance: (balance) => set({ accountBalance: balance }),
      updateRiskPerTrade: (risk) => set({ riskPerTrade: risk }),
      updateTimeframe: (tf) => set({ timeframe: tf }),
      updateRiskTolerance: (tolerance) => set({ riskTolerance: tolerance }),
      updateModelWeights: (weights) => set({ modelWeights: weights }),
      updateTheme: (theme) => {
        if (!THEMES[theme]) theme = 'dark'
        set({ theme })
        if (typeof document !== 'undefined') {
          const html = document.documentElement
          Object.keys(THEMES).forEach(t => html.classList.remove(t))
          html.classList.remove('light', 'dark')
          html.classList.add(theme)
          const isLight = ['light', 'sakura', 'mono'].includes(theme)
          html.classList.add(isLight ? 'light' : 'dark')
          html.setAttribute('data-theme', theme)
          html.setAttribute('data-accent', get().accent || 'emerald')
          html.setAttribute('data-visual', get().visualStyle || 'liquid')
        }
      },
      updateVisualStyle: (visualStyle) => {
        if (!VISUAL_STYLES[visualStyle]) visualStyle = 'liquid'
        set({ visualStyle })
        if (typeof document !== 'undefined') {
          document.documentElement.setAttribute('data-visual', visualStyle)
        }
      },
      toggleTheme: () => {
        const current = get().theme
        const themes = Object.keys(THEMES)
        const idx = themes.indexOf(current)
        const next = themes[(idx + 1) % themes.length]
        get().updateTheme(next)
        return next
      },
      updateAccent: (accent) => {
        set({ accent })
        if (typeof document !== 'undefined') {
          document.documentElement.setAttribute('data-accent', accent)
        }
      },
      updateFont: (font) => set({ font }),
      updateDensity: (density) => set({ density }),
      toggleAnimations: () => set({ animations: !get().animations }),
      toggleBlur: () => set({ blur: !get().blur }),
      updateTradingStyle: (style) => set({ tradingStyle: style }),
      updateLeveragePreference: (lev) => set({ leveragePreference: lev }),
      updateChartType: (ct) => set({ chartType: ct }),
      updateDefaultSymbol: (sym) => set({ defaultSymbol: sym }),
      toggleAdvanced: () => set({ showAdvanced: !get().showAdvanced }),
      toggleNotifications: () => set({ enableNotifications: !get().enableNotifications }),
      toggleShowVolume: () => set({ showVolume: !get().showVolume }),
      toggleShowForecast: () => set({ showForecast: !get().showForecast }),
      toggleAutoRefresh: () => set({ autoRefresh: !get().autoRefresh }),
      toggleSidebar: () => set({ sidebarCollapsed: !get().sidebarCollapsed }),
      toggleMarketTicker: () => set({ showMarketTicker: !get().showMarketTicker }),
      
      // Risk tolerance presets
      setRiskPreset: (preset) => {
        const presets = {
          conservative: { riskPerTrade: 0.01, modelWeights: { lstm: 0.2, transformer: 0.3, xgboost: 0.2, arima: 0.3 } },
          moderate: { riskPerTrade: 0.02, modelWeights: { lstm: 0.25, transformer: 0.30, xgboost: 0.20, arima: 0.25 } },
          aggressive: { riskPerTrade: 0.05, modelWeights: { lstm: 0.3, transformer: 0.35, xgboost: 0.25, arima: 0.1 } }
        }
        const config = presets[preset]
        if (config) {
          set({ 
            riskTolerance: preset,
            riskPerTrade: config.riskPerTrade,
            modelWeights: config.modelWeights
          })
        }
      },
      
      // Reset to defaults
      resetSettings: () => {
        const defaultTheme = 'dark'
        set({
          accountBalance: 10000,
          riskPerTrade: 0.02,
          timeframe: '1d',
          riskTolerance: 'moderate',
          modelWeights: { lstm: 0.25, transformer: 0.30, xgboost: 0.20, arima: 0.25 },
          useStacking: true,
          useDynamicWeights: true,
          theme: defaultTheme,
          visualStyle: 'liquid',
          accent: 'emerald',
          font: 'poppins',
          density: 'comfortable',
          animations: true,
          blur: true,
          showAdvanced: false,
          defaultSymbol: 'BTC-USD',
          chartType: 'candlestick',
          showVolume: true,
          showForecast: true,
          enableNotifications: false,
          tradingStyle: 'swing',
          leveragePreference: 'low',
          sidebarCollapsed: false,
          showMarketTicker: true
        })
        if (typeof document !== 'undefined') {
          const html = document.documentElement
          Object.keys(THEMES).forEach(t => html.classList.remove(t))
          html.classList.remove('light', 'dark')
          html.classList.add(defaultTheme)
          html.classList.add('dark')
          html.setAttribute('data-theme', defaultTheme)
          html.setAttribute('data-accent', 'emerald')
        }
      }
    }),
    {
      name: 'crypto-pred-settings-v2',
      version: 4,
      onRehydrateStorage: () => (state) => {
        if (state?.theme && typeof document !== 'undefined') {
          const html = document.documentElement
          Object.keys(THEMES).forEach(t => html.classList.remove(t))
          html.classList.remove('light', 'dark')
          const theme = THEMES[state.theme] ? state.theme : 'dark'
          html.classList.add(theme)
          const isLight = ['light', 'sakura', 'mono'].includes(theme)
          html.classList.add(isLight ? 'light' : 'dark')
          html.setAttribute('data-theme', theme)
          html.setAttribute('data-accent', state.accent || 'emerald')
        }
      }
    }
  )
)
