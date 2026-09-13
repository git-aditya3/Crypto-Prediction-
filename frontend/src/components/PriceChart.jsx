import { useEffect, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'
import { useSettingsStore } from '../store/useSettingsStore'

export default function PriceChart({ data, forecast, height = 360, realtimePrice = null, symbol = 'BTC-USD' }) {
  const ref = useRef()
  const chartRef = useRef()
  const seriesRef = useRef({})
  const [showForecast, setShowForecast] = useState(true)
  const theme = useSettingsStore(s => s.theme)

  const getThemeColors = () => {
    const isLight = theme === 'light' || theme === 'sakura'
    if (theme === 'midnight') return { text: '#a5a5c5', grid: 'rgba(30,30,50,0.5)', border: '#1e1e32', up: '#8b5cf6', down: '#ef4444', forecast: '#8b5cf6', live: '#8b5cf6' }
    if (theme === 'ocean') return { text: '#7fb5cc', grid: 'rgba(20,48,77,0.5)', border: '#14304d', up: '#06b6d4', down: '#ef4444', forecast: '#06b6d4', live: '#06b6d4' }
    if (theme === 'forest') return { text: '#7ab895', grid: 'rgba(20,61,30,0.5)', border: '#143d1e', up: '#10b981', down: '#ef4444', forecast: '#10b981', live: '#10b981' }
    if (theme === 'sunset') return { text: '#d4a574', grid: 'rgba(61,31,31,0.5)', border: '#3d1f1f', up: '#f97316', down: '#ef4444', forecast: '#f97316', live: '#f97316' }
    if (theme === 'neon') return { text: '#d4a5c5', grid: 'rgba(45,27,78,0.5)', border: '#2d1b4e', up: '#ec4899', down: '#ef4444', forecast: '#ec4899', live: '#ec4899' }
    if (theme === 'cyberpunk') return { text: '#8ab58a', grid: 'rgba(42,42,74,0.5)', border: '#2a2a4a', up: '#00ff9f', down: '#ff0055', forecast: '#00ff9f', live: '#00ff9f' }
    if (theme === 'dracula') return { text: '#a5a5c5', grid: 'rgba(68,71,90,0.5)', border: '#44475a', up: '#50fa7b', down: '#ff5555', forecast: '#bd93f9', live: '#bd93f9' }
    if (theme === 'nord') return { text: '#a5adbd', grid: 'rgba(76,86,106,0.3)', border: '#4c566a', up: '#a3be8c', down: '#bf616a', forecast: '#88c0d0', live: '#88c0d0' }
    if (isLight) return { text: '#94a3b8', grid: 'rgba(0,0,0,0.04)', border: '#e2e8f0', up: '#10b981', down: '#ef4444', forecast: '#0f172a', live: '#0f172a' }
    return { text: '#71717a', grid: 'rgba(255,255,255,0.04)', border: '#1f1f23', up: '#10b981', down: '#ef4444', forecast: '#fafafa', live: '#fafafa' }
  }

  useEffect(() => {
    if (!ref.current || !data) return
    ref.current.innerHTML = ''

    const colors = getThemeColors()

    const chart = createChart(ref.current, {
      width: ref.current.clientWidth,
      height,
      layout: { 
        background: { type: 'solid', color: 'transparent' }, 
        textColor: colors.text,
        fontFamily: 'Geist Mono, monospace',
        fontSize: 10
      },
      grid: { 
        vertLines: { color: colors.grid, style: 1 }, 
        horzLines: { color: colors.grid, style: 1 } 
      },
      timeScale: { 
        borderColor: colors.border,
        timeVisible: true,
        secondsVisible: false,
        borderVisible: false,
      },
      rightPriceScale: { 
        borderColor: colors.border,
        borderVisible: false,
        scaleMargins: { top: 0.1, bottom: 0.1 }
      },
      crosshair: {
        mode: 1,
        vertLine: { color: colors.grid, width: 1, style: 2 },
        horzLine: { color: colors.grid, width: 1, style: 2 }
      },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
      handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true }
    })

    chartRef.current = chart

    const candleSeries = chart.addCandlestickSeries({
      upColor: colors.up,
      downColor: colors.down,
      borderUpColor: colors.up,
      borderDownColor: colors.down,
      wickUpColor: colors.up,
      wickDownColor: colors.down,
      priceFormat: { type: 'price', precision: 2, minMove: 0.01 }
    })

    const candles = (data.dates || []).map((d, i) => ({
      time: d,
      open: data.open?.[i] ?? 0,
      high: data.high?.[i] ?? 0,
      low: data.low?.[i] ?? 0,
      close: data.close?.[i] ?? 0
    })).filter(c => c.open && c.close)

    if (candles.length === 0) return

    candleSeries.setData(candles)
    seriesRef.current.candle = candleSeries

    if (forecast && showForecast && forecast.ensemble) {
      const ensembleSeries = chart.addLineSeries({ 
        color: colors.forecast, 
        lineWidth: 2.5,
        priceLineVisible: false,
        lastValueVisible: true,
      })
      const fcData = forecast.dates.map((d, i) => ({
        time: d,
        value: forecast.ensemble[i]
      })).filter(d => d.value != null)
      ensembleSeries.setData(fcData)
      seriesRef.current.ensemble = ensembleSeries
    }

    if (realtimePrice && !isNaN(realtimePrice) && realtimePrice > 0) {
      const priceLine = candleSeries.createPriceLine({
        price: realtimePrice,
        color: colors.live,
        lineWidth: 1,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'LIVE',
      })
      seriesRef.current.liveLine = priceLine
    }

    chart.timeScale().fitContent()

    const handleResize = () => {
      if (ref.current) {
        chart.applyOptions({ width: ref.current.clientWidth })
      }
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [data, forecast, height, showForecast, theme])

  useEffect(() => {
    if (seriesRef.current.candle && realtimePrice && seriesRef.current.liveLine) {
      try { seriesRef.current.candle.removePriceLine(seriesRef.current.liveLine) } catch {}
      const colors = getThemeColors()
      const line = seriesRef.current.candle.createPriceLine({
        price: realtimePrice,
        color: colors.live,
        lineWidth: 1,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'LIVE',
      })
      seriesRef.current.liveLine = line
    }
  }, [realtimePrice, theme])

  if (!data) {
    return (
      <div className="w-full rounded-xl border border-[var(--border)] bg-[var(--card)] p-8 flex items-center justify-center gpu-accelerated" style={{ height }}>
        <div className="text-center">
          <div className="w-8 h-8 mx-auto mb-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] flex items-center justify-center animate-pulse">
            <div className="w-3 h-3 rounded bg-[var(--text-faint)]"></div>
          </div>
          <div className="text-[11px] text-[var(--text-muted)]">Loading chart</div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative rounded-xl overflow-hidden border border-[var(--border)] bg-[var(--card)] gpu-accelerated">
      <div className="absolute top-0 left-0 right-0 z-10 p-3 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2 pointer-events-auto">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--card)] border border-[var(--border)] shadow-sm">
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse"></div>
            <span className="text-[11px] font-medium tracking-tight text-[var(--text)]">{symbol}</span>
          </div>
          {realtimePrice && !isNaN(realtimePrice) && (
            <div className="px-2.5 py-1 rounded-full bg-[var(--accent)] text-white border border-[var(--accent)] shadow-sm">
              <span className="text-[11px] mono font-medium">${(realtimePrice ?? 0).toLocaleString()}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-1.5 pointer-events-auto">
          <button
            onClick={() => setShowForecast(!showForecast)}
            className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-all duration-200 hover:scale-105 gpu-accelerated ${showForecast ? 'bg-[var(--accent)] text-white border-[var(--accent)] shadow-sm' : 'bg-[var(--card)] text-[var(--text-muted)] border-[var(--border)] hover:border-[var(--border-strong)]'}`}
          >
            Forecast
          </button>
        </div>
      </div>

      <div ref={ref} className="w-full" style={{ paddingTop: '48px' }} />
    </div>
  )
}
