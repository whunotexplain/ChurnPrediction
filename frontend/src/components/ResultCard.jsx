import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react'

export default function ResultCard({ result }) {
  if (!result) return null

  const riskConfig = {
    high: { icon: AlertTriangle, className: 'risk-high', label: 'Высокий риск оттока' },
    medium: { icon: AlertCircle, className: 'risk-medium', label: 'Средний риск оттока' },
    low: { icon: CheckCircle, className: 'risk-low', label: 'Низкий риск оттока' },
  }

  const config = riskConfig[result.churn_risk]
  const Icon = config.icon

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel p-6 mt-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Результат предсказания</h3>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${config.className}`}>
          {config.label}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-900/40 rounded-xl p-4 text-center">
          <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Вероятность оттока</p>
          <div className="relative w-32 h-32 mx-auto mt-2">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#1e293b" strokeWidth="8" />
              <circle 
                cx="50" cy="50" r="42" fill="none" 
                stroke={result.churn_risk === 'high' ? '#f43f5e' : result.churn_risk === 'medium' ? '#f59e0b' : '#10b981'} 
                strokeWidth="8" 
                strokeLinecap="round"
                strokeDasharray={`${result.probability * 264} 264`}
                className="transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl font-bold">{(result.probability * 100).toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/40 rounded-xl p-4 flex flex-col justify-center">
          <div className="flex items-center gap-3 mb-3">
            <Icon size={20} className={config.className.split(' ')[0]} />
            <span className="font-medium">Предсказание</span>
          </div>
          <p className="text-3xl font-bold mb-1">
            {result.prediction === 1 ? 'Churn' : 'No Churn'}
          </p>
          <p className="text-slate-400 text-sm">
            Порог модели: {(result.threshold_used * 100).toFixed(1)}%
          </p>
        </div>

        <div className="bg-slate-900/40 rounded-xl p-4 flex flex-col justify-center space-y-3">
          <div>
            <p className="text-slate-400 text-xs uppercase">Рекомендация</p>
            <p className="text-sm mt-1 leading-relaxed">
              {result.churn_risk === 'high' 
                ? 'Клиент с высокой вероятностью уйдёт. Рекомендуется персональная акция или звонок менеджера.'
                : result.churn_risk === 'medium'
                ? 'Умеренный риск. Можно предложить бонусную программу лояльности.'
                : 'Клиент лоялен. Стандартное обслуживание.'}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}