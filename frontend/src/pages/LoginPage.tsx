import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function PasswordInput({
  value,
  onChange,
  placeholder,
  show,
  onToggle,
}: {
  value: string
  onChange: (v: string) => void
  placeholder: string
  show: boolean
  onToggle: () => void
}) {
  return (
    <div className="relative">
      <input
        type={show ? 'text' : 'password'}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
      />
      <button
        type="button"
        onClick={onToggle}
        className="absolute inset-y-0 right-0 flex items-center pr-3 text-sm text-slate-500"
        aria-label="Toggle password visibility"
      >
        {show ? '🙈' : '👁️'}
      </button>
    </div>
  )
}

export default function LoginPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(false)
  const [showPass, setShowPass] = useState(false)

  const [rName, setRName] = useState('')
  const [rEmail, setREmail] = useState('')
  const [rContact, setRContact] = useState('')
  const [rPassword, setRPassword] = useState('')
  const [rConfirm, setRConfirm] = useState('')
  const [rShow, setRShow] = useState(false)

  async function handleLogin(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await login(email, password, remember)
      navigate('/')
    } catch (err) {
      setError((err as any)?.response?.data?.detail ?? 'Login failed. Please try again.')
    }
  }

  async function handleRegister(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (rPassword !== rConfirm) {
      setError('Passwords do not match.')
      return
    }
    if (!/^\d{10}$/.test(rContact)) {
      setError('Contact number must be exactly 10 digits.')
      return
    }
    try {
      await register({
        full_name: rName,
        email: rEmail,
        contact_number: rContact,
        password: rPassword,
        confirm_password: rConfirm,
      })
      navigate('/')
    } catch (err) {
      setError((err as any)?.response?.data?.detail ?? 'Registration failed. Please try again.')
    }
  }

  const input =
    'w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500'

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-100 via-blue-100 to-indigo-100">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-4 py-10">
        <div className="mb-6 text-center">
          <div className="text-4xl">🌧️</div>
          <h1 className="mt-2 text-3xl font-bold text-navy-900">RainMumbai AI</h1>
          <p className="text-sm text-slate-600">
            Predictive modeling of the RainMumbai Index using meteorological data
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          {/* Welcome Back */}
          <div className="rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="text-xl font-bold text-slate-800">Welcome Back</h2>
            <p className="mt-1 text-sm text-slate-500">Sign in to continue to your dashboard.</p>
            <form onSubmit={handleLogin} className="mt-5 space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-600">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className={`${input} mt-1`}
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600">Password</label>
                <PasswordInput
                  value={password}
                  onChange={setPassword}
                  placeholder="••••••••"
                  show={showPass}
                  onToggle={() => setShowPass((s) => !s)}
                />
              </div>
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={remember}
                    onChange={(e) => setRemember(e.target.checked)}
                  />
                  Remember Me
                </label>
                <Link to="/reset-password" className="text-sm text-sky-600 hover:underline">
                  Forgot Password?
                </Link>
              </div>
              <button
                type="submit"
                className="w-full rounded-lg bg-sky-600 py-2.5 font-medium text-white hover:bg-sky-700"
              >
                Login
              </button>
            </form>
          </div>

          {/* Create Your Account */}
          <div className="rounded-2xl bg-white p-6 shadow-xl">
            <h2 className="text-xl font-bold text-slate-800">Create Your Account</h2>
            <p className="mt-1 text-sm text-slate-500">Free access to all predictions and analytics.</p>
            <form onSubmit={handleRegister} className="mt-5 space-y-4">
              <input
                value={rName}
                onChange={(e) => setRName(e.target.value)}
                placeholder="Full Name"
                required
                className={input}
              />
              <input
                type="email"
                value={rEmail}
                onChange={(e) => setREmail(e.target.value)}
                placeholder="Email Address"
                required
                className={input}
              />
              <input
                value={rContact}
                onChange={(e) => setRContact(e.target.value)}
                placeholder="Contact Number (10 digits)"
                required
                maxLength={10}
                className={input}
              />
              <PasswordInput
                value={rPassword}
                onChange={setRPassword}
                placeholder="Password"
                show={rShow}
                onToggle={() => setRShow((s) => !s)}
              />
              <input
                type="password"
                value={rConfirm}
                onChange={(e) => setRConfirm(e.target.value)}
                placeholder="Confirm Password"
                required
                className={input}
              />
              <button
                type="submit"
                className="w-full rounded-lg bg-green-600 py-2.5 font-medium text-white hover:bg-green-700"
              >
                Create Account
              </button>
            </form>
          </div>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-600">
          <span className="flex items-center gap-1.5">🔒 Secure Access</span>
          <span className="flex items-center gap-1.5">🛡️ Privacy First</span>
          <span className="flex items-center gap-1.5">✅ Trusted Platform</span>
        </div>
      </div>
    </div>
  )
}
