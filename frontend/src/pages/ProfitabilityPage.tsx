import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Disclaimer from '../components/Disclaimer'
import KpiCard from '../components/KpiCard'
import Spinner from '../components/Spinner'
import type { Profitability } from '../types'

export default function ProfitabilityPage() {
  const [data, setData] = useState<Profitability | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get('/profitability')
      .then((r) => setData(r.data as Profitability))
      .catch((err) => setError(err?.response?.data?.detail ?? 'Failed to load profitability'))
  }, [])

  if (!data) return error ? <div className="text-slate-600">{error}</div> : <Spinner />

  const pnlColor = data.total_pnl_inr >= 0 ? 'text-green-600' : 'text-red-600'

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-slate-800">Profitability Analysis</h1>
      <p className="text-sm text-slate-500">
        Decision rule: <span className="font-medium text-slate-700">{data.decision_rule}</span> · {data.lots} lot
        (s) · ₹{data.inr_per_mm} per mm. Hypothetical, based on historical predictions.
      </p>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <KpiCard title="Total P&L" value={`₹${data.total_pnl_inr.toFixed(2)}`} accent={pnlColor} />
        <KpiCard title="Trades" value={data.trade_count} />
        <KpiCard title="Win Rate" value={`${data.win_rate_pct.toFixed(1)}%`} />
        <KpiCard title="Multiplier" value={`₹${data.inr_per_mm}/mm`} />
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Target</th>
              <th className="px-4 py-3">Direction</th>
              <th className="px-4 py-3">Current</th>
              <th className="px-4 py-3">Actual</th>
              <th className="px-4 py-3">Realized Δ</th>
              <th className="px-4 py-3">P&L (₹)</th>
            </tr>
          </thead>
          <tbody>
            {data.trades.map((t, idx) => (
              <tr key={idx} className="border-t border-slate-100">
                <td className="px-4 py-3 whitespace-nowrap">
                  {new Date(t.target_timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3">{t.direction}</td>
                <td className="px-4 py-3">{t.current_index.toFixed(2)}</td>
                <td className="px-4 py-3">{t.actual_index.toFixed(2)}</td>
                <td className="px-4 py-3">
                  {t.realized_delta >= 0 ? '+' : ''}
                  {t.realized_delta.toFixed(2)}
                </td>
                <td className={`px-4 py-3 font-medium ${t.pnl_inr >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{t.pnl_inr.toFixed(2)}
                </td>
              </tr>
            ))}
            {data.trades.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No matured trades yet. Profitability appears once predictions are compared with observed outcomes.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Disclaimer text={data.disclaimer} />
    </div>
  )
}
