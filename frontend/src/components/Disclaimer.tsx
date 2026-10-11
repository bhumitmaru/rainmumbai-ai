import { DISCLAIMER } from '../lib/constants'

export default function Disclaimer({ text = DISCLAIMER }: { text?: string }) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-800">
      ⚠️ {text}
    </div>
  )
}
