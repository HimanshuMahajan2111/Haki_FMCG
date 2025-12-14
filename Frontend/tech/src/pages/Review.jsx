import React, { useState } from 'react'
import { CheckCircle, AlertCircle, DollarSign } from 'lucide-react'

export default function Review() {
  const [approved, setApproved] = useState(false)
  const [reviewerName, setReviewerName] = useState('Technical Expert')

  const technicalData = [
    {
      rfpItem: "11 kV XLPE Armoured Power Cable",
      selectedProduct: "11 kV High Tension Cables 3C x 95 sq.mm Copper XLPE",
      specMatch: 92,
      specs: [
        { param: "Voltage Rating", rfpValue: "11 kV", productValue: "11 kV", status: "full" },
        { param: "Conductor Material", rfpValue: "Copper", productValue: "Copper", status: "full" },
        { param: "Cross Section", rfpValue: "95", productValue: "95", status: "full" },
        { param: "Cores", rfpValue: "3", productValue: "3", status: "full" },
        { param: "Insulation", rfpValue: "XLPE", productValue: "XLPE", status: "full" },
        { param: "Armour", rfpValue: "SWA", productValue: "SWA", status: "full" },
        { param: "Standard", rfpValue: "IS 7098", productValue: "IS 7098", status: "full" },
        { param: "Temperature", rfpValue: "90°C", productValue: "90°C", status: "full" },
      ]
    },
    {
      rfpItem: "1.1 kV PVC Insulated Cable",
      selectedProduct: "1.1 kV Low Tension Cables 4C x 50 sq.mm Aluminium PVC",
      specMatch: 88,
      specs: [
        { param: "Voltage Rating", rfpValue: "1.1 kV", productValue: "1.1 kV", status: "full" },
        { param: "Conductor Material", rfpValue: "Aluminium", productValue: "Aluminium", status: "full" },
        { param: "Cross Section", rfpValue: "50", productValue: "50", status: "full" },
        { param: "Cores", rfpValue: "4", productValue: "4", status: "full" },
        { param: "Insulation", rfpValue: "PVC", productValue: "PVC", status: "full" },
        { param: "Armour", rfpValue: "None", productValue: "None", status: "full" },
        { param: "Standard", rfpValue: "IS 1554", productValue: "IS 1554", status: "full" },
        { param: "Temperature", rfpValue: "70°C", productValue: "70°C", status: "full" },
      ]
    }
  ]

  const handleApprove = () => {
    setApproved(true)
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Step 3: Expert Review & Validation</h1>
        <p className="text-gray-600 mt-2">Human-in-the-Loop checkpoint for quality assurance</p>
      </div>

      {/* Technical Compliance Review */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">Technical Compliance Review</h2>
        {technicalData.map((item, idx) => (
          <div key={idx} className="bg-white rounded-lg shadow mb-4">
            <div className="p-4 bg-gray-50 border-b flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-lg">📦 {item.rfpItem}</h3>
                <p className="text-sm text-gray-600 mt-1">Selected: {item.selectedProduct}</p>
              </div>
              <span className="px-4 py-2 bg-green-100 text-green-800 rounded-full font-semibold">
                Match: {item.specMatch}%
              </span>
            </div>
            <div className="p-4">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 text-sm font-semibold text-gray-600">Parameter</th>
                    <th className="text-left py-2 text-sm font-semibold text-gray-600">RFP Value</th>
                    <th className="text-left py-2 text-sm font-semibold text-gray-600">Product Value</th>
                    <th className="text-center py-2 text-sm font-semibold text-gray-600">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {item.specs.map((spec, specIdx) => (
                    <tr key={specIdx} className="border-b">
                      <td className="py-2">{spec.param}</td>
                      <td className="py-2">{spec.rfpValue}</td>
                      <td className={`py-2 ${spec.status === 'full' ? 'bg-green-50' : spec.status === 'partial' ? 'bg-yellow-50' : 'bg-red-50'}`}>
                        {spec.productValue}
                      </td>
                      <td className="py-2 text-center">
                        {spec.status === 'full' ? '✅' : spec.status === 'partial' ? '⚠️' : '❌'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>

      {/* Pricing Review */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-2xl font-bold mb-4">Pricing Review</h2>
        <div className="grid grid-cols-3 gap-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Material Cost</p>
            <p className="text-3xl font-bold text-blue-600">₹8.5L</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Testing Cost</p>
            <p className="text-3xl font-bold text-green-600">₹4.0L</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Grand Total</p>
            <p className="text-3xl font-bold text-purple-600">₹12.5L</p>
          </div>
        </div>
      </div>

      {/* Approval Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Final Approval</h2>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Reviewer Name
          </label>
          <input
            type="text"
            value={reviewerName}
            onChange={(e) => setReviewerName(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {!approved ? (
          <button
            onClick={handleApprove}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <CheckCircle size={20} />
            ✅ Approve & Generate Document
          </button>
        ) : (
          <>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <p className="text-green-800 font-semibold">✅ Response approved by {reviewerName}!</p>
            </div>
            <button
              onClick={() => window.location.href = '/document'}
              className="w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              ➡️ Go to Final Document
            </button>
          </>
        )}
      </div>
    </div>
  )
}
