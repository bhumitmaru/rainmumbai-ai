import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Spinner from '../components/Spinner'
import type { HistoryItem } from '../types'

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [total, setTotal] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/predictions/history?limit=200')
      .then((r) => {
        setItems(r.data.items)
        setTotal(r.data.total)
      })
      .catch((err) => setError(err?.response?.data?.detail ?? 'Failed to load history'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner label="Loading history…" />
  if (error) return <div className="text-slate-600">{error}</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-800">Historical Predictions</h1>
        <span className="text-sm text-slate-500">{total} total</span>
      </div>
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Target</th>
              <th className="px-4 py-3">Predicted</th>
              <th className="px-4 py-3">Actual</th>
              <th className="px-4 py-3">Deviation</th>
              <th className="px-4 py-3">Direction</th>
              <th className="px-4 py-3">Actual Dir</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Version</th>
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={i.id} className="border-t border-slate-100">
                <td className="px-4 py-3 whitespace-nowrap">
                  {new Date(i.target_timestamp).toLocaleString()}
                </td>
                <td className="px-4 py-3">{i.predicted_index.toFixed(2)}</td>
                <td className="px-4 py-3">{i.actual_index != null ? i.actual_index.toFixed(2) : '—'}</td>
                <td className="px-4 py-3">
                  {i.expected_deviation >= 0 ? '+' : ''}
                  {i.expected_deviation.toFixed(2)}
                </td>
                <td className="px-4 py-3">{i.direction}</td>
                <td className="px-4 py-3">{i.actual_direction ?? '—'}</td>
                <td className="px-4 py-3">{i.confidence_overall.toFixed(0)}%</td>
                <td className="px-4 py-3 text-xs">{i.model_version}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-slate-500">
                  No historical predictions yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
