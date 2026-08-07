import { motion, AnimatePresence } from 'framer-motion'
import { Clock, Trash2 } from 'lucide-react'

export default function HistoryPanel({ history, onClear }) {
  return (
    <div className="glass-panel p-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Clock size={18} className="text-accent-400" />
          История предсказаний
        </h3>
        {history.length > 0 && (
          <button onClick={onClear} className="text-xs text-slate-400 hover:text-rose-400 flex items-center gap-1 transition-colors">
            <Trash2 size={14} /> Очистить
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <p className="text-slate-500 text-sm text-center py-8">История пуста. Сделайте первое предсказание.</p>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
          <AnimatePresence>
            {history.slice().reverse().map((item, i) => (
              <motion.div
                key={item.id || i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex items-center justify-between bg-slate-900/40 rounded-xl p-3 hover:bg-slate-900/60 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${item.prediction === 1 ? 'bg-rose-400' : 'bg-emerald-400'}`} />
                  <div>
                    <p className="text-sm font-medium">{item.customer_id || 'Аноним'}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(item.created_at).toLocaleString('ru-RU')}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold ${item.prediction === 1 ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {(item.probability * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-slate-500">{item.prediction === 1 ? 'Churn' : 'No Churn'}</p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}