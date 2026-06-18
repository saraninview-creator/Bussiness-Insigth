import React, {useEffect, useRef, useState, useMemo} from 'react';
import {useParams, useNavigate} from 'react-router-dom';
import {BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid} from 'recharts';

const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

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

/* ── Chatbot Component ───────────────────────────────────────── */
function Chatbot({findings}) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {user: false, text: "Hi! I'm the DataNarrate bot. Ask me anything about your analysis."}
  ]);
  const [input, setInput] = useState('');
  const endRef = useRef(null);

  // Auto-scroll
  useEffect(() => {
    endRef.current?.scrollIntoView({behavior: 'smooth'});
  }, [messages, open]);

  const allText = useMemo(() => findings.map(f => f.text).join(' ').toLowerCase(), [findings]);
  
  const handleSend = (text) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, {user: true, text}]);
    setInput('');
    
    // Simulate delay
    setTimeout(() => {
      const q = text.toLowerCase();
      let response = '';

      if (q.includes('problem') || q.includes('issue')) {
        const probs = findings.filter(f => f.type === 'problem');
        response = probs.length 
          ? "Here are the main problems found: " + probs.map(p => p.text).join(" ")
          : "I didn't find any major problems in this dataset.";
      } else if (q.includes('growth') || q.includes('opportunity') || q.includes('suggestion')) {
        const suggs = findings.filter(f => f.type === 'suggestion');
        response = suggs.length 
          ? "Here are some growth opportunities: " + suggs.map(s => s.text).join(" ")
          : "No specific suggestions were generated.";
      } else if (q.includes('insight') || q.includes('top')) {
        const ins = findings.filter(f => f.type === 'insight');
        response = ins.length 
          ? "Top insight: " + ins[0].text
          : "No core insights were found.";
      } else {
        // Keyword matching
        const words = q.split(' ').filter(w => w.length > 3);
        const match = findings.find(f => words.some(w => f.text.toLowerCase().includes(w)));
        if (match) {
          response = `I found this related to your question: ${match.text}`;
        } else {
          // Extract column names if possible (from meta or text)
          const cols = [...new Set(findings.map(f => f.meta?.col || f.meta?.col1 || '').filter(Boolean))];
          response = `I couldn't find an exact match for that. Try asking about your data columns: ${cols.length ? cols.join(', ') : 'the general metrics'}.`;
        }
      }
      setMessages(prev => [...prev, {user: false, text: response}]);
    }, 600);
  };

  if (!open) {
    return (
      <div className="chatbot-toggle" onClick={() => setOpen(true)}>
        🤖
      </div>
    );
  }

  return (
    <div className="chatbot-panel">
      <div className="chatbot-header">
        <div style={{display: 'flex', alignItems: 'center', gap: 8}}>
          <span style={{fontSize: 18}}>🤖</span> DataNarrate Bot
        </div>
        <button onClick={() => setOpen(false)} style={{background: 'transparent', border: 'none', color: 'var(--text-3)'}}>✕</button>
      </div>
      <div className="chatbot-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.user ? 'user' : 'bot'}`}>{m.text}</div>
        ))}
        {messages.length === 1 && (
          <div className="chat-chips">
            <div className="chat-chip" onClick={() => handleSend("What are the biggest problems?")}>What are the biggest problems?</div>
            <div className="chat-chip" onClick={() => handleSend("Show me growth opportunities")}>Show me growth opportunities</div>
            <div className="chat-chip" onClick={() => handleSend("Explain the top insight")}>Explain the top insight</div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="chatbot-input">
        <input 
          type="text" 
          value={input} 
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend(input)}
          placeholder="Ask about your data..."
        />
        <button className="chatbot-btn" onClick={() => handleSend(input)}>Send</button>
      </div>
    </div>
  );
}

/* ── What-If Simulator Component ─────────────────────────────── */
function WhatIfSimulator({findings, jobId}) {
  // Extract all bar charts to use as our param baseline (since they have discrete categories and values)
  const baseCharts = useMemo(() => findings.filter(f => f.chart_type === 'bar' && f.chart_data), [findings]);
  
  if (baseCharts.length === 0) return null; // Only show if we have bar charts to simulate

  // State to hold the multipliers. Default is 1.0
  const [multipliers, setMultipliers] = useState({});

  // Initialize multipliers
  useEffect(() => {
    const init = {};
    baseCharts.forEach((c, cIdx) => {
      c.chart_data.labels.forEach((label, lIdx) => {
        init[`${cIdx}_${lIdx}`] = 1.0;
      });
    });
    setMultipliers(init);
  }, [baseCharts]);

  const handleReset = () => {
    const init = {};
    Object.keys(multipliers).forEach(k => init[k] = 1.0);
    setMultipliers(init);
  };

  const handleGenerate = () => {
    // In a real app, this would send multipliers back to the /analyze endpoint.
    alert("In a full implementation, this would send the modified dataset to the backend and generate a new Remotion video!");
  };

  return (
    <div className="whatif-container">
      <div className="whatif-header">
        <div>
          <h3 style={{fontSize: 18, marginBottom: 4}}>What-If Simulator</h3>
          <p style={{color: 'var(--text-2)', fontSize: 13}}>Adjust values to see how they impact your charts</p>
        </div>
        <div style={{display: 'flex', gap: 12}}>
          <button className="btn-ghost" onClick={handleReset}>Reset All</button>
          <button className="chatbot-btn" onClick={handleGenerate} style={{padding: '8px 16px'}}>Generate What-If Video</button>
        </div>
      </div>

      <div className="whatif-grid">
        {baseCharts.map((chart, cIdx) => {
          // Re-calculate the chart data
          const simData = chart.chart_data.labels.map((label, lIdx) => {
            const m = multipliers[`${cIdx}_${lIdx}`] ?? 1.0;
            return {
              name: label,
              original: chart.chart_data.values[lIdx],
              value: chart.chart_data.values[lIdx] * m,
              multiplier: m
            };
          });

          return (
            <div key={cIdx}>
              <h4 style={{fontSize: 14, color: 'var(--text)', marginBottom: 16, borderBottom: '1px solid var(--border)', paddingBottom: 8}}>
                {chart.chart_data.x_label || 'Category'} Adjustments
              </h4>
              <div className="whatif-recharts-container" style={{marginBottom: 24}}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={simData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false}/>
                    <XAxis dataKey="name" tick={{fill: 'var(--text-3)', fontSize: 12}} axisLine={false} tickLine={false} />
                    <YAxis tick={{fill: 'var(--text-3)', fontSize: 12}} axisLine={false} tickLine={false} />
                    <Tooltip 
                      contentStyle={{background: '#161616', border: '1px solid #2a2a2a', borderRadius: 8, color: '#fff'}}
                      formatter={(val) => Number(val).toFixed(2)}
                    />
                    <Bar dataKey="value" fill="var(--insight)" radius={[4, 4, 0, 0]} isAnimationActive={true} animationDuration={300} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{display: 'flex', flexDirection: 'column', gap: 16}}>
                {simData.map((d, lIdx) => {
                  const pct = Math.round((d.multiplier - 1) * 100);
                  let impactClass = 'neutral';
                  let impactText = 'No Change';
                  if (pct > 0) { impactClass = 'positive'; impactText = `↑ +${pct}% Positive Impact`; }
                  else if (pct < 0) { impactClass = 'negative'; impactText = `↓ ${pct}% Negative Impact`; }

                  return (
                    <div key={lIdx} className="whatif-slider-group">
                      <div className="whatif-label-row">
                        <span>{d.name} <span style={{color: 'var(--text-3)', marginLeft: 8}}>(orig: {Number(d.original).toFixed(1)})</span></span>
                        <span className={`whatif-impact ${impactClass}`}>{impactText}</span>
                      </div>
                      <input 
                        type="range" 
                        min="0.5" 
                        max="1.5" 
                        step="0.05"
                        value={d.multiplier}
                        onChange={(e) => setMultipliers(prev => ({...prev, [`${cIdx}_${lIdx}`]: parseFloat(e.target.value)}))}
                        className="whatif-slider"
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Standard Finding Card / Grid ────────────────────────────── */
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

      {/* What-If Simulator */}
      <WhatIfSimulator findings={findings} jobId={jobId} />

      {/* Floating Chatbot */}
      <Chatbot findings={findings} />
    </div>
  );
}
