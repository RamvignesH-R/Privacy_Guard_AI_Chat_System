import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Download, Copy, AlertCircle, CheckCircle, Flag } from 'lucide-react';
import './DocumentMasker.css';

const DocumentMasker = ({ onFlag }) => {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  const [copied, setCopied] = useState(false);
  const [outputTab, setOutputTab] = useState('masked'); // 'masked' or 'original'

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setError('');
    }
  };

  const handleMask = async () => {
    if (!file) return;
    setIsLoading(true);
    setError('');
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:5000/mask', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (!response.ok || data.error) {
        throw new Error(data.error || 'Failed to process document');
      }

      setResult(data);
    } catch (err) {
      setError(err.message || 'Error connecting to Document Masker backend. Ensure it is running on port 5000.');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (result && result.masked) {
      navigator.clipboard.writeText(result.masked);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const downloadText = () => {
    if (result && result.masked) {
      const blob = new Blob([result.masked], { type: 'text/plain' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `masked_${file?.name || 'document'}.txt`;
      a.click();
    }
  };

  const highlightTokens = (text) => {
    const parts = text.split(/(\[[A-Z][A-Z_]+\])/g);
    return parts.map((part, i) => {
      if (part.match(/^\[[A-Z][A-Z_]+\]$/)) {
        return <span key={i} className="doc-pii-token">{part}</span>;
      }
      return part;
    });
  };

  return (
    <div className="doc-masker-container">
      <div className="doc-masker-grid">
        {/* Upload Panel */}
        <div className="doc-panel">
          <div className="doc-panel-header">
            <h3>Document Upload</h3>
          </div>
          <div className="doc-panel-body">
            <div 
              className={`drop-zone ${file ? 'has-file' : ''}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current.click()}
            >
              <UploadCloud size={32} className="drop-icon" />
              <div className="drop-text">
                {file ? file.name : "Click to browse or drag a file here"}
              </div>
              <div className="drop-hint">TXT | PDF | PNG | DOCX</div>
              <input 
                type="file" 
                ref={fileInputRef}
                style={{ display: 'none' }}
                accept=".txt,.pdf,.png,.docx,.jpg,.jpeg"
                onChange={handleFileChange}
              />
            </div>

            <button 
              className="mask-btn" 
              onClick={handleMask}
              disabled={!file || isLoading}
            >
              {isLoading ? <div className="loader" style={{margin: 'auto'}} /> : "Mask Document"}
            </button>

            {error && (
              <div className="doc-error">
                <AlertCircle size={14} />
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>

        {/* Results Panel */}
        <div className="doc-panel result-panel">
          <div className="doc-panel-header">
            <h3>{outputTab === 'masked' ? 'Masked Output' : 'Original Document'}</h3>
            {result && (
              <div className="doc-actions">
                <div className="toggle-container" style={{ marginRight: '10px' }}>
                  <span 
                    style={{ padding: '2px 8px', borderRadius: '100px', cursor: 'pointer', background: outputTab === 'original' ? 'var(--cyan-dim)' : 'transparent', color: outputTab === 'original' ? 'var(--cyan)' : 'var(--text-muted)' }}
                    onClick={() => setOutputTab('original')}
                  >Original</span>
                  <span 
                    style={{ padding: '2px 8px', borderRadius: '100px', cursor: 'pointer', background: outputTab === 'masked' ? 'var(--cyan-dim)' : 'transparent', color: outputTab === 'masked' ? 'var(--cyan)' : 'var(--text-muted)' }}
                    onClick={() => setOutputTab('masked')}
                  >Masked</span>
                </div>
                {onFlag && (
                  <button className="action-btn flag-btn" onClick={() => onFlag(result.original)} title="Flag Bad Masking for Retraining" style={{ borderColor: 'var(--red)', color: 'var(--red)' }}>
                    <Flag size={14} />
                  </button>
                )}
                <button className="action-btn" onClick={copyToClipboard} title="Copy">
                  {copied ? <CheckCircle size={14} /> : <Copy size={14} />}
                </button>
                <button className="action-btn" onClick={downloadText} title="Download">
                  <Download size={14} />
                </button>
              </div>
            )}
          </div>
          
          <div className="doc-panel-body result-body">
            {!result && !isLoading && (
              <div className="doc-placeholder">
                <FileText size={32} />
                <p>Upload a document to see the redacted output here.</p>
              </div>
            )}

            {isLoading && (
              <div className="doc-placeholder">
                <div className="loader" style={{ width: 30, height: 30, borderWidth: 3 }} />
                <p style={{ marginTop: 15 }}>Processing document... This may take a moment.</p>
              </div>
            )}

            {result && (
              <>
                {outputTab === 'masked' && (
                  <div className="stats-container">
                    <div className="stat-pill total">
                      <span>{result.total_redactions}</span> total redactions
                    </div>
                    {Object.entries(result.entities_found || {}).sort((a, b) => b[1] - a[1]).map(([key, count]) => (
                      <div key={key} className="stat-pill">
                        <span>{count}</span> {key.replace(/_/g, ' ')}
                      </div>
                    ))}
                  </div>
                )}
                <div className="doc-text-output">
                  {outputTab === 'masked' ? highlightTokens(result.masked) : result.original}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentMasker;
