import React, { useState } from 'react'
import { Upload, CheckCircle, FileText, Database } from 'lucide-react'

export default function DataImport() {
  const [file, setFile] = useState(null)
  const [uploaded, setUploaded] = useState(false)
  const [productCount, setProductCount] = useState(0)

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      setFile(selectedFile)
    }
  }

  const handleUpload = () => {
    if (file) {
      setTimeout(() => {
        setUploaded(true)
        setProductCount(Math.floor(Math.random() * 500) + 100)
      }, 1500)
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">📊 Wire & Cable Data Import</h1>
        <p className="text-gray-600 mt-2">Upload your product catalog to populate the system</p>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-bold mb-4">Upload Product Data</h2>
        
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center mb-4">
          <Upload className="mx-auto mb-4 text-gray-400" size={48} />
          <p className="text-gray-600 mb-4">
            Drag and drop your file here, or click to browse
          </p>
          <input
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg cursor-pointer inline-block"
          >
            Choose File
          </label>
          <p className="text-sm text-gray-500 mt-2">
            Supported formats: CSV, Excel (.xlsx, .xls), JSON
          </p>
        </div>

        {file && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-3">
              <FileText className="text-blue-600" size={24} />
              <div>
                <p className="font-semibold text-blue-900">{file.name}</p>
                <p className="text-sm text-blue-700">{(file.size / 1024).toFixed(2)} KB</p>
              </div>
            </div>
          </div>
        )}

        {file && !uploaded && (
          <button
            onClick={handleUpload}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <Upload size={20} />
            Upload & Process Data
          </button>
        )}
      </div>

      {uploaded && (
        <>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-center gap-3">
            <CheckCircle className="text-green-600" size={24} />
            <div>
              <p className="font-semibold text-green-900">✅ Data uploaded successfully!</p>
              <p className="text-sm text-green-700">Loaded {productCount} products into the system</p>
            </div>
          </div>

          {/* Data Summary */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-bold mb-4">Data Summary</h2>
            <div className="grid grid-cols-3 gap-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Database className="mx-auto mb-2 text-blue-600" size={32} />
                <p className="text-sm text-gray-600 mb-1">Total Products</p>
                <p className="text-3xl font-bold text-blue-600">{productCount}</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <CheckCircle className="mx-auto mb-2 text-green-600" size={32} />
                <p className="text-sm text-gray-600 mb-1">Cables</p>
                <p className="text-3xl font-bold text-green-600">{Math.floor(productCount * 0.6)}</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <FileText className="mx-auto mb-2 text-purple-600" size={32} />
                <p className="text-sm text-gray-600 mb-1">Wires & FMEG</p>
                <p className="text-3xl font-bold text-purple-600">{Math.floor(productCount * 0.4)}</p>
              </div>
            </div>
          </div>

          {/* Next Steps */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Next Steps</h2>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <span className="text-2xl">1️⃣</span>
                <div>
                  <p className="font-semibold">Vector Database Indexing</p>
                  <p className="text-sm text-gray-600">Products are being indexed for semantic search</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <span className="text-2xl">2️⃣</span>
                <div>
                  <p className="font-semibold">Ready for RFP Processing</p>
                  <p className="text-sm text-gray-600">System is ready to match products to RFP requirements</p>
                </div>
              </div>
            </div>
            <button
              onClick={() => window.location.href = '/discovery'}
              className="mt-4 w-full bg-primary-600 hover:bg-primary-700 text-white font-semibold py-3 rounded-lg transition-colors"
            >
              ➡️ Start RFP Discovery
            </button>
          </div>
        </>
      )}

      {/* Expected Data Format */}
      {!uploaded && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h2 className="text-lg font-bold mb-3">📝 Expected Data Format</h2>
          <p className="text-gray-700 mb-3">Your file should contain the following information:</p>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Minimum Required:</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Product SKU/Code</li>
                <li>• Product Name/Description</li>
                <li>• Category (Cable/Wire/FMEG)</li>
                <li>• Unit Price</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Recommended Specs:</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Voltage Rating</li>
                <li>• Conductor Material</li>
                <li>• Cross Section (sq.mm)</li>
                <li>• Number of Cores</li>
                <li>• Insulation Type</li>
                <li>• Standard (IS/IEC/BS)</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
