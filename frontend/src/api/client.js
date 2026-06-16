const BASE = '/api'

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data.detail || JSON.stringify(data)
    } catch {
      // ignore
    }
    throw new Error(detail)
  }
  return res
}

async function getJSON(path) {
  const res = await fetch(`${BASE}${path}`)
  await handle(res)
  return res.json()
}

async function postJSON(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  await handle(res)
  return res.json()
}

async function putJSON(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  await handle(res)
  return res.json()
}

async function del(path) {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' })
  await handle(res)
}

// ---------------------------------------------------------------------------
// Reference data
// ---------------------------------------------------------------------------
export function getCustomers() {
  return getJSON('/customers')
}

export function getBreakerOptions(oem) {
  return getJSON(`/breakers/options?oem=${encodeURIComponent(oem)}`)
}

export function listBreakers({ oem, series, amperage }) {
  const params = new URLSearchParams({ oem })
  if (series) params.set('series', series)
  if (amperage !== undefined && amperage !== null) params.set('amperage', amperage)
  return getJSON(`/breakers?${params.toString()}`)
}

export function getBreaker(breakerId) {
  return getJSON(`/breakers/${breakerId}`)
}

export function listAccessories(params = {}) {
  const qs = new URLSearchParams(params)
  return getJSON(`/accessories${qs.toString() ? `?${qs.toString()}` : ''}`)
}

// ---------------------------------------------------------------------------
// Quotation
// ---------------------------------------------------------------------------
export function previewQuotation(payload) {
  return postJSON('/quotation/preview', payload)
}

async function downloadFile(endpoint, payload, fallbackName) {
  const res = await fetch(`${BASE}/quotation/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  await handle(res)

  const blob = await res.blob()
  const disposition = res.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : fallbackName

  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export function downloadExcel(payload) {
  return downloadFile('export/excel', payload, 'BOM.xlsx')
}

export function downloadSpec(payload) {
  return downloadFile('export/spec', payload, 'TechnicalSpec.docx')
}

// ---------------------------------------------------------------------------
// Admin CRUD
// ---------------------------------------------------------------------------
export function adminListBreakers() {
  return getJSON('/admin/breakers')
}
export function adminCreateBreaker(payload) {
  return postJSON('/admin/breakers', payload)
}
export function adminUpdateBreaker(id, payload) {
  return putJSON(`/admin/breakers/${id}`, payload)
}
export function adminDeleteBreaker(id) {
  return del(`/admin/breakers/${id}`)
}

export function adminListAccessories() {
  return getJSON('/admin/accessories')
}
export function adminCreateAccessory(payload) {
  return postJSON('/admin/accessories', payload)
}
export function adminUpdateAccessory(id, payload) {
  return putJSON(`/admin/accessories/${id}`, payload)
}
export function adminDeleteAccessory(id) {
  return del(`/admin/accessories/${id}`)
}
