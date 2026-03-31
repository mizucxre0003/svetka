'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { api } from '@/lib/api'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'

export default function AnalyticsPage() {
  const router = useRouter()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) { router.push('/login'); return }
    api.usageAnalytics().then(setData).catch(() => router.push('/login')).finally(() => setLoading(false))
  }, [router])

  if (loading) return <div className="layout"><Sidebar /><main className="main-content"><div className="loading">Загрузка...</div></main></div>
  if (!data || !data.total_chats) return <div className="layout"><Sidebar /><main className="main-content"><div className="empty-state"><div className="empty-icon">◈</div>Нет данных</div></main></div>

  const features = [
    { key: 'welcome_enabled', label: 'Приветствие', icon: '👋' },
    { key: 'anti_flood_enabled', label: 'Антифлуд', icon: '🛡️' },
    { key: 'anti_links_enabled', label: 'Антиссылки', icon: '🔗' },
    { key: 'stop_words_enabled', label: 'Стоп-слова', icon: '🚫' },
    { key: 'caps_filter_enabled', label: 'Капс-фильтр', icon: '🔠' },
    { key: 'triggers_enabled', label: 'Триггеры', icon: '⚡' },
    { key: 'rules_enabled', label: 'Правила', icon: '📋' },
  ]

  const radarData = features.map(f => ({ feature: f.label, value: data[f.key]?.pct || 0 }))

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Usage Analytics</h1>
          <p className="page-subtitle">Использование функций по всем группам · {data.total_chats} групп</p>
        </div>

        <div className="grid-2" style={{ marginBottom: 20 }}>
          {/* Таблица */}
          <div className="card">
            {features.map(f => {
              const d = data[f.key] || { count: 0, pct: 0 }
              return (
                <div key={f.key} style={{ marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13 }}>
                    <span>{f.icon} {f.label}</span>
                    <span style={{ fontWeight: 600 }}>{d.count} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({d.pct}%)</span></span>
                  </div>
                  <div className="funnel-bar-track">
                    <div className="funnel-bar-fill" style={{ width: `${d.pct}%` }} />
                  </div>
                </div>
              )
            })}
          </div>

          {/* Radar chart */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 15 }}>Радар активации функций</div>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.06)" />
                <PolarAngleAxis dataKey="feature" tick={{ fill: '#8b8fa8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#16181f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                <Radar dataKey="value" stroke="#6c63ff" fill="#6c63ff" fillOpacity={0.2} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="section-title">Итог по функциям</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
            {features.map(f => {
              const d = data[f.key] || { count: 0, pct: 0 }
              return (
                <div key={f.key} style={{ textAlign: 'center', padding: '16px 8px', background: 'var(--bg-base)', borderRadius: 10, border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: 24, marginBottom: 6 }}>{f.icon}</div>
                  <div style={{ fontWeight: 700, fontSize: 22 }}>{d.pct}%</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{f.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{d.count} групп</div>
                </div>
              )
            })}
          </div>
        </div>
      </main>
    </div>
  )
}
