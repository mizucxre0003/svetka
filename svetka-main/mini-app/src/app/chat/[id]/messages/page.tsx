'use client'
import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { miniApi } from '@/lib/api'
import ChatNav from '@/components/ChatNav'

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="toggle" onClick={() => onChange(!checked)}>
      <input type="checkbox" checked={checked} onChange={() => {}} />
      <div className="toggle-track" />
      <div className="toggle-thumb" />
    </label>
  )
}

export default function MessagesPage() {
  const params = useParams()
  const chatId = Number(params.id)
  const router = useRouter()
  const [s, setS] = useState<any>(null)
  const [triggers, setTriggers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [tab, setTab] = useState<'welcome' | 'rules' | 'triggers'>('welcome')
  const [newTrigger, setNewTrigger] = useState({ trigger_text: '', response_text: '', match_type: 'contains' })
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    Promise.all([miniApi.settings(chatId), miniApi.triggers(chatId)])
      .then(([st, tr]) => { setS(st); setTriggers(Array.isArray(tr) ? tr : []) })
      .catch(console.error).finally(() => setLoading(false))
  }, [chatId])

  async function patchSettings(data: Record<string, unknown>) {
    setSaving(true)
    const updated = await miniApi.updateSettings(chatId, data)
    setS(updated)
    setSaving(false)
  }

  async function createTrigger() {
    if (!newTrigger.trigger_text.trim() || !newTrigger.response_text.trim()) return
    setAdding(true)
    const t = await miniApi.createTrigger(chatId, newTrigger)
    setTriggers(prev => [...prev, t])
    setNewTrigger({ trigger_text: '', response_text: '', match_type: 'contains' })
    setAdding(false)
  }

  async function toggleTrigger(id: number, enabled: boolean) {
    await miniApi.updateTrigger(id, { is_enabled: enabled })
    setTriggers(prev => prev.map(t => t.id === id ? { ...t, is_enabled: enabled } : t))
  }

  async function deleteTrigger(id: number) {
    await miniApi.deleteTrigger(id)
    setTriggers(prev => prev.filter(t => t.id !== id))
  }

  if (loading) return <div className="page"><div className="spinner" /></div>

  return (
    <div className="page">
      <div className="topbar">
        <button className="topbar-back" onClick={() => router.push(`/chat/${chatId}`)}>←</button>
        <div>
          <div className="topbar-title">Контент</div>
          <div className="topbar-subtitle">{saving ? 'Сохранение...' : 'Привет · Правила · Триггеры'}</div>
        </div>
      </div>

      <div style={{ padding: '12px 16px 0', display: 'flex', gap: 6 }}>
        {(['welcome', 'rules', 'triggers'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: '7px 14px', borderRadius: 20, border: 'none', cursor: 'pointer', fontSize: 13,
              fontFamily: 'inherit', fontWeight: 500,
              background: tab === t ? 'var(--accent)' : 'var(--glass-bg-light)',
              color: tab === t ? '#fff' : 'var(--text-2)', transition: 'all 0.15s'
            }}>
            {t === 'welcome' ? '👋' : t === 'rules' ? '📋' : '⚡'} {t === 'welcome' ? 'Привет' : t === 'rules' ? 'Правила' : 'Триггеры'}
          </button>
        ))}
      </div>

      <div className="page-content fade-in">
        {tab === 'welcome' && (
          <div className="section">
            <div className="glass">
              <div className="setting-row">
                <div className="setting-info">
                  <div className="setting-title">Приветствие включено</div>
                  <div className="setting-desc">Отправляется при вступлении</div>
                </div>
                <Toggle checked={!!s?.welcome_enabled} onChange={v => patchSettings({ welcome_enabled: v })} />
              </div>
            </div>
            {s?.welcome_enabled && (
              <div style={{ marginTop: 12 }}>
                <div className="field-wrap">
                  <label className="field-label">Текст приветствия</label>
                  <textarea className="field" rows={5}
                    placeholder="Добро пожаловать, {name}!"
                    defaultValue={s?.welcome_text || ''}
                    onBlur={e => patchSettings({ welcome_text: e.target.value })} />
                </div>
                <div className="field-wrap">
                  <label className="field-label">Автоудаление (сек, 0 = не удалять)</label>
                  <input className="field" type="number" min="0"
                    defaultValue={s?.welcome_delete_after || 0}
                    onBlur={e => patchSettings({ welcome_delete_after: Number(e.target.value) || null })} />
                </div>
              </div>
            )}
          </div>
        )}

        {tab === 'rules' && (
          <div className="section">
            <div className="glass">
              <div className="setting-row">
                <div className="setting-info">
                  <div className="setting-title">Правила группы</div>
                  <div className="setting-desc">Команда /rules покажет текст</div>
                </div>
                <Toggle checked={!!s?.rules_enabled} onChange={v => patchSettings({ rules_enabled: v })} />
              </div>
            </div>
            {s?.rules_enabled && (
              <div style={{ marginTop: 12 }}>
                <div className="field-wrap">
                  <label className="field-label">Текст правил</label>
                  <textarea className="field" rows={8}
                    placeholder={'1. Уважайте друг друга\n2. Не спамить\n3. ...'}
                    defaultValue={s?.rules_text || ''}
                    onBlur={e => patchSettings({ rules_text: e.target.value })} />
                </div>
                <button className="btn btn-primary btn-full" onClick={() => patchSettings({ rules_text: s?.rules_text })}>
                  Сохранить правила
                </button>
              </div>
            )}
          </div>
        )}

        {tab === 'triggers' && (
          <>
            <div className="section">
              <div className="glass">
                <div className="setting-row">
                  <div className="setting-info">
                    <div className="setting-title">Автоответы включены</div>
                    <div className="setting-desc">{triggers.length} / 50 триггеров</div>
                  </div>
                  <Toggle checked={!!s?.triggers_enabled} onChange={v => patchSettings({ triggers_enabled: v })} />
                </div>
              </div>
            </div>

            <div className="section">
              <div className="section-label">Добавить триггер</div>
              <div className="glass" style={{ padding: 16 }}>
                <div className="field-wrap">
                  <label className="field-label">Слово / фраза</label>
                  <input className="field" placeholder="оплата"
                    value={newTrigger.trigger_text}
                    onChange={e => setNewTrigger(p => ({ ...p, trigger_text: e.target.value }))} />
                </div>
                <div className="field-wrap">
                  <label className="field-label">Ответ бота</label>
                  <textarea className="field" rows={3} placeholder="Оплатить можно через Kaspi..."
                    value={newTrigger.response_text}
                    onChange={e => setNewTrigger(p => ({ ...p, response_text: e.target.value }))} />
                </div>
                <div className="field-wrap">
                  <label className="field-label">Тип совпадения</label>
                  <select className="field" value={newTrigger.match_type}
                    onChange={e => setNewTrigger(p => ({ ...p, match_type: e.target.value }))}>
                    <option value="contains">Содержит</option>
                    <option value="exact">Точное</option>
                    <option value="startswith">Начинается с</option>
                  </select>
                </div>
                <button className="btn btn-primary btn-full" onClick={createTrigger} disabled={adding}>
                  {adding ? 'Добавление...' : '+ Добавить'}
                </button>
              </div>
            </div>

            <div className="section">
              <div className="section-label">Триггеры</div>
              {triggers.length === 0
                ? <div className="empty"><div className="empty-icon">⚡</div>Нет триггеров</div>
                : (
                  <div className="glass">
                    {triggers.map(t => (
                      <div key={t.id} className="list-item" style={{ alignItems: 'flex-start' }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2, display: 'flex', alignItems: 'center', gap: 6 }}>
                            {t.trigger_text}
                            <span className="badge badge-grey" style={{ fontSize: 10 }}>{t.match_type}</span>
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--text-2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {t.response_text}
                          </div>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginLeft: 10, alignItems: 'flex-end' }}>
                          <Toggle checked={t.is_enabled} onChange={v => toggleTrigger(t.id, v)} />
                          <button onClick={() => deleteTrigger(t.id)}
                            style={{ fontSize: 11, padding: '3px 8px', borderRadius: 6, border: 'none', cursor: 'pointer', background: 'var(--red-dim)', color: 'var(--red)' }}>
                            Удалить
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
            </div>
          </>
        )}
      </div>
      <ChatNav chatId={chatId} />
    </div>
  )
}


