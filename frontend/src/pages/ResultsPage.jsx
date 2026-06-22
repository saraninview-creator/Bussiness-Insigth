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
  const params = useParams();

  // Auto-scroll
  useEffect(() => {
    endRef.current?.scrollIntoView({behavior: 'smooth'});
  }, [messages, open]);

  const handleSend = async (text) => {
    if (!text.trim()) return;
    const userMsg = {user: true, text};
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    
    const botMsgId = Date.now();
    setMessages(prev => [...prev, {user: false, text: '', id: botMsgId}]);

    try {
      const response = await fetch(`${API_URL}/api/chat/${params.jobId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text }),
      });

      if (!response.body) throw new Error('No response body');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamedText = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const raw = decoder.decode(value);
        const lines = raw.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              streamedText += data.chunk;
              setMessages(prev => prev.map(m => 
                m.id === botMsgId ? { ...m, text: streamedText } : m
              ));
            } catch (e) {}
          }
        }
      }
    } catch (err) {
      console.error(err);
    }
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
  const baseCharts = useMemo(() => findings.filter(f => f.chart_type === 'bar' && f.chart_data), [findings]);
  if (baseCharts.length === 0) return null;
  const [multipliers, setMultipliers] = useState({});

  useEffect(() => {
    const init = {};
    baseCharts.forEach((c, cIdx) => {
      c.chart_data.labels.forEach((label, lIdx) => {
        init[`${cIdx}_${lIdx}`] = 1.0;
      });
    });
    setMultipliers(init);
  }, [baseCharts]);

  return (
    <div className="whatif-container">
      <div className="whatif-header">
        <div>
          <h3 style={{fontSize: 18, marginBottom: 4}}>What-If Simulator</h3>
          <p style={{color: 'var(--text-2)', fontSize: 13}}>Adjust values to see impacts</p>
        </div>
      </div>
      <div className="whatif-grid">
        {baseCharts.map((chart, cIdx) => {
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
              <h4 style={{fontSize: 14, marginBottom: 16}}>{chart.chart_data.x_label || 'Category'} Adjustments</h4>
              <div className="whatif-recharts-container" style={{height: 200, marginBottom: 24}}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={simData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false}/>
                    <XAxis dataKey="name" tick={{fill: 'var(--text-3)', fontSize: 10}} />
                    <YAxis tick={{fill: 'var(--text-3)', fontSize: 10}} />
                    <Tooltip contentStyle={{background: '#161616', border: '1px solid #2a2a2a', borderRadius: 8}} />
                    <Bar dataKey="value" fill="var(--insight)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
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
        <span className="finding-chart-badge">{CHART_LABELS[finding.chart_type] || finding.chart_type}</span>
      </div>
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
  const [activeTab, setActiveTab] = useState('insight');
  const [videoStatus, setVideoStatus] = useState('not_started');
  const [videoProgress, setVideoProgress] = useState(0);

  useEffect(() => {
    if (!jobId) return;
    fetch(`${API_URL}/result/${jobId}`)
      .then(r => {
        if (!r.ok) throw new Error(`Status ${r.status}`);
        return r.json();
      })
      .then(data => { 
        setResult(data); 
        setLoading(false);
        if (data.video_url) setVideoStatus('completed');
      })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [jobId]);

  useEffect(() => {
    let interval;
    if (videoStatus === 'processing') {
      interval = setInterval(async () => {
        try {
          const r = await fetch(`${API_URL}/api/video/status/${jobId}`);
          const data = await r.json();
          if (data.status === 'completed') {
            setVideoStatus('completed');
            setResult(prev => ({...prev, video_url: data.url}));
            clearInterval(interval);
          } else if (data.status === 'error') {
            setVideoStatus('error');
            clearInterval(interval);
          } else if (data.progress) {
            setVideoProgress(data.progress);
          }
        } catch (e) { console.error(e); }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [videoStatus, jobId]);

  const triggerGeneration = () => {
    setVideoStatus('processing');
    fetch(`${API_URL}/api/video/generate/${jobId}`, {method:'POST'});
  };

  const interactions = (items, label) => (
    <div className="findings-col-content">
      {items.length === 0
        ? <div className="empty-col">No {label.toLowerCase()} found in this audit.</div>
        : <div className="findings-tab-grid">{items.map(f => <FindingCard key={f.id} finding={f} />)}</div>
      }
    </div>
  );

  if (loading) return <div className="error-page"><div className="spinner" /><p>Loading results…</p></div>;
  if (error) return <div className="error-page"><h2>Error</h2><p>{error}</p><button onClick={() => navigate('/')}>← Back</button></div>;
  if (!result) return null;

  const findings = result.findings ?? [];
  const insights = findings.filter(f => f.type === 'insight');
  const problems = findings.filter(f => f.type === 'problem');
  const suggestions = findings.filter(f => f.type === 'suggestion');

  return (
    <div className="results-page">
      <div>
        <div className="results-section-title" style={{display:'flex', justifyContent:'space-between'}}>
          <span>Generated Video</span>
          {!result.video_url && videoStatus === 'not_started' && (
            <button className="chatbot-btn" onClick={triggerGeneration} style={{padding:'4px 12px', fontSize:12, borderRadius:4}}>
              Generate Insight Video
            </button>
          )}
        </div>
        <div className="video-wrapper">
          {result.video_url ? (
            <video ref={videoRef} className="video-player" src={`${API_URL}${result.video_url}`} controls autoPlay={false} />
          ) : (
            <div style={{background: '#0a0a0a', height: 380, display: 'flex', flexDirection:'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-3)', borderRadius: 10, border: '1px solid var(--border)', gap: 12}}>
              {videoStatus === 'processing' ? (
                <>
                  <div className="spinner" />
                  <div>Synthesizing Storyboard... {videoProgress}%</div>
                </>
              ) : "Video not generated."}
            </div>
          )}
        </div>
      </div>

      <div className="findings-section" style={{marginTop: 32}}>
        <div className="results-section-header" style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
          <div className="results-section-title">Structural Audit</div>
          <div className="tab-switcher" style={{display:'flex', gap: 8}}>
             <button className={`tab-btn ${activeTab === 'insight' ? 'active' : ''}`} onClick={() => setActiveTab('insight')}>INSIGHTS</button>
             <button className={`tab-btn ${activeTab === 'problem' ? 'active' : ''}`} onClick={() => setActiveTab('problem')}>PROBLEMS</button>
             <button className={`tab-btn ${activeTab === 'suggestion' ? 'active' : ''}`} onClick={() => setActiveTab('suggestion')}>SUGGESTIONS</button>
          </div>
        </div>
        <div className="active-tab-content" style={{marginTop: 16}}>
          {activeTab === 'insight' && interactions(insights, 'Insights')}
          {activeTab === 'problem' && interactions(problems, 'Problems')}
          {activeTab === 'suggestion' && interactions(suggestions, 'Suggestions')}
        </div>
      </div>

      <WhatIfSimulator findings={findings} jobId={jobId} />
      <Chatbot findings={findings} />
    </div>
  );
}
