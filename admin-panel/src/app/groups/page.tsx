'use client'
import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Sidebar from '@/components/Sidebar'
import { api } from '@/lib/api'

interface Group {
  id: number; telegram_chat_id: number; title: string
  username: string | null; connected_at: string; last_activity_at: string | null
  member_count: number; tariff: string; status: string
}

const TARIFF_BADGE: Record<string, string> = { free: 'badge-gray', trial: 'badge-yellow', pro: 'badge-accent' }
const STATUS_BADGE: Record<string, string> = { active: 'badge-green', inactive: 'badge-yellow', blocked: 'badge-red' }

function fmtDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

export default function GroupsPage() {
  const router = useRouter()
  const [groups, setGroups] = useState<Group[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [tariff, setTariff] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(0)
  const limit = 25

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = { limit: String(limit), offset: String(page * limit) }
      if (search) params.search = search
      if (tariff) params.tariff = tariff
      if (status) params.status = status
      const data = await api.groups(params)
      setGroups(data.items)
      setTotal(data.total)
    } catch { router.push('/login') }
    setLoading(false)
  }, [search, tariff, status, page, router])

  useEffect(() => {
    if (!localStorage.getItem('admin_token')) { router.push('/login'); return }
    load()
  }, [load, router])

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Группы</h1>
          <p className="page-subtitle">Все подключённые Telegram-группы · {total} всего</p>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
          <input className="input" style={{ maxWidth: 260 }} placeholder="Поиск по названию..." value={search} onChange={e => { setSearch(e.target.value); setPage(0) }} />
          <select className="select" style={{ maxWidth: 130 }} value={tariff} onChange={e => { setTariff(e.target.value); setPage(0) }}>
            <option value="">Все тарифы</option>
            <option value="free">Free</option>
            <option value="trial">Trial</option>
            <option value="pro">Pro</option>
          </select>
          <select className="select" style={{ maxWidth: 130 }} value={status} onChange={e => { setStatus(e.target.value); setPage(0) }}>
            <option value="">Все статусы</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="blocked">Blocked</option>
          </select>
          <button className="btn btn-secondary btn-sm" onClick={load}>↻ Обновить</button>
        </div>

        <div className="card" style={{ padding: 0 }}>
          <div className="table-wrap">
            {loading ? (
              <div className="loading">Загрузка...</div>
            ) : groups.length === 0 ? (
              <div className="empty-state"><div className="empty-icon">◎</div>Группы не найдены</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Название</th>
                    <th>Username</th>
                    <th>Участников</th>
                    <th>Тариф</th>
                    <th>Статус</th>
                    <th>Подключено</th>
                    <th>Активность</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {groups.map(g => (
                    <tr key={g.id}>
                      <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{g.id}</td>
                      <td style={{ fontWeight: 500, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{g.title}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{g.username ? `@${g.username}` : '—'}</td>
                      <td>{g.member_count.toLocaleString()}</td>
                      <td><span className={`badge ${TARIFF_BADGE[g.tariff] || 'badge-gray'}`}>{g.tariff}</span></td>
                      <td><span className={`badge ${STATUS_BADGE[g.status] || 'badge-gray'}`}>{g.status}</span></td>
                      <td style={{ color: 'var(--text-secondary)' }}>{fmtDate(g.connected_at)}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{fmtDate(g.last_activity_at)}</td>
                      <td>
                        <Link href={`/groups/${g.id}`} className="btn btn-secondary btn-sm">Открыть →</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Pagination */}
        {total > limit && (
          <div style={{ display: 'flex', gap: 8, marginTop: 16, alignItems: 'center' }}>
            <button className="btn btn-secondary btn-sm" disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Назад</button>
            <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              {page * limit + 1}–{Math.min((page + 1) * limit, total)} из {total}
            </span>
            <button className="btn btn-secondary btn-sm" disabled={(page + 1) * limit >= total} onClick={() => setPage(p => p + 1)}>Вперёд →</button>
          </div>
        )}
      </main>
    </div>
  )
}
