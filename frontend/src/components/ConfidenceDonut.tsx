import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { ConfidenceBreakdown } from '../types'

export default function ConfidenceDonut({ confidence }: { confidence: ConfidenceBreakdown }) {
  const data = [
    { name: 'Data Quality', value: confidence.data_quality },
    { name: 'Model Performance', value: confidence.model_performance },
    { name: 'Stability', value: confidence.stability },
  ]
  const colors = ['#3b82f6', '#22c55e', '#a855f7']
  return (
    <div className="flex flex-col items-center">
      <ResponsiveContainer width="100%" height={190}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={52}
            outerRadius={80}
            paddingAngle={3}
            strokeWidth={1}
          >
            {data.map((_, i) => (
              <Cell key={i} fill={colors[i]} />
            ))}
          </Pie>
          <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      <div className="text-sm text-slate-600">
        Overall confidence: <span className="font-bold text-slate-800">{confidence.overall}%</span>
      </div>
    </div>
  )
}
