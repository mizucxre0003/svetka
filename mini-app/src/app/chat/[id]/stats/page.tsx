'use client'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { miniApi } from '@/lib/api'
import ChatNav from '@/components/ChatNav'

export default function StatsPage() {
  const params = useParams()
  const chatId = Number(params.id)
  const router = useRouter()
  const [data, setData] = useState<any>(null)
  const [days, setDays] = useState(7)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    miniApi.analytics(chatId, days).then(setData).catch(console.error).finally(() => setLoading(false))
  }, [chatId, days])

  if (loading) return <div className="page"><div className="spinner" /></div>

  const bars = data?.daily?.slice(-7) || []
  const maxVal = Math.max(...bars.map((d: any) => d.messages), 1)

  return (
    <div className="page">
      <div className="topbar">
        <button className="topbar-back" onClick={() => router.push(`/chat/${chatId}`)}>←</button>
        <div style={{ flex: 1 }}>
          <div className="topbar-title">Статистика</div>
          <div className="topbar-subtitle">Активность группы</div>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {[7, 14, 30].map(d => (
            <button key={d} onClick={() => setDays(d)}
              style={{
                padding: '5px 10px', borderRadius: 8, border: 'none', cursor: 'pointer',
                fontFamily: 'inherit', fontSize: 12, fontWeight: 500,
                background: days === d ? 'var(--accent)' : 'var(--glass-bg-light)',
                color: days === d ? '#fff' : 'var(--text-2)',
              }}>{d}д</button>
          ))}
        </div>
      </div>

      <div className="page-content fade-in">
        {/* KPI cards */}
        <div className="section">
          <div className="glass">
            <div className="stat-grid">
              {[
                ['💬', data?.messages ?? 0, 'Сообщений'],
                ['⚠️', data?.warnings ?? 0, 'Предупреждений'],
                ['🔇', data?.mutes ?? 0, 'Мутов'],
                ['🔨', data?.bans ?? 0, 'Банов'],
                ['🛡️', data?.protection_triggers ?? 0, 'Защита'],
                ['📱', data?.mini_app_opens ?? 0, 'Mini App'],
              ].map(([icon, val, lbl]) => (
                <div key={String(lbl)} className="stat-cell" style={{ padding: '16px' }}>
                  <div style={{ fontSize: 22 }}>{icon}</div>
                  <div className="stat-num">{String(val)}</div>
                  <div className="stat-lbl">{String(lbl)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bar chart */}
        {bars.length > 0 && (
          <div className="section">
            <div className="section-label">Сообщения по дням</div>
            <div className="glass" style={{ padding: '16px 16px 8px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 120 }}>
                {bars.map((d: any) => (
                  <div key={d.date} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, height: '100%', justifyContent: 'flex-end' }}>
                    <div style={{ fontSize: 10, color: 'var(--text-3)', fontWeight: 500 }}>{d.messages || 0}</div>
                    <div style={{
                      width: '100%', borderRadius: '4px 4px 0 0',
                      background: 'linear-gradient(180deg, var(--accent) 0%, rgba(124,140,255,0.4) 100%)',
                      height: `${Math.max((d.messages / maxVal) * 90, 4)}%`,
                      minHeight: 4,
                      transition: 'height 0.4s ease',
                    }} />
                    <div style={{ fontSize: 9, color: 'var(--text-3)' }}>{d.date?.slice(5)}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Top commands */}
        {data?.top_commands?.length > 0 && (
          <div className="section">
            <div className="section-label">Топ команд</div>
            <div className="glass">
              {data.top_commands.map((c: any, i: number) => (
                <div key={c.command} className="list-item">
                  <div style={{ width: 28, height: 28, borderRadius: 8, background: 'var(--accent-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, color: 'var(--accent)' }}>
                    {i + 1}
                  </div>
                  <div className="list-body">
                    <div className="list-title" style={{ fontFamily: 'monospace' }}>/{c.command}</div>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-2)' }}>{c.count}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      <ChatNav chatId={chatId} />
    </div>
  )
}


