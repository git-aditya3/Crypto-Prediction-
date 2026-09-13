import { useEffect, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'
import { useSettingsStore } from '../store/useSettingsStore'

export default function PriceChart({ data, forecast, height = 360, realtimePrice = null, symbol = 'BTC-USD' }) {
  const ref = useRef()
  const chartRef = useRef()
  const seriesRef = useRef({})
  const [showForecast, setShowForecast] = useState(true)
  const theme = useSettingsStore(s => s.theme)
  const isLight = theme === 'light' || theme === 'mono'

  useEffect(() => {
    if (!ref.current || !data) return
    ref.current.innerHTML = ''

    const chart = createChart(ref.current, {
      width: ref.current.clientWidth,
      height,
      layout: { 
        background: { type: 'solid', color: 'transparent' }, 
        textColor: isLight ? '#71717a' : '#52525b',
        fontFamily: 'Geist Mono, monospace',
        fontSize: 10
      },
      grid: { 
        vertLines: { color: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.04)', style: 1 }, 
        horzLines: { color: isLight ? 'rgba(0,0,0,0.04)' : 'rgba(255,255,255,0.04)', style: 1 } 
      },
      timeScale: { 
        borderColor: isLight ? '#e4e4e7' : '#27272a',
        timeVisible: true,
        secondsVisible: false,
        borderVisible: false,
      },
      rightPriceScale: { 
        borderColor: isLight ? '#e4e4e7' : '#27272a',
        borderVisible: false,
        scaleMargins: { top: 0.1, bottom: 0.1 }
      },
      crosshair: {
        mode: 1,
        vertLine: { color: isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)', width: 1, style: 2 },
        horzLine: { color: isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.1)', width: 1, style: 2 }
      },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
      handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true }
    })

    chartRef.current = chart

    const upColor = isLight ? '#18181b' : '#fafafa'
    const downColor = isLight ? '#a1a1aa' : '#52525b'

    const candleSeries = chart.addCandlestickSeries({
      upColor,
      downColor,
      borderUpColor: upColor,
      borderDownColor: downColor,
      wickUpColor: upColor,
      wickDownColor: downColor,
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
        color: isLight ? '#18181b' : '#fafafa', 
        lineWidth: 2,
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
        color: isLight ? '#18181b' : '#fafafa',
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
  }, [data, forecast, height, showForecast, isLight])

  useEffect(() => {
    if (seriesRef.current.candle && realtimePrice && seriesRef.current.liveLine) {
      try { seriesRef.current.candle.removePriceLine(seriesRef.current.liveLine) } catch {}
      const line = seriesRef.current.candle.createPriceLine({
        price: realtimePrice,
        color: isLight ? '#18181b' : '#fafafa',
        lineWidth: 1,
        lineStyle: 0,
        axisLabelVisible: true,
        title: 'LIVE',
      })
      seriesRef.current.liveLine = line
    }
  }, [realtimePrice, isLight])

  if (!data) {
    return (
      <div className="w-full rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-8 flex items-center justify-center gpu-accelerated" style={{ height }}>
        <div className="text-center">
          <div className="w-8 h-8 mx-auto mb-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 flex items-center justify-center animate-pulse">
            <div className="w-3 h-3 rounded bg-zinc-300 dark:bg-zinc-600"></div>
          </div>
          <div className="text-[11px] text-zinc-500">Loading chart</div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative rounded-xl overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 gpu-accelerated">
      <div className="absolute top-0 left-0 right-0 z-10 p-3 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-2 pointer-events-auto">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 shadow-sm">
            <div className="w-1.5 h-1.5 rounded-full bg-zinc-900 dark:bg-white animate-pulse"></div>
            <span className="text-[11px] font-medium tracking-tight text-zinc-900 dark:text-white">{symbol}</span>
          </div>
          {realtimePrice && !isNaN(realtimePrice) && (
            <div className="px-2.5 py-1 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-black border border-zinc-900 dark:border-white">
              <span className="text-[11px] mono font-medium">${(realtimePrice ?? 0).toLocaleString()}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-1.5 pointer-events-auto">
          <button
            onClick={() => setShowForecast(!showForecast)}
            className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-all duration-200 hover:scale-105 gpu-accelerated ${showForecast ? 'bg-zinc-900 text-white dark:bg-white dark:text-black border-zinc-900 dark:border-white' : 'bg-white dark:bg-zinc-900 text-zinc-500 border-zinc-200 dark:border-zinc-700 hover:border-zinc-300'}`}
          >
            Forecast
          </button>
        </div>
      </div>

      <div ref={ref} className="w-full" style={{ paddingTop: '48px' }} />
    </div>
  )
}
