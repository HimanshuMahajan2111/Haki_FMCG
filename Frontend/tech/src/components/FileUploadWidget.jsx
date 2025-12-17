 
import React, { useState, useRef } from 'react';
import { useFileUpload } from '../hooks/useRFPApi';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';

export default function FileUploadWidget({ onUploadComplete }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const inputRef = useRef(null);

  const { uploadFile, isUploading, error } = useFileUpload();

  // Handle drag events
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  // Handle drop
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  // Handle file input change
  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  // Handle file selection
  const handleFileSelect = (file) => {
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }

    // Validate file type (documents only)
    const allowedTypes = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'text/plain', 'application/vnd.ms-excel',
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    
    if (!allowedTypes.includes(file.type)) {
      alert('Only PDF, Word, Excel, and text files are allowed');
      return;
    }

    setSelectedFile(file);
    setUploadResult(null);
  };

  // Handle upload
  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const result = await uploadFile(selectedFile);
      setUploadResult(result);
      
      if (onUploadComplete) {
        onUploadComplete(result);
      }

      // Clear selection after successful upload
      setTimeout(() => {
        setSelectedFile(null);
        setUploadResult(null);
      }, 3000);
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  // Handle clear
  const handleClear = () => {
    setSelectedFile(null);
    setUploadResult(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">Upload RFP Document</h2>

      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 bg-white hover:border-gray-400'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          onChange={handleChange}
          accept=".pdf,.doc,.docx,.txt,.xls,.xlsx"
          className="hidden"
        />

        {!selectedFile ? (
          <>
            <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              Drop your file here, or{' '}
              <button
                onClick={() => inputRef.current?.click()}
                className="text-blue-600 hover:text-blue-700 underline"
              >
                browse
              </button>
            </p>
            <p className="text-sm text-gray-500">
              Supported formats: PDF, Word, Excel, Text (max 10MB)
            </p>
          </>
        ) : (
          <SelectedFileView
            file={selectedFile}
            onClear={handleClear}
            onUpload={handleUpload}
            isUploading={isUploading}
          />
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Upload Failed</p>
            <p className="text-sm text-red-600 mt-1">{error.message}</p>
          </div>
        </div>
      )}

      {/* Success Display */}
      {uploadResult && (
        <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-green-800">Upload Successful!</p>
            <p className="text-sm text-green-600 mt-1">
              File ID: <span className="font-mono">{uploadResult.file_id}</span>
            </p>
            {uploadResult.url && (
              <a 
                href={uploadResult.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-700 underline mt-1 inline-block"
              >
                View uploaded file
              </a>
            )}
          </div>
        </div>
      )}

      {/* Usage Guidelines */}
      <div className="mt-6 bg-blue-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">Upload Guidelines</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Upload RFP documents in PDF, Word, Excel, or text format</li>
          <li>• Maximum file size: 10MB</li>
          <li>• Files are automatically scanned and processed</li>
          <li>• Ensure document contains clear product requirements</li>
        </ul>
      </div>
    </div>
  );
}

// Selected File View Component
function SelectedFileView({ file, onClear, onUpload, isUploading }) {
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (type) => {
    if (type.includes('pdf')) return '📄';
    if (type.includes('word')) return '📝';
    if (type.includes('excel') || type.includes('spreadsheet')) return '📊';
    return '📎';
  };

  return (
    <div className="space-y-4">
      {/* File Info */}
      <div className="flex items-start gap-4 bg-gray-50 p-4 rounded-lg">
        <div className="text-4xl">{getFileIcon(file.type)}</div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 truncate">{file.name}</p>
          <p className="text-sm text-gray-600 mt-1">
            {formatFileSize(file.size)} • {file.type.split('/')[1].toUpperCase()}
          </p>
        </div>
        <button
          onClick={onClear}
          disabled={isUploading}
          className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Upload Progress (when uploading) */}
      {isUploading && (
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Uploading...</span>
            <span className="font-medium">Processing</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '70%' }}></div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={onUpload}
          disabled={isUploading}
          className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {isUploading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Upload File
            </>
          )}
        </button>
        <button
          onClick={onClear}
          disabled={isUploading}
          className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
