import { useSettingsStore } from '../store/useSettingsStore'
import { useEffect, useState } from 'react'
import { BookOpen, Plus, TrendingUp, Award } from 'lucide-react'
import { api } from '../api/client'

export default function Journal() {
  const theme = useSettingsStore(s => s.theme)
  const isDark = theme === 'dark'

  const [entries, setEntries] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ symbol: 'BTC-USD', side: 'LONG', entry_price: 100000, quantity: 0.01, strategy: 'AI Ensemble', notes: '', emotions: '', lessons: '', tags: '' })

  const safeFixed = (v, d=2) => {
    if (v == null) return '0.00'
    const n = typeof v === 'number' ? v : parseFloat(v)
    if (isNaN(n)) return '0.00'
    return n.toFixed(d)
  }

  const fetchData = async () => {
    try {
      const [jRes, sRes] = await Promise.all([
        api.getJournal().catch(() => fetch('/api/journal').then(r => r.json())),
        api.getJournalStats().catch(() => fetch('/api/journal/stats').then(r => r.json()))
      ])
      setEntries(jRes.entries || [])
      setStats(jRes.stats || sRes)
    } catch (e) { console.error(e) } finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const addEntry = async () => {
    try {
      const payload = { ...form, entry_price: parseFloat(form.entry_price)||0, quantity: parseFloat(form.quantity)||0, tags: form.tags.split(',').map(t => t.trim()).filter(Boolean) }
      await api.addJournalEntry(payload).catch(() => fetch('/api/journal/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }))
      setShowAdd(false); fetchData()
    } catch (e) { alert(e.message) }
  }

  if (loading) return <div className="p-6 text-center">Loading real trading journal...</div>

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-6 font-poppins space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black flex items-center gap-3"><BookOpen className="text-blue-400" /> Trading Journal - Real Trades</h1>
          <p className="text-zinc-500 mt-1">Log real trades with notes, emotions, lessons - improve actual trading</p>
        </div>
        <button onClick={() => setShowAdd(true)} className="px-4 py-2 rounded-xl bg-blue-500 text-white font-bold flex items-center gap-2"><Plus size={16} /> Add Entry</button>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
            <div className="text-xs text-zinc-500 uppercase">Total Entries</div>
            <div className="text-2xl font-black">{stats.total_entries ?? 0}</div>
          </div>
          <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
            <div className="text-xs text-zinc-500 uppercase">Win Rate</div>
            <div className="text-2xl font-black text-emerald-600">{safeFixed(stats.win_rate,1)}%</div>
          </div>
          <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
            <div className="text-xs text-zinc-500 uppercase">Total P&L</div>
            <div className={`text-2xl font-black ${(stats.total_pnl??0) >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>${safeFixed(stats.total_pnl,2)}</div>
          </div>
          <div className="p-4 rounded-2xl ui-card border border-black/5 dark:border-white/5">
            <div className="text-xs text-zinc-500 uppercase">Avg P&L</div>
            <div className="text-2xl font-black">${safeFixed(stats.avg_pnl,2)}</div>
          </div>
        </div>
      )}

      <div className="p-5 rounded-2xl ui-card border border-black/5 dark:border-white/5">
        <h3 className="font-bold mb-4">Journal Entries - Real Trading History</h3>
        {entries.length === 0 ? (
          <div className="text-center py-12 text-zinc-500">No journal entries - log your real trades to improve</div>
        ) : (
          <div className="space-y-4">
            {entries.map(entry => (
              <div key={entry.id} className="p-4 rounded-xl bg-transparent border border-black/5 dark:border-white/5/50">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold">{entry.symbol || 'Unknown'}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${entry.side === 'LONG' ? 'bg-zinc-100 dark:bg-zinc-800 text-emerald-600' : 'bg-red-500/10 text-red-500'}`}>{entry.side || 'LONG'}</span>
                    <span className="text-xs text-zinc-500">{safeFixed(entry.quantity,6)} @ ${safeFixed(entry.entry_price,2)}</span>
                    <span className={`text-xs font-bold ${(entry.pnl??0) >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>${safeFixed(entry.pnl,2)} ({safeFixed(entry.pnl_pct,2)}%)</span>
                  </div>
                  <span className="text-[10px] text-zinc-500">{entry.timestamp ? new Date(entry.timestamp).toLocaleString() : ''}</span>
                </div>
                <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                  <div className="p-2 rounded-lg ui-card border border-black/5 dark:border-white/5/30">
                    <div className="text-[10px] text-zinc-500 uppercase">Strategy</div>
                    <div className="font-medium mt-1">{entry.strategy || 'Unknown'}</div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {entry.tags?.map((tag, i) => <span key={i} className="px-1.5 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-500 text-[10px]">{tag}</span>)}
                    </div>
                  </div>
                  <div className="p-2 rounded-lg ui-card border border-black/5 dark:border-white/5/30">
                    <div className="text-[10px] text-zinc-500 uppercase">Notes</div>
                    <div className="mt-1 text-zinc-500">{entry.notes || 'No notes'}</div>
                  </div>
                  <div className="p-2 rounded-lg ui-card border border-black/5 dark:border-white/5/30">
                    <div className="text-[10px] text-zinc-500 uppercase">Emotions & Lessons</div>
                    <div className="mt-1"><span className="text-zinc-500">Emotions:</span> {entry.emotions || 'N/A'}</div>
                    <div className="mt-1"><span className="text-zinc-500">Lessons:</span> {entry.lessons || 'N/A'}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur p-4 overflow-auto">
          <div className="p-6 rounded-2xl ui-card border border-black/5 dark:border-white/5 w-full max-w-lg max-h-[90vh] overflow-auto">
            <h3 className="font-bold text-lg mb-4">Add Real Trade Journal Entry</h3>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <select value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                  {['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD'].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
                <select value={form.side} onChange={e => setForm({ ...form, side: e.target.value })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">
                  <option value="LONG">LONG</option>
                  <option value="SHORT">SHORT</option>
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input type="number" placeholder="Entry Price" value={form.entry_price} onChange={e => setForm({ ...form, entry_price: e.target.value })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
                <input type="number" step="0.0001" placeholder="Quantity" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} className="px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              </div>
              <input placeholder="Strategy" value={form.strategy} onChange={e => setForm({ ...form, strategy: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              <textarea placeholder="Notes - why you took this trade" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5 h-20" />
              <input placeholder="Emotions - how you felt" value={form.emotions} onChange={e => setForm({ ...form, emotions: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              <input placeholder="Lessons learned" value={form.lessons} onChange={e => setForm({ ...form, lessons: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              <input placeholder="Tags comma separated e.g. breakout, high conviction" value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })} className="w-full px-3 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5" />
              <div className="flex gap-2">
                <button onClick={() => setShowAdd(false)} className="flex-1 py-2 rounded-xl bg-transparent border border-black/5 dark:border-white/5">Cancel</button>
                <button onClick={addEntry} className="flex-1 py-2 rounded-xl bg-blue-500 text-white font-bold">Add Real Entry</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
