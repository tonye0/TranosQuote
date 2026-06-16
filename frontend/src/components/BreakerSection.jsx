import React, { useEffect, useState, useCallback } from 'react'
import { listBreakers } from '../api/client'

/**
 * A list of breaker rows for incomer or outgoing configuration.
 * Each row lets the user pick: series → amperage → specific breaker (kA).
 * Cable size or busbar is shown automatically based on amperage.
 *
 * props:
 *  - title: section heading
 *  - rows: [{ id, quantity, series, amperage, breaker_id }]
 *  - onChange: (newRows) => void
 *  - oem: "Schneider" | "Siemens"
 *  - seriesList: string[] (available series for the OEM)
 *  - amperages: number[] (all amperages for OEM, filtered per series)
 */
export default function BreakerSection({ title, rows, onChange, oem, seriesList, amperages }) {
  // breakerOptions[rowId] = array of breaker objects matching OEM+series+amperage
  const [breakerOptions, setBreakerOptions] = useState({})

  const fetchOptions = useCallback(async (rowId, series, amperage) => {
    if (!oem || !series || !amperage) return
    try {
      const results = await listBreakers({ oem, series, amperage })
      setBreakerOptions(prev => ({ ...prev, [rowId]: results }))
    } catch {
      setBreakerOptions(prev => ({ ...prev, [rowId]: [] }))
    }
  }, [oem])

  useEffect(() => {
    rows.forEach(row => {
      if (row.series && row.amperage) {
        fetchOptions(row.id, row.series, row.amperage)
      }
    })
  }, [rows, fetchOptions])

  function updateRow(id, changes) {
    const newRows = rows.map(r => {
      if (r.id !== id) return r
      const updated = { ...r, ...changes }
      // Reset breaker_id when series or amperage changes
      if ('series' in changes || 'amperage' in changes) {
        updated.breaker_id = null
      }
      return updated
    })
    onChange(newRows)
  }

  function addRow() {
    const newId = Date.now()
    onChange([
      ...rows,
      {
        id: newId,
        quantity: 1,
        series: seriesList[0] || '',
        amperage: amperages[0] || '',
        breaker_id: null,
      },
    ])
  }

  function removeRow(id) {
    if (rows.length === 1) return
    onChange(rows.filter(r => r.id !== id))
  }

  function supplyLabel(breaker) {
    if (!breaker) return null
    if (breaker.cable_size) return { label: `Cable: ${breaker.cable_size}`, color: 'text-blue-700' }
    if (breaker.busbar) return { label: `Busbar: ${breaker.busbar}`, color: 'text-amber-700' }
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">{title}</h2>
        <button
          type="button"
          onClick={addRow}
          className="text-sm font-medium text-[#1f4e78] hover:text-[#153654] border border-[#1f4e78] hover:border-[#153654] rounded-md px-3 py-1.5 transition"
        >
          + Add Row
        </button>
      </div>

      <div className="space-y-3">
        {rows.map(row => {
          const options = breakerOptions[row.id] || []
          const selectedBreaker = options.find(b => b.id === row.breaker_id) || null
          const supply = supplyLabel(selectedBreaker)

          return (
            <div key={row.id} className="border border-gray-100 rounded-md p-3 bg-gray-50">
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 items-end">

                {/* Quantity */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Qty</label>
                  <input
                    type="number" min="1" max="200"
                    value={row.quantity}
                    onChange={e => updateRow(row.id, { quantity: Math.max(1, parseInt(e.target.value) || 1) })}
                    className="w-full rounded-md border-gray-300 text-sm py-1.5 px-2 border focus:border-[#1f4e78] focus:ring-[#1f4e78]"
                  />
                </div>

                {/* Series */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Series</label>
                  <select
                    value={row.series}
                    onChange={e => updateRow(row.id, { series: e.target.value })}
                    className="w-full rounded-md border-gray-300 text-sm py-1.5 px-2 border bg-white focus:border-[#1f4e78] focus:ring-[#1f4e78]"
                  >
                    <option value="">Select…</option>
                    {seriesList.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>

                {/* Amperage */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Amperage (A)</label>
                  <select
                    value={row.amperage}
                    onChange={e => updateRow(row.id, { amperage: parseInt(e.target.value) })}
                    className="w-full rounded-md border-gray-300 text-sm py-1.5 px-2 border bg-white focus:border-[#1f4e78] focus:ring-[#1f4e78]"
                  >
                    <option value="">Select…</option>
                    {amperages.map(a => <option key={a} value={a}>{a} A</option>)}
                  </select>
                </div>

                {/* Specific breaker (kA rating + part number) */}
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Breaker / kA Rating</label>
                  {!row.series || !row.amperage ? (
                    <p className="text-xs text-gray-400 py-1.5">Select series & amperage first</p>
                  ) : options.length === 0 ? (
                    <p className="text-xs text-red-500 py-1.5">No match found for {oem} {row.series} {row.amperage}A</p>
                  ) : (
                    <select
                      value={row.breaker_id ?? ''}
                      onChange={e => updateRow(row.id, { breaker_id: parseInt(e.target.value) })}
                      className="w-full rounded-md border-gray-300 text-sm py-1.5 px-2 border bg-white focus:border-[#1f4e78] focus:ring-[#1f4e78]"
                    >
                      <option value="">Select kA…</option>
                      {options.map(b => (
                        <option key={b.id} value={b.id}>
                          {b.rating_kA} kA — {b.part_number}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {/* Cable/busbar + remove */}
                <div className="flex items-center gap-2">
                  <div className="flex-1 text-xs leading-tight">
                    {supply && (
                      <span className={`font-medium ${supply.color}`}>
                        {supply.label}
                      </span>
                    )}
                    {selectedBreaker && (
                      <div className="text-gray-500 mt-0.5">
                        ${selectedBreaker.unit_price.toFixed(2)} / unit
                      </div>
                    )}
                  </div>
                  {rows.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRow(row.id)}
                      className="text-red-400 hover:text-red-600 text-lg leading-none px-1"
                      title="Remove row"
                    >✕</button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
