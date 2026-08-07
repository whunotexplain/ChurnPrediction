import { useState, useEffect } from 'react'
import { Activity, Github, Server } from 'lucide-react'
import PredictionForm from './components/PredictionForm'
import ResultCard from './components/ResultCard'
import HistoryPanel from './components/HistoryPanel'
import StatsCards from './components/StatsCards'
import { getHealth, getHistory } from './api/client'

export default function App() {
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ status: 'error' }))
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      const data = await getHistory(100)
      setHistory(data)
    } catch (e) {
      console.error(e)
    }
  }

  const handleResult = (res) => {
    setResult(res)
    loadHistory()
  }

  const isConnected = health?.status === 'ok'

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-accent-500/20 rounded-xl border border-accent-500/30">
            <Activity size={24} className="text-accent-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Churn Prediction</h1>
            <p className="text-slate-400 text-sm">ML Dashboard — CatBoost + FastAPI</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border ${
            isConnected ? 'bg-emerald-400/10 border-emerald-400/20 text-emerald-400' : 'bg-rose-400/10 border-rose-400/20 text-rose-400'
          }`}>
            <Server size={14} />
            {isConnected ? 'API Online' : 'API Offline'}
          </div>
          <a href="https://github.com" target="_blank" rel="noreferrer" 
             className="p-2 hover:bg-slate-800/50 rounded-xl transition-colors text-slate-400 hover:text-white">
            <Github size={20} />
          </a>
        </div>
      </header>

      {/* Stats */}
      <StatsCards history={history} />

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <PredictionForm onResult={handleResult} />
          <ResultCard result={result} />
        </div>
        <div className="lg:col-span-1">
          <HistoryPanel history={history} onClear={() => setHistory([])} />
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-12 text-center text-slate-600 text-sm pb-8">
        <p>Churn Prediction ML Pipeline • CatBoost • FastAPI • React</p>
      </footer>
    </div>
  )
}