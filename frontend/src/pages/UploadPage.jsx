import React, {useState, useRef, useCallback} from 'react';
import {useNavigate} from 'react-router-dom';
import DarkVeil from '../components/DarkVeil';

const ALLOWED = ['.csv', '.xlsx', '.xls'];
// Dynamically retrieve the API base URL from the environment (Next.js or Vite).
const API_URL = (import.meta.env?.VITE_API_URL || import.meta.env?.NEXT_PUBLIC_API_URL || '').replace(/\/+$/, '');

export default function UploadPage({onJobCreated}) {
  const navigate = useNavigate();
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [explanationLevel, setExplanationLevel] = useState('concise_21s');
  const inputRef = useRef();

  const handleFile = useCallback(async (file) => {
    if (!file) return;
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      setError(`Unsupported file type. Please upload ${ALLOWED.join(', ')}`);
      return;
    }
    
    if (!API_URL) {
      setError("Backend API URL is not configured. Please set VITE_API_URL or NEXT_PUBLIC_API_URL in your environment.");
      return;
    }

    setError('');
    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('explanation_level', explanationLevel);
      
      const uploadWithRetry = async (retries = 2) => {
        for (let i = 0; i <= retries; i++) {
          try {
            // Explicitly use the POST method.
            // When using FormData as the body, fetch automatically sets the
            // Content-Type to multipart/form-data with the correct boundary string.
            const res = await fetch(`${API_URL}/upload`, {
              method: 'POST',
              body: form,
            });
            if (res.ok) return res;
            if (i === retries) return res; // return final failing response
          } catch (e) {
            if (i < retries) {
              setUploading("Waking up server...");
              await new Promise(r => setTimeout(r, 5000));
            } else {
              throw e;
            }
          }
        }
      };

      const res = await uploadWithRetry(2);

      if (!res.ok) {
        let errorMsg = `Upload failed (HTTP ${res.status})`;
        try {
          const data = await res.json();
          errorMsg = data.detail || errorMsg;
        } catch (_) {
          if (res.status === 405) {
            errorMsg = '405 Method Not Allowed — ensure the backend is running and CORS is configured, and your API URL is correct.';
          } else if (res.status === 503 || res.status === 502) {
            errorMsg = 'Service Unavailable — please wait a moment. The server may be waking up.';
          } else {
            errorMsg = `Server error (${res.status}). Ensure the backend is available at ${API_URL}.`;
          }
        }
        throw new Error(errorMsg);
      }
      const {job_id} = await res.json();
      onJobCreated?.({id: job_id, filename: file.name});
      navigate(`/processing/${job_id}`);
    } catch (e) {
      if (e instanceof TypeError && e.message.includes('fetch')) {
        setError('Cannot connect to the backend. It may be sleeping or down.');
      } else {
        setError(e.message);
      }
      setUploading(false);
    }
  }, [navigate, onJobCreated, explanationLevel]);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const onInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  return (
    <div className="upload-page" style={{position: 'relative', overflow: 'hidden'}}>
      {/* Animated WebGL background */}
      <div style={{position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none', opacity: 0.35}}>
        <DarkVeil speed={0.3} hueShift={220} noiseIntensity={0.04} warpAmount={0.3} />
      </div>

      <div className="upload-hero" style={{position: 'relative', zIndex: 1}}>
        <h1>Turn Your Data<br />Into a Story</h1>
        <p>
          Upload a CSV or Excel file and DataNarrate will automatically
          profile your data, discover key insights, and generate a
          narrated insight video — in minutes, no configuration needed.
        </p>
      </div>

      <div className="upload-preferences" style={{position: 'relative', zIndex: 1, marginBottom: '24px', display: 'flex', gap: '16px', justifyContent: 'center'}}>
        <label style={{color: 'var(--text-2)', display: 'flex', alignItems: 'center', gap: '8px'}}>
          <input 
            type="radio" 
            name="explanationLevel" 
            value="concise_21s" 
            checked={explanationLevel === 'concise_21s'} 
            onChange={(e) => setExplanationLevel(e.target.value)} 
          />
          Short Pitch (21s Cut)
        </label>
        <label style={{color: 'var(--text-2)', display: 'flex', alignItems: 'center', gap: '8px'}}>
          <input 
            type="radio" 
            name="explanationLevel" 
            value="full_detailed" 
            checked={explanationLevel === 'full_detailed'} 
            onChange={(e) => setExplanationLevel(e.target.value)} 
          />
          Detailed Analyst Review
        </label>
      </div>

      <div
        className={`drop-zone${dragging ? ' drag-active' : ''}`}
        style={{position: 'relative', zIndex: 1}}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={onInputChange}
          style={{display:'none'}}
        />
        {uploading ? (
          <>
            <div className="spinner" />
            <div className="drop-title">Uploading…</div>
          </>
        ) : (
          <>
            <div className="drop-icon">📂</div>
            <div className="drop-title">
              {dragging ? 'Drop your file here' : 'Drop your file, or click to browse'}
            </div>
            <div className="drop-subtitle">Supports CSV, Excel (.xlsx, .xls)</div>
            <div className="drop-types">
              {ALLOWED.map(t => <span key={t} className="type-badge">{t.toUpperCase()}</span>)}
            </div>
          </>
        )}
      </div>

      {error && <div className="upload-error" style={{position: 'relative', zIndex: 1}}>⚠ {error}</div>}

      <div style={{position: 'relative', zIndex: 1, color: 'var(--text-3)', fontSize: 12, textAlign: 'center', maxWidth: 420}}>
        Cloud-powered analysis backed by Supabase.
        Larger files (&gt;10 MB) may take a few extra minutes to render.
      </div>
    </div>
  );
}
