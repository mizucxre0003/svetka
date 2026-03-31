'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/admin/dashboard`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (res.ok) {
        localStorage.setItem('admin_token', token)
        router.push('/dashboard')
      } else {
        setError('Неверный токен доступа')
      }
    } catch {
      setError('Ошибка подключения к серверу')
    }
    setLoading(false)
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 24 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: 'linear-gradient(135deg, #6c63ff, #a78bfa)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 20
          }}>✦</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>Svetka</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Super Admin Panel</div>
          </div>
        </div>
        <h1>Вход</h1>
        <p>Введите токен администратора для доступа к панели управления.</p>
        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label">Admin Token</label>
            <input
              className="input"
              type="password"
              placeholder="••••••••••••••••"
              value={token}
              onChange={e => setToken(e.target.value)}
              required
              autoFocus
            />
          </div>
          {error && (
            <div style={{ color: 'var(--red)', fontSize: 12, marginBottom: 14, padding: '8px 12px', background: 'var(--red-dim)', borderRadius: 6 }}>
              {error}
            </div>
          )}
          <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} type="submit" disabled={loading}>
            {loading ? 'Проверка...' : 'Войти →'}
          </button>
        </form>
      </div>
    </div>
  )
}
