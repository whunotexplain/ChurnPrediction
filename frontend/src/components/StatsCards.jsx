import { Activity, TrendingUp, Zap, Users } from 'lucide-react'

export default function StatsCards({ history }) {
  const total = history.length
  const churned = history.filter(h => h.prediction === 1).length
  const avgProb = total > 0 
    ? (history.reduce((a, b) => a + b.probability, 0) / total * 100).toFixed(1) 
    : 0

  const cards = [
    { label: 'Всего предсказаний', value: total, icon: Activity, color: 'text-violet-400' },
    { label: 'Churn обнаружено', value: churned, icon: TrendingUp, color: 'text-rose-400' },
    { label: 'Средняя вероятность', value: `${avgProb}%`, icon: Zap, color: 'text-amber-400' },
    { label: 'Модель', value: 'CatBoost', icon: Users, color: 'text-emerald-400' },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, i) => (
        <div key={i} className="glass-panel p-5 flex items-center gap-4">
          <div className={`p-3 rounded-xl bg-slate-800/50 ${card.color}`}>
            <card.icon size={22} />
          </div>
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">{card.label}</p>
            <p className="text-2xl font-bold text-white mt-0.5">{card.value}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
