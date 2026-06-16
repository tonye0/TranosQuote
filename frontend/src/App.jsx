import React, { useEffect, useState, useCallback, useRef } from 'react'
import BreakerSection from './components/BreakerSection'
import OptionalComponents from './components/OptionalComponents'
import BOMPreview from './components/BOMPreview'
import AdminPanel from './components/AdminPanel'
import { getCustomers, getBreakerOptions, previewQuotation, downloadExcel, downloadSpec } from './api/client'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const OEMS = ['Schneider', 'Siemens']

const DEFAULT_OPTIONAL = {
  indication_lamp_phase: false,
  indication_lamp_on_off_trip: false,
  meter: false, meter_qty: 1,
  fan: false, fan_qty: 1,
  filter: false, filter_qty: 1,
  e_stop: false, e_stop_qty: 1,
}

function makeRow() {
  return { id: Date.now() + Math.random(), quantity: 1, series: '', amperage: '', breaker_id: null }
}

function rowsValid(rows) {
  return rows.every(r => r.quantity > 0 && r.series && r.amperage && r.breaker_id)
}

function buildPayload({ customerId, customerName, oem, projectName, incomers, outgoings, optional, isDaystar }) {
  return {
    customer_id: customerId,
    customer_name: customerName || null,
    oem,
    project_name: projectName || 'Untitled Project',
    incomers: incomers.map(r => ({ quantity: r.quantity, breaker_id: r.breaker_id })),
    outgoings: outgoings.map(r => ({ quantity: r.quantity, breaker_id: r.breaker_id })),
    optional_components: isDaystar ? null : optional,
  }
}

// ---------------------------------------------------------------------------
// Logo (inline SVG to avoid asset pipeline complexity)
// ---------------------------------------------------------------------------
function Logo() {
  return (
    <div className="flex items-center gap-2 select-none">
      <div className="w-9 h-9 rounded-lg flex items-center justify-center"
        style={{ background: 'rgba(255,255,255,0.18)' }}>
        <svg viewBox="0 0 36 36" fill="none" className="w-6 h-6">
          <rect x="4" y="6" width="28" height="24" rx="2" fill="white" fillOpacity="0.9" />
          <rect x="8" y="10" width="8" height="4" rx="1" fill="#1f4e78" />
          <rect x="20" y="10" width="8" height="4" rx="1" fill="#1f4e78" />
          <rect x="8" y="17" width="8" height="4" rx="1" fill="#1f4e78" />
          <rect x="20" y="17" width="8" height="4" rx="1" fill="#1f4e78" />
          <rect x="14" y="24" width="8" height="2" rx="1" fill="#1f4e78" />
          <line x1="18" y1="6" x2="18" y2="3" stroke="white" strokeWidth="2" strokeLinecap="round" />
        </svg>
      </div>
      <div className="leading-tight">
        <div className="text-white font-bold text-sm tracking-wide">PanelQuote</div>
        <div className="text-blue-200 text-xs">AC Combiner Systems</div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main App
// ---------------------------------------------------------------------------
export default function App() {
  const [customers, setCustomers] = useState([])
  const [customerId, setCustomerId] = useState('')
  const [customerName, setCustomerName] = useState('')
  const [oem, setOem] = useState('')
  const [projectName, setProjectName] = useState('')

  const [seriesList, setSeriesList] = useState([])
  const [amperages, setAmperages] = useState([])

  const [incomers, setIncomers] = useState([makeRow()])
  const [outgoings, setOutgoings] = useState([makeRow()])
  const [optional, setOptional] = useState(DEFAULT_OPTIONAL)

  const [quotation, setQuotation] = useState(null)
  const [loadingBOM, setLoadingBOM] = useState(false)
  const [bomError, setBomError] = useState(null)
  const [exporting, setExporting] = useState(null)
  const [exportError, setExportError] = useState(null)
  const [initError, setInitError] = useState(null)
  const [showAdmin, setShowAdmin] = useState(false)

  const debounceRef = useRef(null)

  // Load customers on mount
  useEffect(() => {
    getCustomers()
      .then(data => {
        setCustomers(data)
        if (data.length > 0) setCustomerId(data[0].id)
      })
      .catch(() => setInitError('Could not connect to the API. Make sure the backend is running on port 8000.'))
  }, [])

  // Load breaker options when OEM changes
  useEffect(() => {
    if (!oem) return
    getBreakerOptions(oem)
      .then(data => {
        setSeriesList(data.series_list)
        setAmperages(data.amperages)
        // Reset rows when OEM changes - old selections are no longer valid
        setIncomers([makeRow()])
        setOutgoings([makeRow()])
      })
      .catch(() => {
        setSeriesList([])
        setAmperages([])
      })
  }, [oem])

  const selectedCustomer = customers.find(c => c.id === customerId)
  const isDaystar = selectedCustomer?.id === 'daystar'
  const requiresCustomName = selectedCustomer?.requires_custom_name

  // Live BOM preview - debounced 500ms
  useEffect(() => {
    if (!customerId || !oem) return
    if (!rowsValid(incomers) || !rowsValid(outgoings)) return
    if (requiresCustomName && !customerName.trim()) return

    setLoadingBOM(true)
    setBomError(null)

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const payload = buildPayload({ customerId, customerName, oem, projectName, incomers, outgoings, optional, isDaystar })
        const data = await previewQuotation(payload)
        setQuotation(data)
      } catch (e) {
        setBomError(e.message)
        setQuotation(null)
      } finally {
        setLoadingBOM(false)
      }
    }, 500)

    return () => clearTimeout(debounceRef.current)
  }, [customerId, customerName, oem, projectName, incomers, outgoings, optional, isDaystar, requiresCustomName])

  async function handleExport(type) {
    setExportError(null)
    setExporting(type)
    try {
      const payload = buildPayload({ customerId, customerName, oem, projectName, incomers, outgoings, optional, isDaystar })
      if (type === 'excel') await downloadExcel(payload)
      else await downloadSpec(payload)
    } catch (e) {
      setExportError(e.message)
    } finally {
      setExporting(null)
    }
  }

  const canExport = quotation && !loadingBOM && exporting === null

  if (initError) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-md bg-white border border-red-200 rounded-lg shadow-sm p-6 text-center">
          <div className="text-3xl mb-3">⚡</div>
          <h1 className="text-lg font-semibold text-red-700 mb-2">Connection Error</h1>
          <p className="text-sm text-gray-600">{initError}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-16">
      {/* Admin panel overlay */}
      {showAdmin && <AdminPanel onClose={() => setShowAdmin(false)} />}

      {/* Header */}
      <header className="bg-[#1f4e78] text-white px-6 py-4 shadow-sm">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <Logo />
          <div className="flex items-center gap-3">
            <span className="text-blue-200 text-sm hidden sm:block">AC Combiner Panel Quotation Tool</span>
            <button
              onClick={() => setShowAdmin(true)}
              className="text-sm font-medium text-white border border-white/30 hover:border-white/60 hover:bg-white/10 rounded-md px-3 py-1.5 transition"
            >
              ⚙ Settings
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 mt-6 space-y-5">

        {/* Step 1: OEM selection (requirement #6) - must happen first */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-800 mb-1">Step 1 — Select OEM</h2>
          <p className="text-sm text-gray-500 mb-4">
            Choose the breaker manufacturer. All component selections will be scoped to this OEM.
          </p>
          <div className="flex gap-3 flex-wrap">
            {OEMS.map(o => (
              <button
                key={o}
                type="button"
                onClick={() => setOem(o)}
                className={`px-6 py-3 rounded-lg border-2 font-semibold text-sm transition ${
                  oem === o
                    ? 'border-[#1f4e78] bg-[#1f4e78] text-white shadow-md'
                    : 'border-gray-300 bg-white text-gray-700 hover:border-[#1f4e78] hover:text-[#1f4e78]'
                }`}
              >
                {o}
              </button>
            ))}
          </div>
          {!oem && (
            <p className="mt-3 text-xs text-amber-600 font-medium">⚠ Please select an OEM to continue.</p>
          )}
        </div>

        {/* Step 2: Customer + Project */}
        {oem && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Step 2 — Customer & Project</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Customer Template</label>
                <select
                  value={customerId}
                  onChange={e => { setCustomerId(e.target.value); setCustomerName('') }}
                  className="w-full rounded-md border-gray-300 border text-sm py-2 px-3 bg-white focus:border-[#1f4e78] focus:outline-none"
                >
                  {customers.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                {selectedCustomer && (
                  <p className="mt-1 text-xs text-gray-500">{selectedCustomer.description}</p>
                )}
              </div>

              {/* Requirement #2: show customer name input for "Others" */}
              {requiresCustomName && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Customer Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Enter the customer's name…"
                    value={customerName}
                    onChange={e => setCustomerName(e.target.value)}
                    className="w-full rounded-md border-gray-300 border text-sm py-2 px-3 focus:border-[#1f4e78] focus:outline-none"
                  />
                  {!customerName.trim() && (
                    <p className="mt-1 text-xs text-red-500">Required before generating a quotation.</p>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
                <input
                  type="text"
                  placeholder="e.g. Solar Farm Phase 1"
                  value={projectName}
                  onChange={e => setProjectName(e.target.value)}
                  className="w-full rounded-md border-gray-300 border text-sm py-2 px-3 focus:border-[#1f4e78] focus:outline-none"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Breaker configuration */}
        {oem && seriesList.length > 0 && (
          <>
            <BreakerSection
              title="Step 3 — Incomer Configuration"
              rows={incomers}
              onChange={setIncomers}
              oem={oem}
              seriesList={seriesList}
              amperages={amperages}
            />
            <BreakerSection
              title="Outgoing Configuration"
              rows={outgoings}
              onChange={setOutgoings}
              oem={oem}
              seriesList={seriesList}
              amperages={amperages}
            />
          </>
        )}

        {/* Daystar auto-include banner */}
        {oem && isDaystar && (
          <div className="bg-blue-50 border border-blue-200 rounded-md px-4 py-3 text-sm text-blue-800">
            <strong>Auto-included for Daystar:</strong> Phase indication lamps, shunt trip coil(s) & motor
            mechanism (per incomer, sized to frame/OEM), power meter, cooling fan, and intake filter are
            added automatically. Terminal blocks are included for all breakers rated 200A and below.
          </div>
        )}

        {/* Optional components for Others */}
        {oem && !isDaystar && (
          <OptionalComponents value={optional} onChange={setOptional} />
        )}

        {/* BOM Preview */}
        {oem && (
          <BOMPreview quotation={quotation} loading={loadingBOM} error={bomError} />
        )}

        {/* Export */}
        {oem && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <h2 className="text-lg font-semibold text-gray-800 mb-1">Generate Quotation</h2>
            <p className="text-sm text-gray-500 mb-4">
              Download the Bill of Materials (Excel) and technical specification document (Word).
              {!canExport && ' Complete all selections above to enable export.'}
            </p>

            {exportError && (
              <div className="mb-3 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm p-3">
                {exportError}
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                type="button"
                onClick={() => handleExport('excel')}
                disabled={!canExport}
                className="flex-1 bg-[#1f4e78] hover:bg-[#153654] disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium rounded-md py-2.5 px-4 transition text-sm"
              >
                {exporting === 'excel' ? 'Generating…' : '📊 Download BOM (Excel)'}
              </button>
              <button
                type="button"
                onClick={() => handleExport('spec')}
                disabled={!canExport}
                className="flex-1 bg-gray-700 hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium rounded-md py-2.5 px-4 transition text-sm"
              >
                {exporting === 'spec' ? 'Generating…' : '📄 Download Technical Spec (Word)'}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
