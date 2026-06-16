import React from 'react'

const CATEGORY_LABELS = {
  incomer: 'Incomer',
  outgoing: 'Outgoing',
  cable: 'Cable',
  busbar: 'Busbar',
  accessory: 'Accessory',
}

const CATEGORY_COLORS = {
  incomer: 'bg-blue-50 text-blue-700',
  outgoing: 'bg-green-50 text-green-700',
  cable: 'bg-gray-100 text-gray-600',
  busbar: 'bg-amber-50 text-amber-700',
  accessory: 'bg-purple-50 text-purple-700',
}

function formatCurrency(value) {
  if (value === 0) return '-'
  return `$${value.toFixed(2)}`
}

/**
 * props:
 *  - quotation: QuotationResponse | null
 *  - loading: boolean
 *  - error: string | null
 */
export default function BOMPreview({ quotation, loading, error }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Bill of Materials Preview</h2>

      {loading && (
        <div className="text-sm text-gray-500 py-8 text-center">Calculating BOM...</div>
      )}

      {!loading && error && (
        <div className="rounded-md bg-red-50 border border-red-200 text-red-700 text-sm p-3">
          {error}
        </div>
      )}

      {!loading && !error && quotation && (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-brand-500 text-white text-left">
                  <th className="px-3 py-2 font-medium rounded-tl-md w-12">S/N</th>
                  <th className="px-3 py-2 font-medium">Item Description</th>
                  <th className="px-3 py-2 font-medium text-center">Type</th>
                  <th className="px-3 py-2 font-medium text-center">Qty</th>
                  <th className="px-3 py-2 font-medium">Part Number</th>
                  <th className="px-3 py-2 font-medium text-right">Unit Price</th>
                  <th className="px-3 py-2 font-medium text-right rounded-tr-md">Total</th>
                </tr>
              </thead>
              <tbody>
                {quotation.bom.map((line) => (
                  <tr key={line.sn} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-500">{line.sn}</td>
                    <td className="px-3 py-2 text-gray-800">{line.description}</td>
                    <td className="px-3 py-2 text-center">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CATEGORY_COLORS[line.category] || ''}`}>
                        {CATEGORY_LABELS[line.category] || line.category}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center text-gray-700">{line.quantity}</td>
                    <td className="px-3 py-2 text-gray-600 font-mono text-xs">{line.part_number}</td>
                    <td className="px-3 py-2 text-right text-gray-700">{formatCurrency(line.unit_price)}</td>
                    <td className="px-3 py-2 text-right font-medium text-gray-800">{formatCurrency(line.total_price)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50 font-semibold">
                  <td colSpan={6} className="px-3 py-2 text-right text-gray-700">Grand Total</td>
                  <td className="px-3 py-2 text-right text-gray-900">${quotation.grand_total.toFixed(2)}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          {quotation.warnings && quotation.warnings.length > 0 && (
            <div className="mt-4 space-y-2">
              {quotation.warnings.map((w, i) => (
                <div key={i} className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
                  ⚠ {w}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {!loading && !error && !quotation && (
        <div className="text-sm text-gray-400 py-8 text-center">
          Configure incomers and outgoings to see the BOM preview.
        </div>
      )}
    </div>
  )
}
