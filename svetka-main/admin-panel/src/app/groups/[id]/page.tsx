'use client'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { api } from '@/lib/api'

export default function GroupCardPage() {
  const router = useRouter()
  const params = useParams()
  const id = Number(params.id)
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [note, setNote] = useState('')
  const [noteLoading, setNoteLoading] = useState(false)
  const [tariffPlan, setTariffPlan] = useState('')
  const [tariffDays, setTariffDays] = useState('')
  const [tariffMsg, setTariffMsg] = useState('')

  async function load() {
    try {
      const d = await api.group(id)
      setData(d)
      setTariffPlan(d.chat.tariff)
    } catch { router.push('/login') }
    setLoading(false)
  }

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) { router.push('/login'); return }
    load()
  }, [id])

  async function handleNote(e: React.FormEvent) {
    e.preventDefault()
    if (!note.trim()) return
    setNoteLoading(true)
    await api.addNote(id, note)
    setNote('')
    await load()
    setNoteLoading(false)
  }

  async function handleTariff() {
    await api.updateTariff(id, tariffPlan, tariffDays ? Number(tariffDays) : undefined)
    setTariffMsg('Тариф обновлён ✓')
    await load()
    setTimeout(() => setTariffMsg(''), 3000)
  }

  async function handleBlock() {
    if (!confirm('Заблокировать группу?')) return
    await api.blockGroup(id)
    await load()
  }

  async function handleUnblock() {
    await api.unblockGroup(id)
    await load()
  }

  if (loading) return <div className="layout"><Sidebar /><main className="main-content"><div className="loading">Загрузка...</div></main></div>
  if (!data) return null

  const { chat, metrics_30d, recent_logs, notes } = data
  const TARIFF_BADGE: Record<string, string> = { free: 'badge-gray', trial: 'badge-yellow', pro: 'badge-accent' }
  const STATUS_BADGE: Record<string, string> = { active: 'badge-green', inactive: 'badge-yellow', blocked: 'badge-red' }

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <button className="btn btn-secondary btn-sm" onClick={() => router.push('/groups')}>← Назад</button>
              <h1 className="page-title" style={{ margin: 0 }}>{chat.title}</h1>
              <span className={`badge ${STATUS_BADGE[chat.status]}`}>{chat.status}</span>
              <span className={`badge ${TARIFF_BADGE[chat.tariff]}`}>{chat.tariff}</span>
            </div>
            <p className="page-subtitle">ID: {chat.telegram_chat_id} {chat.username ? `· @${chat.username}` : ''}</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {chat.status !== 'blocked'
              ? <button className="btn btn-danger btn-sm" onClick={handleBlock}>⊗ Заблокировать</button>
              : <button className="btn btn-secondary btn-sm" onClick={handleUnblock}>✓ Разблокировать</button>
            }
          </div>
        </div>

        {/* Metrics */}
        <div className="grid-4" style={{ marginBottom: 20 }}>
          {[
            ['Сообщений (30д)', metrics_30d.messages.toLocaleString(), ''],
            ['Банов', metrics_30d.bans, 'var(--red)'],
            ['Мутов', metrics_30d.mutes, 'var(--yellow)'],
            ['Предупреждений', metrics_30d.warnings, 'var(--blue)'],
          ].map(([title, val, color]) => (
            <div className="card stat-card" key={String(title)}>
              <div className="card-title">{title}</div>
              <div className="card-value" style={{ color: String(color) || 'inherit' }}>{val}</div>
            </div>
          ))}
        </div>

        <div className="grid-2" style={{ marginBottom: 20 }}>
          {/* Тариф */}
          <div className="card">
            <div className="section-title">Управление тарифом</div>
            <div className="form-group">
              <label className="form-label">Тариф</label>
              <select className="select" value={tariffPlan} onChange={e => setTariffPlan(e.target.value)}>
                <option value="free">Free</option>
                <option value="trial">Trial</option>
                <option value="pro">Pro</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Срок (дней, пусто = навсегда)</label>
              <input className="input" type="number" placeholder="30" value={tariffDays} onChange={e => setTariffDays(e.target.value)} />
            </div>
            <button className="btn btn-primary" onClick={handleTariff}>Сохранить тариф</button>
            {tariffMsg && <div style={{ marginTop: 8, color: 'var(--green)', fontSize: 12 }}>{tariffMsg}</div>}
          </div>

          {/* Инфо */}
          <div className="card">
            <div className="section-title">Информация</div>
            {[
              ['Участников', chat.member_count?.toLocaleString()],
              ['Подключено', new Date(chat.connected_at).toLocaleDateString('ru-RU')],
              ['Последняя активность', chat.last_activity_at ? new Date(chat.last_activity_at).toLocaleDateString('ru-RU') : '—'],
              ['Mini App открытий (30д)', metrics_30d.mini_app_opens.toLocaleString()],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
                <span style={{ fontWeight: 500 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid-2">
          {/* Логи */}
          <div className="card">
            <div className="section-title">Последние события</div>
            {recent_logs.length === 0
              ? <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Событий нет</div>
              : recent_logs.slice(0, 10).map((l: any, i: number) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--border)', fontSize: 12 }}>
                  <span style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>{l.action_type}</span>
                  <span style={{ color: 'var(--text-muted)' }}>{new Date(l.created_at).toLocaleDateString('ru-RU')}</span>
                </div>
              ))
            }
          </div>

          {/* Заметки */}
          <div className="card">
            <div className="section-title">Заметки команды</div>
            <form onSubmit={handleNote} style={{ marginBottom: 14 }}>
              <textarea
                className="input"
                rows={3}
                placeholder="Добавить заметку..."
                value={note}
                onChange={e => setNote(e.target.value)}
                style={{ resize: 'none', marginBottom: 8 }}
              />
              <button className="btn btn-secondary btn-sm" type="submit" disabled={noteLoading}>
                {noteLoading ? 'Сохранение...' : '+ Добавить'}
              </button>
            </form>
            {notes.length === 0
              ? <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Заметок нет</div>
              : notes.map((n: any) => (
                <div key={n.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                  <div style={{ marginBottom: 4 }}>{n.text}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {n.created_by} · {new Date(n.created_at).toLocaleDateString('ru-RU')}
                  </div>
                </div>
              ))
            }
          </div>
        </div>
      </main>
    </div>
  )
}
