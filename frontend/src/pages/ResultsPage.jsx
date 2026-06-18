import React, {useEffect, useRef, useState} from 'react';
import {useParams, useNavigate} from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || '';

const CHART_LABELS = {
  line: 'Line Chart',
  bar: 'Bar Chart',
  donut: 'Donut Chart',
  histogram: 'Histogram',
  scatter: 'Scatter Plot',
  stat_card: 'Stat Card',
};

const ICONS = {
  insight: '↗',
  problem: '⚠',
  suggestion: '→',
};

function FindingCard({finding}) {
  return (
    <div className="finding-card">
      <div className="finding-icon">{ICONS[finding.type]}</div>
      <div>
        <div className="finding-text">{finding.text}</div>
        <span className="finding-chart-badge">
          {CHART_LABELS[finding.chart_type] || finding.chart_type}
        </span>
      </div>
    </div>
  );
}

function FindingsColumn({type, label, findings}) {
  return (
    <div className={`findings-column col-${type}`}>
      <div className="findings-col-header">
        <span className="findings-col-title">{ICONS[type]} {label}</span>
        <span className="findings-col-count">{findings.length}</span>
      </div>
      {findings.length === 0
        ? <div className="empty-col">No {label.toLowerCase()} found</div>
        : findings.map(f => <FindingCard key={f.id} finding={f} />)
      }
    </div>
  );
}

export default function ResultsPage() {
  const {jobId} = useParams();
  const navigate = useNavigate();
  const videoRef = useRef();
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) return;
    fetch(`${API_URL}/result/${jobId}`)
      .then(r => {
        if (!r.ok) throw new Error(`Status ${r.status}`);
        return r.json();
      })
      .then(data => { setResult(data); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [jobId]);

  const downloadVideo = () => {
    if (!result?.video_url) return;
    const a = document.createElement('a');
    a.href = result.video_url;
    a.download = `datnarrate-${jobId}.mp4`;
    a.click();
  };

  const downloadJson = () => {
    if (!result?.findings) return;
    const blob = new Blob([JSON.stringify(result.findings, null, 2)], {type: 'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `datnarrate-findings-${jobId}.json`;
    a.click();
  };

  if (loading) {
    return (
      <div className="error-page">
        <div className="spinner" style={{width:28, height:28}} />
        <p style={{color:'var(--text-2)'}}>Loading results…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-page">
        <h2>Unable to load results</h2>
        <p>{error}</p>
        <button className="btn-ghost" onClick={() => navigate('/')}>← New Analysis</button>
      </div>
    );
  }

  if (!result) return null;

  const findings = result.findings ?? [];
  const insights    = findings.filter(f => f.type === 'insight');
  const problems    = findings.filter(f => f.type === 'problem');
  const suggestions = findings.filter(f => f.type === 'suggestion');

  // Calculate full summary and total suggested timing
  const totalSeconds = findings.reduce((acc, f) => acc + (f.duration_seconds || f.estimated_duration_seconds || 0), 0);
  const fullSummaryText = findings.map(f => f.text).join(' ');

  return (
    <div className="results-page">
      {/* Video player */}
      <div>
        <div className="results-section-title">Generated Video</div>
        <div className="video-wrapper">
          {result.video_url ? (
            <video
              ref={videoRef}
              className="video-player"
              src={result.video_url}
              controls
              autoPlay={false}
            />
          ) : (
            <div style={{
              background: '#0a0a0a',
              height: 380,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-3)',
              borderRadius: 10,
              border: '1px solid var(--border)',
            }}>
              Video processing… check back shortly.
            </div>
          )}
        </div>
      </div>

      {/* Downloads */}
      <div className="download-bar">
        <button className="btn-ghost" onClick={downloadVideo} disabled={!result.video_url}>
          ↓ Download Video
        </button>
        <button className="btn-ghost" onClick={downloadJson}>
          ↓ Download Findings JSON
        </button>
        <button className="btn-ghost" onClick={() => navigate('/')}
          style={{marginLeft: 'auto'}}>
          + New Analysis
        </button>
      </div>

      {/* Summary Section */}
      <div style={{
        marginTop: 24,
        marginBottom: 24,
        padding: 16,
        background: 'var(--surface-2)',
        borderRadius: 8,
        border: '1px solid var(--border)'
      }}>
        <div style={{fontWeight: 600, marginBottom: 8, display: 'flex', justifyContent: 'space-between'}}>
          <span>Analyst Video Summary</span>
          <span style={{color: 'var(--text-3)'}}>Timing: {totalSeconds.toFixed(1)} seconds</span>
        </div>
        <p style={{color: 'var(--text-2)', lineHeight: 1.5, fontSize: 14}}>
          {fullSummaryText || "No findings summary available."}
        </p>
      </div>

      {/* Findings panel */}
      <div>
        <div className="results-section-title">Findings ({findings.length})</div>
        <div className="findings-grid">
          <FindingsColumn type="insight"    label="Insights"    findings={insights}    />
          <FindingsColumn type="problem"    label="Problems"    findings={problems}    />
          <FindingsColumn type="suggestion" label="Suggestions" findings={suggestions} />
        </div>
      </div>
    </div>
  );
}
