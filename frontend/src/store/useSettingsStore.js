import { create } from 'zustand'
import { persist } from 'zustand/middleware'

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
      
      // Actions
      updateAccountBalance: (balance) => set({ accountBalance: balance }),
      updateRiskPerTrade: (risk) => set({ riskPerTrade: risk }),
      updateTimeframe: (tf) => set({ timeframe: tf }),
      updateRiskTolerance: (tolerance) => set({ riskTolerance: tolerance }),
      updateModelWeights: (weights) => set({ modelWeights: weights }),
      updateTheme: (theme) => {
        set({ theme })
        if (typeof document !== 'undefined') {
          document.documentElement.classList.remove('light', 'dark')
          document.documentElement.classList.add(theme)
          document.documentElement.setAttribute('data-theme', theme)
        }
      },
      toggleTheme: () => {
        const current = get().theme
        const next = current === 'dark' ? 'light' : 'dark'
        set({ theme: next })
        if (typeof document !== 'undefined') {
          document.documentElement.classList.remove('light', 'dark')
          document.documentElement.classList.add(next)
          document.documentElement.setAttribute('data-theme', next)
        }
        return next
      },
      updateTradingStyle: (style) => set({ tradingStyle: style }),
      updateLeveragePreference: (lev) => set({ leveragePreference: lev }),
      updateChartType: (ct) => set({ chartType: ct }),
      updateDefaultSymbol: (sym) => set({ defaultSymbol: sym }),
      toggleAdvanced: () => set({ showAdvanced: !get().showAdvanced }),
      toggleNotifications: () => set({ enableNotifications: !get().enableNotifications }),
      toggleShowVolume: () => set({ showVolume: !get().showVolume }),
      toggleShowForecast: () => set({ showForecast: !get().showForecast }),
      toggleAutoRefresh: () => set({ autoRefresh: !get().autoRefresh }),
      
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
          showAdvanced: false,
          defaultSymbol: 'BTC-USD',
          chartType: 'candlestick',
          showVolume: true,
          showForecast: true,
          enableNotifications: false,
          tradingStyle: 'swing',
          leveragePreference: 'low'
        })
        if (typeof document !== 'undefined') {
          document.documentElement.classList.remove('light', 'dark')
          document.documentElement.classList.add(defaultTheme)
          document.documentElement.setAttribute('data-theme', defaultTheme)
        }
      }
    }),
    {
      name: 'crypto-pred-settings',
      version: 3,
      onRehydrateStorage: () => (state) => {
        if (state?.theme && typeof document !== 'undefined') {
          document.documentElement.classList.remove('light', 'dark')
          document.documentElement.classList.add(state.theme)
          document.documentElement.setAttribute('data-theme', state.theme)
        }
      }
    }
  )
)
