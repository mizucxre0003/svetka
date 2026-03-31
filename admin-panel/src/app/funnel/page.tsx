'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { api } from '@/lib/api'

export default function FunnelPage() {
  const router = useRouter()
  const [steps, setSteps] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) { router.push('/login'); return }
    api.funnel().then(setSteps).catch(() => router.push('/login')).finally(() => setLoading(false))
  }, [router])

  if (loading) return <div className="layout"><Sidebar /><main className="main-content"><div className="loading">Загрузка...</div></main></div>

  const max = steps[0]?.count || 1

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Funnel активации</h1>
          <p className="page-subtitle">Путь группы от подключения до полной настройки</p>
        </div>

        <div className="card">
          {steps.map((step, i) => {
            const drop = i > 0 ? ((steps[i - 1].count - step.count) / (steps[i - 1].count || 1) * 100).toFixed(0) : null
            return (
              <div key={step.step} style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 8 }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: i === 0 ? 'var(--accent-dim)' : 'var(--bg-base)',
                    border: `1px solid ${i === 0 ? 'var(--accent)' : 'var(--border)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 12, fontWeight: 700,
                    color: i === 0 ? 'var(--accent)' : 'var(--text-muted)',
                    flexShrink: 0,
                  }}>{step.step}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                      <span style={{ fontWeight: 500 }}>{step.label}</span>
                      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                        {drop && Number(drop) > 0 && (
                          <span style={{ fontSize: 11, color: 'var(--red)' }}>▼ -{drop}%</span>
                        )}
                        <span style={{ fontWeight: 700 }}>{step.count}</span>
                        <span style={{ fontSize: 12, color: 'var(--text-muted)', minWidth: 44, textAlign: 'right' }}>{step.pct}%</span>
                      </div>
                    </div>
                    <div className="funnel-bar-track">
                      <div className="funnel-bar-fill" style={{ width: `${step.pct}%`, opacity: 1 - i * 0.08 }} />
                    </div>
                  </div>
                </div>
                {i < steps.length - 1 && (
                  <div style={{ marginLeft: 48, height: 16, width: 2, background: 'var(--border)' }} />
                )}
              </div>
            )
          })}
        </div>
      </main>
    </div>
  )
}
