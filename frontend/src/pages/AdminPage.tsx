import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Spinner from '../components/Spinner'
import { useAuth } from '../context/AuthContext'

interface IngestionStatus {
  provider: string
  last_success_at: string | null
  last_error_at: string | null
  last_error: string | null
  last_source: string | null
  records_last_run: number
}

interface JobRun {
  id: number
  job_name: string
  started_at: string
  finished_at: string | null
  status: string
  message: string | null
}

interface UserRow {
  id: number
  full_name: string
  email: string
  contact_number: string
  role: string
  status: string
  created_at: string
}

export default function AdminPage() {
  const { user } = useAuth()
  const [ingestion, setIngestion] = useState<IngestionStatus[]>([])
  const [jobs, setJobs] = useState<JobRun[]>([])
  const [users, setUsers] = useState<UserRow[]>([])
  const [counts, setCounts] = useState({ user_count: 0, prediction_count: 0 })
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)

  function load() {
    api.get('/admin/overview').then((r) => {
      setIngestion(r.data.ingestion)
      setJobs(r.data.recent_jobs)
      setCounts({ user_count: r.data.user_count, prediction_count: r.data.prediction_count })
    })
    api.get('/admin/users').then((r) => setUsers(r.data))
  }

  useEffect(load, [])

  async function trigger(path: string) {
    setBusy(true)
    setNotice(null)
    try {
      const r = await api.post(path)
      setNotice(`${path} → ${r.data.message}`)
    } catch (err) {
      setNotice((err as any)?.response?.data?.detail ?? 'Trigger failed')
    } finally {
      setBusy(false)
      load()
    }
  }

  if (user?.role !== 'admin') {
    return <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">Admin access required.</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-800">Admin Panel</h1>
        <div className="flex gap-2">
          <button
            disabled={busy}
            onClick={() => trigger('/admin/ingest')}
            className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
          >
            Run Ingest + Predict
          </button>
          <button
            disabled={busy}
            onClick={() => trigger('/admin/evaluate')}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            Run Evaluation
          </button>
        </div>
      </div>

      {notice && <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm">{notice}</div>}

      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs text-slate-500">Registered Users</div>
          <div className="text-2xl font-bold text-slate-800">{counts.user_count}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-xs text-slate-500">Predictions Stored</div>
          <div className="text-2xl font-bold text-slate-800">{counts.prediction_count}</div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-800">Ingestion Status</h3>
        {ingestion.length === 0 ? (
          <p className="text-sm text-slate-500">No ingestion recorded yet.</p>
        ) : (
          <div className="space-y-2">
            {ingestion.map((s) => (
              <div key={s.provider} className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 text-sm">
                <div>
                  <div className="font-medium">{s.provider}</div>
                  <div className="text-xs text-slate-500">
                    source: {s.last_source ?? '—'} · {s.records_last_run} records
                  </div>
                </div>
                <div className="text-right text-xs">
                  <div className={s.last_error_at ? 'text-red-600' : 'text-green-600'}>
                    {s.last_error_at ? 'Degraded' : 'OK'}
                  </div>
                  <div className="text-slate-500">
                    {s.last_success_at ? new Date(s.last_success_at).toLocaleString() : '—'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-800">Recent Job Runs</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Job</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Started</th>
                <th className="px-3 py-2">Finished</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{j.job_name}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        j.status === 'success'
                          ? 'bg-green-100 text-green-700'
                          : j.status === 'failed'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-amber-100 text-amber-700'
                      }`}
                    >
                      {j.status}
                    </span>
                  </td>
                  <td className="px-3 py-2">{new Date(j.started_at).toLocaleString()}</td>
                  <td className="px-3 py-2">
                    {j.finished_at ? new Date(j.finished_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-4 text-center text-slate-500">
                    No job runs yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 font-semibold text-slate-800">Users</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Name</th>
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Role</th>
                <th className="px-3 py-2">Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{u.id}</td>
                  <td className="px-3 py-2">{u.full_name}</td>
                  <td className="px-3 py-2">{u.email}</td>
                  <td className="px-3 py-2">{u.role}</td>
                  <td className="px-3 py-2">{new Date(u.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {busy && <Spinner label="Running job…" />}
    </div>
  )
}
