import React from 'react'

/**
 * Optional accessories panel for "Others" customers.
 *
 * Implements requirement #7 indication lamp rules:
 *   - Phase indication lamps: offered to all (Others can choose to include)
 *   - On/Off/Trip lamps: offered to Others only
 *
 * props:
 *  - value: OptionalComponentSelection object
 *  - onChange: (newValue) => void
 */
export default function OptionalComponents({ value, onChange }) {
  function toggle(key) {
    onChange({ ...value, [key]: !value[key] })
  }
  function setQty(key, qty) {
    onChange({ ...value, [`${key}_qty`]: Math.max(0, parseInt(qty) || 0) })
  }

  const LAMP_ITEMS = [
    {
      key: 'indication_lamp_phase',
      label: 'Phase Indication Lamps (R/Y/B)',
      desc: 'LED indicators for each phase — recommended for all panels',
      hasQty: false,
    },
    {
      key: 'indication_lamp_on_off_trip',
      label: 'On / Off / Trip Indication Lamps',
      desc: 'LED indicators for breaker status (On, Off, Trip)',
      hasQty: false,
    },
  ]

  const ACCESSORY_ITEMS = [
    { key: 'e_stop', label: 'Emergency Stop Button', desc: '22mm red mushroom head, NC contact', hasQty: true },
    { key: 'meter', label: 'Digital Power Meter', desc: 'V/A/kW/kWh, LCD display, RS485', hasQty: true },
    { key: 'fan', label: 'Cooling Fan', desc: '220VAC, 150 CFM, with louvre', hasQty: true },
    { key: 'filter', label: 'Intake Air Filter', desc: 'Replaceable mesh filter, fits standard fan louvre', hasQty: true },
  ]

  const renderItem = ({ key, label, desc, hasQty }) => {
    const checked = !!value[key]
    const qty = value[`${key}_qty`] ?? 1

    return (
      <div
        key={key}
        className={`flex items-start justify-between rounded-md border p-3 transition ${
          checked ? 'border-[#1f4e78] bg-blue-50' : 'border-gray-200 bg-gray-50'
        }`}
      >
        <label className="flex items-start gap-3 cursor-pointer flex-1">
          <input
            type="checkbox"
            checked={checked}
            onChange={() => toggle(key)}
            className="mt-0.5 h-4 w-4 rounded border-gray-300 text-[#1f4e78]"
          />
          <div>
            <span className="text-sm font-medium text-gray-800">{label}</span>
            <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
          </div>
        </label>

        {hasQty && checked && (
          <div className="flex items-center gap-2 ml-4 shrink-0">
            <label className="text-xs text-gray-500">Qty</label>
            <input
              type="number" min="0" max="50"
              value={qty}
              onChange={e => setQty(key, e.target.value)}
              className="w-16 rounded-md border-gray-300 text-sm py-1 px-2 border focus:border-[#1f4e78]"
            />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
      <h2 className="text-lg font-semibold text-gray-800 mb-1">Optional Components</h2>
      <p className="text-sm text-gray-500 mb-4">
        Select any accessories to include in this panel configuration.
      </p>

      <div className="mb-3">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Indication Lamps</h3>
        <div className="space-y-2">
          {LAMP_ITEMS.map(renderItem)}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Other Accessories</h3>
        <div className="space-y-2">
          {ACCESSORY_ITEMS.map(renderItem)}
        </div>
      </div>
    </div>
  )
}
