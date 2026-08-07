import { useState } from 'react'
import { motion } from 'framer-motion'
import { Send, Loader2 } from 'lucide-react'
import { predictChurn } from '../api/client'

const initialForm = {
  customer_id: '',
  gender: 'Male',
  SeniorCitizen: 0,
  Partner: 'No',
  Dependents: 'No',
  tenure: 12,
  PhoneService: 'Yes',
  MultipleLines: 'No',
  InternetService: 'DSL',
  OnlineSecurity: 'No',
  OnlineBackup: 'Yes',
  DeviceProtection: 'No',
  TechSupport: 'No',
  StreamingTV: 'No',
  StreamingMovies: 'No',
  Contract: 'Month-to-month',
  PaperlessBilling: 'Yes',
  PaymentMethod: 'Electronic check',
  MonthlyCharges: 29.85,
  TotalCharges: '29.85',
}

export default function PredictionForm({ onResult }) {
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    const { name, value, type } = e.target
    setForm(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = {
        ...form,
        SeniorCitizen: parseInt(form.SeniorCitizen),
        tenure: parseInt(form.tenure),
        MonthlyCharges: parseFloat(form.MonthlyCharges),
      }
      const result = await predictChurn(data)
      onResult(result)
    } catch (err) {
      alert('Ошибка: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const selectField = (name, label, options) => (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</label>
      <select name={name} value={form[name]} onChange={handleChange} className="input-field">
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  )

  const numberField = (name, label, min, max, step = 1) => (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</label>
      <input type="number" name={name} value={form[name]} onChange={handleChange}
             min={min} max={max} step={step} className="input-field" />
    </div>
  )

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
          Новое предсказание
        </h2>
        <button 
          type="button" 
          onClick={() => setForm(initialForm)}
          className="text-xs text-slate-400 hover:text-white transition-colors"
        >
          Сбросить
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">Customer ID</label>
            <input name="customer_id" value={form.customer_id} onChange={handleChange}
                   placeholder="Опционально" className="input-field" />
          </div>

          {selectField('gender', 'Пол', ['Male', 'Female'])}
          {selectField('SeniorCitizen', 'Пенсионер', ['0', '1'])}
          {selectField('Partner', 'Партнёр', ['Yes', 'No'])}
          {selectField('Dependents', 'Иждивенцы', ['Yes', 'No'])}
          {numberField('tenure', 'Стаж (мес.)', 0, 100)}
          {selectField('PhoneService', 'Телефон', ['Yes', 'No'])}
          {selectField('MultipleLines', 'Несколько линий', ['Yes', 'No', 'No phone service'])}
          {selectField('InternetService', 'Интернет', ['DSL', 'Fiber optic', 'No'])}
          {selectField('OnlineSecurity', 'Безопасность', ['Yes', 'No', 'No internet service'])}
          {selectField('OnlineBackup', 'Бэкап', ['Yes', 'No', 'No internet service'])}
          {selectField('DeviceProtection', 'Защита устройств', ['Yes', 'No', 'No internet service'])}
          {selectField('TechSupport', 'Техподдержка', ['Yes', 'No', 'No internet service'])}
          {selectField('StreamingTV', 'ТВ', ['Yes', 'No', 'No internet service'])}
          {selectField('StreamingMovies', 'Кино', ['Yes', 'No', 'No internet service'])}
          {selectField('Contract', 'Контракт', ['Month-to-month', 'One year', 'Two year'])}
          {selectField('PaperlessBilling', 'Эл. счёт', ['Yes', 'No'])}
          {selectField('PaymentMethod', 'Способ оплаты', ['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)'])}
          {numberField('MonthlyCharges', 'Ежемес. платёж', 0, 200, 0.01)}
          {numberField('TotalCharges', 'Всего заплачено', 0, 10000, 0.01)}
        </div>

        <div className="pt-2">
          <button type="submit" disabled={loading} className="btn-primary w-full md:w-auto flex items-center justify-center gap-2">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            {loading ? 'Анализирую...' : 'Предсказать отток'}
          </button>
        </div>
      </form>
    </motion.div>
  )
}