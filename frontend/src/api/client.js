const API_BASE = '/api/v1'

export async function predictChurn(data) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`)
  return res.json()
}

export async function getHistory(limit = 50) {
  const res = await fetch(`${API_BASE}/predictions?limit=${limit}`)
  return res.json()
}