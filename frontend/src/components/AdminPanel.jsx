import React, { useEffect, useState } from 'react'
import {
  adminListBreakers, adminCreateBreaker, adminUpdateBreaker, adminDeleteBreaker,
  adminListAccessories, adminCreateAccessory, adminUpdateAccessory, adminDeleteAccessory,
} from '../api/client'

const FRAME_SIZES = ['FRAME_100', 'FRAME_250', 'FRAME_400', 'FRAME_630', 'FRAME_630b...1600']
const OEMS = ['Schneider', 'Siemens']
const SCOPES = ['all', 'daystar', 'others']

const EMPTY_BREAKER = { oem: 'Schneider', series: '', amperage: '', rating_kA: '', voltage: 415, part_number: '', unit_price: '', frame_size: 'FRAME_100' }
const EMPTY_ACCESSORY = { type: '', applicability: 'ALL', oem: '', customer_scope: 'all', part_number: '', description: '', unit_price: '' }

function Input({ label, type = 'text', value, onChange, required, placeholder, small }) {
  return (
    <div className={small ? 'col-span-1' : 'col-span-2'}>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-md border border-gray-300 text-sm py-1.5 px-2 focus:border-[#1f4e78] focus:ring-[#1f4e78] focus:outline-none"
      />
    </div>
  )
}

function Select({ label, value, onChange, options, small }) {
  return (
    <div className={small ? 'col-span-1' : 'col-span-2'}>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full rounded-md border border-gray-300 text-sm py-1.5 px-2 bg-white focus:border-[#1f4e78] focus:ring-[#1f4e78] focus:outline-none"
      >
        {options.map(o => (
          <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>
        ))}
      </select>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Breaker CRUD
// ---------------------------------------------------------------------------
function BreakerAdmin() {
  const [breakers, setBreakers] = useState([])
  const [form, setForm] = useState(EMPTY_BREAKER)
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('')

  async function load() {
    try {
      const data = await adminListBreakers()
      setBreakers(data)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => { load() }, [])

  function set(field) {
    return val => setForm(f => ({ ...f, [field]: val }))
  }

  function startEdit(b) {
    setEditingId(b.id)
    setForm({ oem: b.oem, series: b.series, amperage: b.amperage, rating_kA: b.rating_kA, voltage: b.voltage, part_number: b.part_number, unit_price: b.unit_price, frame_size: b.frame_size })
    setError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_BREAKER)
    setError(null)
  }

  async function save() {
    setLoading(true)
    setError(null)
    const payload = { ...form, amperage: parseInt(form.amperage), rating_kA: parseInt(form.rating_kA), voltage: parseInt(form.voltage), unit_price: parseFloat(form.unit_price) }
    try {
      if (editingId) {
        await adminUpdateBreaker(editingId, payload)
      } else {
        await adminCreateBreaker(payload)
      }
      cancelEdit()
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function remove(id) {
    if (!window.confirm('Delete this breaker? This cannot be undone.')) return
    try {
      await adminDeleteBreaker(id)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  const filtered = breakers.filter(b =>
    !filter || [b.oem, b.series, String(b.amperage), b.part_number].some(v => v.toLowerCase().includes(filter.toLowerCase()))
  )

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-800 mb-4">Breaker Catalog</h3>

      {/* Form */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-5">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">{editingId ? 'Edit Breaker' : 'Add New Breaker'}</h4>
        <div className="grid grid-cols-4 gap-3">
          <Select label="OEM *" value={form.oem} onChange={set('oem')} options={OEMS} small />
          <Input label="Series *" value={form.series} onChange={set('series')} placeholder="e.g. NSX" required small />
          <Input label="Amperage (A) *" type="number" value={form.amperage} onChange={set('amperage')} placeholder="e.g. 250" required small />
          <Input label="Rating (kA) *" type="number" value={form.rating_kA} onChange={set('rating_kA')} placeholder="e.g. 36" required small />
          <Input label="Part Number *" value={form.part_number} onChange={set('part_number')} placeholder="e.g. NSX250N-TM250D" required small />
          <Input label="Unit Price ($) *" type="number" value={form.unit_price} onChange={set('unit_price')} placeholder="e.g. 258.00" required small />
          <Select label="Frame Size *" value={form.frame_size} onChange={set('frame_size')} options={FRAME_SIZES} small />
          <Input label="Voltage (V)" type="number" value={form.voltage} onChange={set('voltage')} small />
        </div>
        {error && <p className="text-red-600 text-xs mt-2">{error}</p>}
        <div className="flex gap-2 mt-3">
          <button onClick={save} disabled={loading} className="bg-[#1f4e78] hover:bg-[#153654] text-white text-sm font-medium rounded-md px-4 py-1.5 disabled:opacity-50 transition">
            {loading ? 'Saving…' : editingId ? 'Update' : 'Add Breaker'}
          </button>
          {editingId && (
            <button onClick={cancelEdit} className="border border-gray-300 text-gray-700 text-sm rounded-md px-4 py-1.5 hover:bg-gray-50 transition">Cancel</button>
          )}
        </div>
      </div>

      {/* Filter + table */}
      <input
        type="text"
        placeholder="Filter by OEM, series, amperage, or part number…"
        value={filter}
        onChange={e => setFilter(e.target.value)}
        className="w-full border border-gray-300 rounded-md text-sm py-1.5 px-3 mb-3 focus:border-[#1f4e78] focus:outline-none"
      />

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100 text-gray-600 text-left">
            <tr>
              {['OEM', 'Series', 'A', 'kA', 'Frame', 'Part Number', 'Price', ''].map(h => (
                <th key={h} className="px-3 py-2 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(b => (
              <tr key={b.id} className="border-t border-gray-100 hover:bg-gray-50">
                <td className="px-3 py-2">{b.oem}</td>
                <td className="px-3 py-2 font-medium">{b.series}</td>
                <td className="px-3 py-2">{b.amperage}</td>
                <td className="px-3 py-2">{b.rating_kA}</td>
                <td className="px-3 py-2 text-xs text-gray-500">{b.frame_size}</td>
                <td className="px-3 py-2 font-mono text-xs">{b.part_number}</td>
                <td className="px-3 py-2">${b.unit_price.toFixed(2)}</td>
                <td className="px-3 py-2 flex gap-2">
                  <button onClick={() => startEdit(b)} className="text-[#1f4e78] hover:underline text-xs">Edit</button>
                  <button onClick={() => remove(b.id)} className="text-red-500 hover:underline text-xs">Delete</button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={8} className="text-center text-gray-400 py-6 text-sm">No breakers found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Accessory CRUD
// ---------------------------------------------------------------------------
function AccessoryAdmin() {
  const [accessories, setAccessories] = useState([])
  const [form, setForm] = useState(EMPTY_ACCESSORY)
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('')

  async function load() {
    try {
      const data = await adminListAccessories()
      setAccessories(data)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => { load() }, [])

  function set(field) {
    return val => setForm(f => ({ ...f, [field]: val }))
  }

  function startEdit(a) {
    setEditingId(a.id)
    setForm({ type: a.type, applicability: a.applicability, oem: a.oem || '', customer_scope: a.customer_scope, part_number: a.part_number, description: a.description, unit_price: a.unit_price })
    setError(null)
  }

  function cancelEdit() {
    setEditingId(null)
    setForm(EMPTY_ACCESSORY)
    setError(null)
  }

  async function save() {
    setLoading(true)
    setError(null)
    const payload = { ...form, oem: form.oem || null, unit_price: parseFloat(form.unit_price) }
    try {
      if (editingId) {
        await adminUpdateAccessory(editingId, payload)
      } else {
        await adminCreateAccessory(payload)
      }
      cancelEdit()
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function remove(id) {
    if (!window.confirm('Delete this accessory? This cannot be undone.')) return
    try {
      await adminDeleteAccessory(id)
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  const APPLICABILITY_OPTIONS = ['ALL', 'STANDARD', 'LE_200A', 'FRAME_100', 'FRAME_250', 'FRAME_400', 'FRAME_630']
  const OEM_OPTIONS = [{ value: '', label: '— OEM-agnostic —' }, ...OEMS.map(o => ({ value: o, label: o }))]

  const filtered = accessories.filter(a =>
    !filter || [a.type, a.part_number, a.description, a.applicability].some(v => v?.toLowerCase().includes(filter.toLowerCase()))
  )

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-800 mb-4">Accessory Catalog</h3>

      {/* Form */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-5">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">{editingId ? 'Edit Accessory' : 'Add New Accessory'}</h4>
        <div className="grid grid-cols-4 gap-3">
          <Input label="Type key *" value={form.type} onChange={set('type')} placeholder="e.g. shunt_trip" required small />
          <Select label="Applicability *" value={form.applicability} onChange={set('applicability')} options={APPLICABILITY_OPTIONS} small />
          <Select label="OEM" value={form.oem} onChange={set('oem')} options={OEM_OPTIONS} small />
          <Select label="Customer Scope" value={form.customer_scope} onChange={set('customer_scope')} options={SCOPES} small />
          <Input label="Part Number *" value={form.part_number} onChange={set('part_number')} placeholder="e.g. SCH-SHT-250" required small />
          <Input label="Unit Price ($) *" type="number" value={form.unit_price} onChange={set('unit_price')} placeholder="e.g. 48.00" required small />
          <div className="col-span-4">
            <label className="block text-xs font-medium text-gray-600 mb-1">Description *</label>
            <input
              type="text"
              value={form.description}
              onChange={e => set('description')(e.target.value)}
              placeholder="Full component description shown in BOM"
              className="w-full rounded-md border border-gray-300 text-sm py-1.5 px-2 focus:border-[#1f4e78] focus:outline-none"
            />
          </div>
        </div>
        {error && <p className="text-red-600 text-xs mt-2">{error}</p>}
        <div className="flex gap-2 mt-3">
          <button onClick={save} disabled={loading} className="bg-[#1f4e78] hover:bg-[#153654] text-white text-sm font-medium rounded-md px-4 py-1.5 disabled:opacity-50 transition">
            {loading ? 'Saving…' : editingId ? 'Update' : 'Add Accessory'}
          </button>
          {editingId && (
            <button onClick={cancelEdit} className="border border-gray-300 text-gray-700 text-sm rounded-md px-4 py-1.5 hover:bg-gray-50 transition">Cancel</button>
          )}
        </div>
      </div>

      <input
        type="text"
        placeholder="Filter by type, part number, or description…"
        value={filter}
        onChange={e => setFilter(e.target.value)}
        className="w-full border border-gray-300 rounded-md text-sm py-1.5 px-3 mb-3 focus:border-[#1f4e78] focus:outline-none"
      />

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100 text-gray-600 text-left">
            <tr>
              {['Type', 'Applicability', 'OEM', 'Scope', 'Part Number', 'Description', 'Price', ''].map(h => (
                <th key={h} className="px-3 py-2 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(a => (
              <tr key={a.id} className="border-t border-gray-100 hover:bg-gray-50">
                <td className="px-3 py-2 font-medium text-xs">{a.type}</td>
                <td className="px-3 py-2 text-xs text-gray-500">{a.applicability}</td>
                <td className="px-3 py-2 text-xs">{a.oem || '—'}</td>
                <td className="px-3 py-2 text-xs">{a.customer_scope}</td>
                <td className="px-3 py-2 font-mono text-xs">{a.part_number}</td>
                <td className="px-3 py-2 text-xs text-gray-600 max-w-xs truncate" title={a.description}>{a.description}</td>
                <td className="px-3 py-2">${a.unit_price.toFixed(2)}</td>
                <td className="px-3 py-2 flex gap-2">
                  <button onClick={() => startEdit(a)} className="text-[#1f4e78] hover:underline text-xs">Edit</button>
                  <button onClick={() => remove(a.id)} className="text-red-500 hover:underline text-xs">Delete</button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr><td colSpan={8} className="text-center text-gray-400 py-6 text-sm">No accessories found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main admin panel (tabs: Breakers / Accessories)
// ---------------------------------------------------------------------------
export default function AdminPanel({ onClose }) {
  const [tab, setTab] = useState('breakers')

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-start justify-center overflow-y-auto pt-6 pb-12 px-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-5xl">
        {/* Header */}
        <div className="flex items-center justify-between bg-[#1f4e78] text-white px-6 py-4 rounded-t-xl">
          <div>
            <h2 className="text-lg font-bold">Settings / Admin Panel</h2>
            <p className="text-sm text-blue-200">Manage breaker catalog and accessories</p>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white text-2xl leading-none">✕</button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 px-6 pt-4">
          {[['breakers', 'Breakers'], ['accessories', 'Accessories']].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`mr-4 pb-2 text-sm font-medium border-b-2 transition ${
                tab === key
                  ? 'border-[#1f4e78] text-[#1f4e78]'
                  : 'border-transparent text-gray-500 hover:text-gray-800'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-6">
          {tab === 'breakers' ? <BreakerAdmin /> : <AccessoryAdmin />}
        </div>
      </div>
    </div>
  )
}
