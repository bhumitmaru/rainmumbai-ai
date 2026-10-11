import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Disclaimer from '../components/Disclaimer'
import ProbabilityBar from '../components/ProbabilityBar'
import Spinner from '../components/Spinner'
import { DISCLAIMER } from '../lib/constants'
import type { Prediction } from '../types'

export default function PredictionsPage() {
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get('/predictions/latest')
      .then((r) => setPrediction(r.data as Prediction))
      .catch((err) => setError(err?.response?.data?.detail ?? 'Failed to load prediction'))
  }, [])

  if (!prediction) return error ? <div className="text-slate-600">{error}</div> : <Spinner />

  const rows = [
    { label: 'Current Index', value: prediction.current_index.toFixed(2) },
    { label: 'Predicted Index', value: prediction.predicted_index.toFixed(2) },
    { label: 'Expected Deviation', value: `${prediction.expected_deviation >= 0 ? '+' : ''}${prediction.expected_deviation.toFixed(2)}` },
    { label: 'Direction', value: prediction.direction },
    { label: 'Current Category', value: prediction.category_current },
    { label: 'Predicted Category', value: prediction.category_predicted },
    { label: 'Target Timestamp', value: new Date(prediction.target_timestamp).toLocaleString() },
    { label: 'Model Version', value: prediction.model_version },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-slate-800">Latest Prediction</h1>
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="grid gap-4 sm:grid-cols-2">
          {rows.map((r) => (
            <div key={r.label} className="flex justify-between border-b border-slate-100 py-2">
              <span className="text-sm text-slate-500">{r.label}</span>
              <span className="text-sm font-semibold text-slate-800">{r.value}</span>
            </div>
          ))}
        </div>
        <div className="mt-5">
          <h3 className="mb-2 text-sm font-semibold text-slate-700">Direction Probabilities</h3>
          <ProbabilityBar probabilities={prediction.probabilities} />
        </div>
        <div className="mt-5 grid grid-cols-3 gap-4 text-center">
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">Data Quality</div>
            <div className="text-lg font-bold text-slate-800">{prediction.confidence.data_quality}%</div>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">Model Performance</div>
            <div className="text-lg font-bold text-slate-800">{prediction.confidence.model_performance}%</div>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">Stability</div>
            <div className="text-lg font-bold text-slate-800">{prediction.confidence.stability}%</div>
          </div>
        </div>
      </div>
      <Disclaimer text={prediction.disclaimer || DISCLAIMER} />
    </div>
  )
}
