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

export default function ProtectionPage() {
  const params = useParams()
  const chatId = Number(params.id)
  const router = useRouter()
  const [s, setS] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [newWord, setNewWord] = useState('')

  useEffect(() => {
    miniApi.settings(chatId).then(setS).catch(console.error).finally(() => setLoading(false))
  }, [chatId])

  async function patch(data: Record<string, unknown>) {
    setSaving(true)
    const updated = await miniApi.updateSettings(chatId, data)
    setS(updated)
    setSaving(false)
  }

  async function addStopWord() {
    if (!newWord.trim()) return
    const list = [...(s?.stop_words_list || []), newWord.trim()]
    await patch({ stop_words_list: list })
    setNewWord('')
  }

  async function removeStopWord(word: string) {
    const list = (s?.stop_words_list || []).filter((w: string) => w !== word)
    await patch({ stop_words_list: list })
  }

  if (loading) return <div className="page"><div className="spinner" /></div>

  const MODULES = [
    {
      key: 'anti_flood_enabled', title: 'Антифлуд', icon: '🌊',
      desc: `Лимит: ${s?.anti_flood_limit ?? 5} сообщ. за ${s?.anti_flood_interval ?? 5} сек.`,
      extra: (
        <div className="setting-row" style={{ paddingTop: 0 }}>
          <div className="setting-info">
            <div className="setting-title" style={{ fontSize: 13, color: 'var(--text-2)' }}>Действие</div>
          </div>
          <select className="field" style={{ width: 'auto', padding: '6px 10px' }}
            value={s?.anti_flood_action || 'mute'}
            onChange={e => patch({ anti_flood_action: e.target.value })}>
            <option value="mute">Мут</option>
            <option value="delete">Удалить</option>
            <option value="ban">Бан</option>
          </select>
        </div>
      )
    },
    {
      key: 'anti_links_enabled', title: 'Антиссылки', icon: '🔗',
      desc: 'Удаляет URL и ссылки на внешние ресурсы',
      extra: (
        <div className="setting-row" style={{ paddingTop: 0 }}>
          <div className="setting-info"><div className="setting-title" style={{ fontSize: 13, color: 'var(--text-2)' }}>Действие</div></div>
          <select className="field" style={{ width: 'auto', padding: '6px 10px' }}
            value={s?.anti_links_action || 'delete'}
            onChange={e => patch({ anti_links_action: e.target.value })}>
            <option value="delete">Удалить</option>
            <option value="warn">Предупреждение</option>
            <option value="mute">Мут</option>
          </select>
        </div>
      )
    },
    { key: 'repeat_filter_enabled', title: 'Фильтр повторов', icon: '♻️', desc: 'Удаляет дублирующиеся сообщения' },
    {
      key: 'caps_filter_enabled', title: 'Капс-фильтр', icon: '🔠',
      desc: `Порог ${Math.round((s?.caps_filter_threshold || 0.7) * 100)}% заглавных букв`,
    },
  ]

  return (
    <div className="page">
      <div className="topbar">
        <button className="topbar-back" onClick={() => router.push(`/chat/${chatId}`)}>←</button>
        <div>
          <div className="topbar-title">Защита</div>
          <div className="topbar-subtitle">{saving ? 'Сохранение...' : 'Антиспам-модули'}</div>
        </div>
      </div>

      <div className="page-content fade-in">
        {MODULES.map(m => (
          <div className="section" key={m.key}>
            <div className="glass">
              <div className="setting-row">
                <div className="list-icon" style={{ marginRight: 12, fontSize: 20 }}>{m.icon}</div>
                <div className="setting-info">
                  <div className="setting-title">{m.title}</div>
                  <div className="setting-desc">{m.desc}</div>
                </div>
                <Toggle checked={!!s?.[m.key]} onChange={v => patch({ [m.key]: v })} />
              </div>
              {s?.[m.key] && m.extra}
            </div>
          </div>
        ))}

        {/* Stop words */}
        <div className="section">
          <div className="section-label">Стоп-слова</div>
          <div className="glass">
            <div className="setting-row">
              <div className="setting-info">
                <div className="setting-title">Включить фильтр</div>
                <div className="setting-desc">{(s?.stop_words_list?.length || 0)} слов в списке</div>
              </div>
              <Toggle checked={!!s?.stop_words_enabled} onChange={v => patch({ stop_words_enabled: v })} />
            </div>

            {s?.stop_words_enabled && (
              <div style={{ padding: '0 16px 16px' }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                  <input
                    className="field" style={{ flex: 1 }}
                    placeholder="Добавить слово..."
                    value={newWord}
                    onChange={e => setNewWord(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addStopWord()}
                  />
                  <button className="btn btn-ghost btn-sm" onClick={addStopWord}>+</button>
                </div>
                <div className="chips">
                  {(s?.stop_words_list || []).map((w: string) => (
                    <span key={w} className="chip">
                      {w}
                      <span className="chip-del" onClick={() => removeStopWord(w)}>×</span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <ChatNav chatId={chatId} />
    </div>
  )
}


