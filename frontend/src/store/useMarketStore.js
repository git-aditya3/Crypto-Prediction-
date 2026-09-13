import { create } from 'zustand'
import { fetchTicker24h, BinanceTickerWS, SUPPORTED } from '../api/binance'
import { api } from '../api/client'

export const useMarketStore = create((set, get) => ({
  tickers: {}, // symbol -> ticker data
  prices: {}, // symbol -> price
  loading: true,
  isLive: false,
  lastUpdate: null,
  selectedSymbol: 'BTC-USD',
  ws: null,
  error: null,

  setSelectedSymbol: (symbol) => set({ selectedSymbol: symbol }),

  // Fetch all tickers via Binance direct + fallback to backend
  fetchAllTickers: async () => {
    set({ loading: true, error: null })
    try {
      // Try Binance direct first
      const data = await fetchTicker24h()
      const tickers = {}
      const prices = {}
      data.forEach(t => {
        // Map Binance symbol back to our format
        const ourSymbol = Object.entries({
          'BTCUSDT': 'BTC-USD',
          'ETHUSDT': 'ETH-USD',
          'BNBUSDT': 'BNB-USD',
          'SOLUSDT': 'SOL-USD',
          'XRPUSDT': 'XRP-USD',
          'ADAUSDT': 'ADA-USD',
          'DOGEUSDT': 'DOGE-USD',
          'AVAXUSDT': 'AVAX-USD',
          'DOTUSDT': 'DOT-USD',
          'MATICUSDT': 'MATIC-USD',
          'POLUSDT': 'MATIC-USD',
        }).find(([k]) => k === t.symbol)?.[1]
        if (ourSymbol) {
          tickers[ourSymbol] = {
            symbol: ourSymbol,
            binanceSymbol: t.symbol,
            price: parseFloat(t.lastPrice),
            lastPrice: parseFloat(t.lastPrice),
            priceChange: parseFloat(t.priceChange),
            priceChangePercent: parseFloat(t.priceChangePercent),
            high: parseFloat(t.highPrice),
            low: parseFloat(t.lowPrice),
            volume: parseFloat(t.volume),
            quoteVolume: parseFloat(t.quoteVolume),
            open: parseFloat(t.openPrice),
            trades: t.count,
            raw: t
          }
          prices[ourSymbol] = parseFloat(t.lastPrice)
        }
      })
      set({ tickers, prices, loading: false, lastUpdate: new Date() })
      return tickers
    } catch (e) {
      console.warn('Binance direct failed, trying backend', e)
      try {
        // Fallback to backend /realtime/prices or /symbols?
        // Try fetching each symbol individually via backend
        const symbols = SUPPORTED
        const results = await Promise.allSettled(
          symbols.map(sym => api.getRealtimePrice(sym).catch(() => null))
        )
        const tickers = {}
        const prices = {}
        results.forEach((r, i) => {
          if (r.status === 'fulfilled' && r.value) {
            const sym = symbols[i]
            const t = r.value.ticker || {}
            tickers[sym] = {
              symbol: sym,
              binanceSymbol: r.value.binance_symbol,
              price: r.value.price || parseFloat(t.lastPrice || 0),
              lastPrice: parseFloat(t.lastPrice || r.value.price || 0),
              priceChangePercent: parseFloat(t.priceChangePercent || 0),
              high: parseFloat(t.highPrice || 0),
              low: parseFloat(t.lowPrice || 0),
              volume: parseFloat(t.volume || 0),
              quoteVolume: parseFloat(t.quoteVolume || 0),
              open: parseFloat(t.openPrice || 0),
            }
            prices[sym] = tickers[sym].price
          }
        })
        if (Object.keys(tickers).length > 0) {
          set({ tickers, prices, loading: false, lastUpdate: new Date() })
          return tickers
        }
        throw new Error('No tickers from backend')
      } catch (e2) {
        console.error('All ticker fetches failed', e2)
        set({ error: e2.message, loading: false })
        return {}
      }
    }
  },

  // Start live WebSocket
  startLive: () => {
    const { ws, tickers } = get()
    if (ws) return

    const symbols = Object.keys(tickers).length ? Object.keys(tickers) : SUPPORTED.slice(0, 6)

    const newWs = new BinanceTickerWS(symbols, (update) => {
      set(state => ({
        tickers: {
          ...state.tickers,
          [update.symbol]: {
            ...(state.tickers[update.symbol] || {}),
            ...update,
            price: update.price,
            lastPrice: update.price,
          }
        },
        prices: {
          ...state.prices,
          [update.symbol]: update.price
        },
        lastUpdate: new Date()
      }))
    })

    newWs.connect()
    set({ ws: newWs, isLive: true })
  },

  stopLive: () => {
    const { ws } = get()
    if (ws) {
      ws.disconnect()
      set({ ws: null, isLive: false })
    }
  },

  // Update single price
  updatePrice: (symbol, price) => set(state => ({
    prices: { ...state.prices, [symbol]: price },
    tickers: {
      ...state.tickers,
      [symbol]: { ...(state.tickers[symbol] || {}), price, lastPrice: price }
    }
  }))
}))
