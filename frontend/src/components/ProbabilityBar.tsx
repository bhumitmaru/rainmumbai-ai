import type { DirectionProbabilities } from '../types'

export default function ProbabilityBar({ probabilities }: { probabilities: DirectionProbabilities }) {
  const segments = [
    { label: 'Increase', value: probabilities.increase, color: '#22c55e' },
    { label: 'No Change', value: probabilities.no_change, color: '#f59e0b' },
    { label: 'Decrease', value: probabilities.decrease, color: '#ef4444' },
  ]
  return (
    <div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-200">
        {segments.map((s) => (
          <div key={s.label} style={{ width: `${s.value}%`, backgroundColor: s.color }} />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap justify-between gap-2 text-xs">
        {segments.map((s) => (
          <span key={s.label} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
            {s.label} {s.value.toFixed(1)}%
          </span>
        ))}
      </div>
    </div>
  )
}
