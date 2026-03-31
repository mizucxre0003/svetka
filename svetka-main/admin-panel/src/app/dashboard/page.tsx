'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import { api } from '@/lib/api'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'

interface DashboardData {
  total_chats: number
  active_chats: number
  new_today: number
  new_week: number
  new_month: number
  dau: number
  wau: number
  mau: number
  free_count: number
  pro_count: number
  trial_count: number
  messages_7d: number
  moderation_actions_7d: number
  mini_app_opens_7d: number
  protection_triggers_7d: number
  growth_chart: { date: string; new_chats: number }[]
}

function StatCard({ title, value, sub, color = 'var(--text-primary)', badge }: {
  title: string; value: string | number; sub?: string; color?: string; badge?: React.ReactNode
}) {
  return (
    <div className="card stat-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div className="card-title">{title}</div>
        {badge}
      </div>
      <div className="card-value" style={{ color }}>{value}</div>
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  )
}

export default function DashboardPage() {
  const router = useRouter()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('admin_token')
    if (!token) { router.push('/login'); return }
    api.dashboard().then(setData).catch(() => router.push('/login')).finally(() => setLoading(false))
  }, [router])

  if (loading) return (
    <div className="layout">
      <Sidebar />
      <main className="main-content"><div className="loading">Загрузка данных...</div></main>
    </div>
  )
  if (!data) return null

  const chartData = data.growth_chart.map(d => ({
    date: d.date.slice(5),
    value: d.new_chats,
  }))

  return (
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Общая картина по всем подключённым группам</p>
        </div>

        {/* KPI */}
        <div className="grid-4" style={{ marginBottom: 20 }}>
          <StatCard title="Всего групп" value={data.total_chats} sub={`Активных: ${data.active_chats}`} />
          <StatCard title="Новых сегодня" value={data.new_today} sub={`За неделю: ${data.new_week}`} color="var(--green)" />
          <StatCard title="Новых за месяц" value={data.new_month} sub="rolling 30d" />
          <StatCard title="DAU / WAU / MAU"
            value={`${data.dau} / ${data.wau} / ${data.mau}`}
            sub="активных групп"
          />
        </div>

        {/* Тарифы + Activity */}
        <div className="grid-4" style={{ marginBottom: 20 }}>
          <StatCard title="Free" value={data.free_count} badge={<span className="badge badge-gray">Free</span>} />
          <StatCard title="Trial" value={data.trial_count} badge={<span className="badge badge-yellow">Trial</span>} />
          <StatCard title="Pro" value={data.pro_count} badge={<span className="badge badge-accent">Pro</span>} color="var(--accent)" />
          <StatCard title="Mini App открытий" value={data.mini_app_opens_7d.toLocaleString()} sub="за 7 дней" />
        </div>

        {/* Activity cards */}
        <div className="grid-4" style={{ marginBottom: 24 }}>
          <StatCard title="Сообщений (7д)" value={data.messages_7d.toLocaleString()} />
          <StatCard title="Мод. действий (7д)" value={data.moderation_actions_7d.toLocaleString()} color="var(--yellow)" />
          <StatCard title="Срабатываний защиты" value={data.protection_triggers_7d.toLocaleString()} color="var(--blue)" />
          <StatCard title="Открытий Mini App" value={data.mini_app_opens_7d.toLocaleString()} color="var(--accent)" />
        </div>

        {/* Growth Chart */}
        <div className="chart-container">
          <div className="chart-header">
            <div>
              <div style={{ fontWeight: 600, fontSize: 15 }}>Рост групп</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Новые подключения за 30 дней</div>
            </div>
            <span className="badge badge-accent">{data.new_month} за месяц</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorGrow" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6c63ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6c63ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fill: '#555870', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#555870', fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
              <Tooltip
                contentStyle={{ background: '#16181f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: '#8b8fa8' }}
                itemStyle={{ color: '#6c63ff' }}
              />
              <Area type="monotone" dataKey="value" stroke="#6c63ff" strokeWidth={2} fill="url(#colorGrow)" name="Новых групп" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </main>
    </div>
  )
}
