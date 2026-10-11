import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [debugToken, setDebugToken] = useState<string | null>(null)

  async function handleForgot(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      const r = await api.post('/auth/forgot-password', { email })
      setMessage(r.data.message)
      setDebugToken(r.data.debug_reset_token ?? null)
    } catch (err) {
      setError((err as any)?.response?.data?.detail ?? 'Request failed')
    }
  }

  async function handleReset(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      const r = await api.post('/auth/reset-password', { token, new_password: password })
      setMessage(r.data.message)
    } catch (err) {
      setError((err as any)?.response?.data?.detail ?? 'Reset failed')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-sky-100 to-indigo-100 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <div className="mb-4 text-center text-3xl">🌧️</div>
        <h1 className="text-center text-xl font-bold text-slate-800">
          {token ? 'Reset Your Password' : 'Forgot Password'}
        </h1>

        {token ? (
          <form onSubmit={handleReset} className="mt-6 space-y-4">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="New password (min 8 characters)"
              required
              minLength={8}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-sky-500 focus:outline-none"
            />
            <button className="w-full rounded-lg bg-sky-600 py-2.5 font-medium text-white hover:bg-sky-700">
              Update Password
            </button>
          </form>
        ) : (
          <form onSubmit={handleForgot} className="mt-6 space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-sky-500 focus:outline-none"
            />
            <button className="w-full rounded-lg bg-sky-600 py-2.5 font-medium text-white hover:bg-sky-700">
              Send Reset Link
            </button>
          </form>
        )}

        {message && (
          <div className="mt-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
            {message}
            {debugToken && (
              <div className="mt-2 break-all text-xs text-slate-500">
                Dev reset token: {debugToken}
              </div>
            )}
          </div>
        )}
        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mt-6 text-center text-sm">
          <Link to="/login" className="text-sky-600 hover:underline">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  )
}
