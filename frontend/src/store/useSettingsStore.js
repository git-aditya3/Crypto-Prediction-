import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const THEMES = {
  light: {
    id: 'light',
    name: 'Light',
    desc: 'Clean & minimal',
    category: 'Minimal',
    colors: { bg: '#E3EDF7', card: '#ffffff', accent: '#0f172a', text: '#0f172a' },
    preview: 'bg-[#E3EDF7] text-black border-black/10',
    icon: '☀️'
  },
  dark: {
    id: 'dark',
    name: 'Dark',
    desc: 'Pure black',
    category: 'Minimal',
    colors: { bg: '#000000', card: '#161618', accent: '#ffffff', text: '#F1F5F9' },
    preview: 'bg-black text-white border-white/10',
    icon: '🌙'
  },
  midnight: {
    id: 'midnight',
    name: 'Midnight',
    desc: 'Deep purple',
    category: 'Dark',
    colors: { bg: '#0a0a12', card: '#13131f', accent: '#8b5cf6', text: '#e9e9ff' },
    preview: 'bg-[#0a0a12] text-violet-300 border-violet-500/20',
    icon: '🌌'
  },
  ocean: {
    id: 'ocean',
    name: 'Ocean',
    desc: 'Deep sea blue',
    category: 'Dark',
    colors: { bg: '#060e1a', card: '#0e1e2e', accent: '#06b6d4', text: '#c7f0ff' },
    preview: 'bg-[#060e1a] text-cyan-300 border-cyan-500/20',
    icon: '🌊'
  },
  forest: {
    id: 'forest',
    name: 'Forest',
    desc: 'Emerald dark',
    category: 'Dark',
    colors: { bg: '#06120a', card: '#0f2214', accent: '#10b981', text: '#d1fae5' },
    preview: 'bg-[#06120a] text-emerald-300 border-emerald-500/20',
    icon: '🌲'
  },
  sunset: {
    id: 'sunset',
    name: 'Sunset',
    desc: 'Warm dusk',
    category: 'Colorful',
    colors: { bg: '#1a0a0a', card: '#2a1515', accent: '#f97316', text: '#ffedd5' },
    preview: 'bg-[#1a0a0a] text-orange-300 border-orange-500/20',
    icon: '🌅'
  },
  neon: {
    id: 'neon',
    name: 'Neon',
    desc: 'Cyber glow',
    category: 'Colorful',
    colors: { bg: '#0a0014', card: '#1a0a2e', accent: '#ec4899', text: '#fce7f3' },
    preview: 'bg-[#0a0014] text-pink-300 border-pink-500/20',
    icon: '💜'
  },
  nord: {
    id: 'nord',
    name: 'Nord',
    desc: 'Arctic frost',
    category: 'Minimal',
    colors: { bg: '#2e3440', card: '#3b4252', accent: '#88c0d0', text: '#eceff4' },
    preview: 'bg-[#2e3440] text-slate-200 border-slate-500/20',
    icon: '❄️'
  },
  dracula: {
    id: 'dracula',
    name: 'Dracula',
    desc: 'Vampire dark',
    category: 'Dark',
    colors: { bg: '#282a36', card: '#343746', accent: '#bd93f9', text: '#f8f8f2' },
    preview: 'bg-[#282a36] text-purple-200 border-purple-500/20',
    icon: '🧛'
  },
  cyberpunk: {
    id: 'cyberpunk',
    name: 'Cyberpunk',
    desc: 'Neon city',
    category: 'Colorful',
    colors: { bg: '#0f0f1e', card: '#1a1a2e', accent: '#00ff9f', text: '#00ff9f' },
    preview: 'bg-[#0f0f1e] text-green-300 border-green-400/20',
    icon: '🤖'
  },
  sakura: {
    id: 'sakura',
    name: 'Sakura',
    desc: 'Cherry blossom',
    category: 'Light',
    colors: { bg: '#fdf2f8', card: '#ffffff', accent: '#ec4899', text: '#831843' },
    preview: 'bg-[#fdf2f8] text-pink-800 border-pink-300',
    icon: '🌸'
  },
  mono: {
    id: 'mono',
    name: 'Mono',
    desc: 'High contrast',
    category: 'Minimal',
    colors: { bg: '#ffffff', card: '#000000', accent: '#000000', text: '#000000' },
    preview: 'bg-white text-black border-black',
    icon: '◐'
  }
}

export const THEME_CATEGORIES = ['All', 'Minimal', 'Dark', 'Colorful', 'Light']

export const VISUAL_STYLES = {
  liquid: { id: 'liquid', name: 'Liquid Glass', desc: 'Premium frosted glass', icon: '💎', vibe: 'Premium, sleek, high-tech', bestFor: 'Trading dashboards' },
  clay: { id: 'clay', name: 'Claymorphism', desc: 'Soft 3D clay', icon: '🧸', vibe: 'Friendly, 3D, gamified', bestFor: 'Crypto/Web3 wallets' },
  flat: { id: 'flat', name: 'Flat 2.0', desc: 'Clean & functional', icon: '◧', vibe: 'Professional, legible', bestFor: 'Enterprise data' },
  neo: { id: 'neo', name: 'Neomorphism', desc: 'Soft extruded', icon: '◫', vibe: 'Minimalist, tactile', bestFor: 'Minimal dashboards' },
  brutal: { id: 'brutal', name: 'Neo-Brutalism', desc: 'Raw & edgy', icon: '◩', vibe: 'Edgy, creative', bestFor: 'Creative trading' },
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
