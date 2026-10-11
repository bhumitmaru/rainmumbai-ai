import { render, screen, waitFor } from '@testing-library/react'
import PerformancePage from './PerformancePage'

const getMock = vi.fn()

vi.mock('../api/client', () => ({
  api: {
    get: (...args: unknown[]) => getMock(...args),
  },
}))

function perfPayload(sampleCount = 1) {
  return {
    mae: 1.2,
    rmse: 2.1,
    direction_accuracy: 0.6,
    direction_f1: 0.55,
    sample_count: sampleCount,
    sample_total: sampleCount,
    last_evaluated_at: null,
    model_version: 'ncdex_cdr_v1',
    disclaimer: 'Predictions are probabilistic.',
    baseline: { label: 'Persistence (No Change / predicted deviation = 0)', mae: 2.4, direction_accuracy: 0.4 },
    evaluated_from: sampleCount ? '2025-06-02T08:30:00Z' : null,
    evaluated_to: sampleCount ? '2025-06-02T08:30:00Z' : null,
    error_series: sampleCount ? [{ target_timestamp: '2025-06-02T08:30:00Z', value: 1.1 }] : [],
    cumulative_accuracy_series: sampleCount ? [{ target_timestamp: '2025-06-02T08:30:00Z', value: 100 }] : [],
    limit: 25,
    offset: 0,
    evaluation_runs: [],
    samples: sampleCount
      ? [
          {
            prediction_id: 1,
            target_timestamp: '2025-06-02T08:30:00Z',
            predicted_index: 2208,
            actual_index: 2207,
            error: 1,
            abs_error: 1,
            direction: 'Increase',
            actual_direction: 'Increase',
            direction_correct: true,
            source: 'backfill',
          },
        ]
      : [],
  }
}

describe('PerformancePage', () => {
  afterEach(() => {
    getMock.mockReset()
  })

  it('renders metrics, charts, and table rows', async () => {
    getMock.mockResolvedValueOnce({ data: perfPayload(1) })
    render(<PerformancePage />)
    await waitFor(() => expect(screen.getByText('Historical Performance')).toBeInTheDocument())
    expect(screen.getByText('MAE')).toBeInTheDocument()
    expect(screen.getByText(/Cumulative direction accuracy/i)).toBeInTheDocument()
    expect(screen.getByText(/Backfilled/i)).toBeInTheDocument()
  })

  it('renders empty state when samples are zero', async () => {
    getMock.mockResolvedValueOnce({ data: perfPayload(0) })
    render(<PerformancePage />)
    await waitFor(() => expect(screen.getByText(/No matured outcomes yet/i)).toBeInTheDocument())
  })
})
