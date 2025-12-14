import React, { useState, useRef } from 'react';

const ActiveRFPs = () => {
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef(null);
  const [uploadStatusText, setUploadStatusText] = useState('Ready to upload.');


  const handleFileChange = (event) => {
    if (event.target.files.length > 0) {
      const selectedFile = event.target.files[0];
      setFile(selectedFile);
      setUploadProgress(0); 
      setUploadStatusText(`Selected: ${selectedFile.name}`);
    } else {
      setFile(null);
      setUploadStatusText('Ready to upload.');
    }
  };


  const startUploadSimulation = () => {
    if (!file || isUploading) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatusText('Uploading...');

    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadProgress(progress);

      if (progress >= 100) {
        clearInterval(interval);
        setIsUploading(false);
        setUploadStatusText(`Upload Complete: ${file.name}`);

      }
    }, 200); 
  };

  return (
    <div className="tab-content upload-section">
      <h3 className="upload-title">T File Upload</h3>

      <div className="drop-zone-wrapper">
        <div className="file-input-wrapper">
         
          <input
            type="file"
            id="file-upload"
            ref={fileInputRef}
            onChange={handleFileChange}
            disabled={isUploading}
          />

          <label htmlFor="file-upload" className="upload-drop-zone">
            <span className="upload-icon">📁</span>
            <p style={{ margin: '0', fontSize: '16px' }}>Drag & drop your file here, or click to select.</p>
            {file && <p className="selected-file-name">Selected: {file.name}</p>}
          </label>
        </div>
      </div>

      {file && (
        <div className="full-width-progress-bar-container">
          <div
            className="full-width-progress-bar-fill"
            style={{ width: `${uploadProgress}%` }}
          ></div>
        </div>
      )}

      <button
        className="start-upload-button"
        onClick={startUploadSimulation}
        disabled={!file || isUploading || uploadProgress === 100}
      >
        {isUploading ? 'Uploading...' : 'Start Upload'}
      </button>

      {file && <p className="upload-status">{uploadStatusText}</p>}
    </div>
  );
};

export default ActiveRFPs;