import React, {useEffect, useState} from 'react';
import {useParams, useNavigate} from 'react-router-dom';

const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '');

const STAGES = [
  {key: 'parsing',          label: 'Parsing',           desc: 'Loading and reading your data file'},
  {key: 'profiling',        label: 'Profiling',          desc: 'Computing statistics and detecting patterns'},
  {key: 'scripting',        label: 'Scripting',          desc: 'Generating findings and narration script'},
  {key: 'rendering_charts', label: 'Rendering Charts',  desc: 'Preparing chart data for each scene'},
  {key: 'generating_audio', label: 'Generating Audio',  desc: 'Synthesizing narration with text-to-speech'},
  {key: 'assembling_video', label: 'Assembling Video',  desc: 'Rendering animated scenes into MP4'},
  {key: 'done',             label: 'Done',              desc: 'Your insight video is ready'},
];

function stageIndex(status) {
  const idx = STAGES.findIndex(s => s.key === status);
  return idx === -1 ? 0 : idx;
}

export default function ProcessingPage() {
  const {jobId} = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('queued');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!jobId) return;
    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/status/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();
        setStatus(data.status);
        if (data.status === 'done') navigate(`/results/${jobId}`);
        if (data.status === 'error') setErrorMsg(data.error || 'Pipeline failed');
      } catch (e) {
        console.error('Status poll error:', e);
      }
    };

    poll();
    const timer = setInterval(poll, 2500);
    return () => clearInterval(timer);
  }, [jobId, navigate]);

  if (errorMsg) {
    return (
      <div className="error-page">
        <h2>⚠ Pipeline Error</h2>
        <p>{errorMsg}</p>
        <button className="btn-ghost" onClick={() => navigate('/')}>
          ← Try Again
        </button>
      </div>
    );
  }

  const activeIdx = stageIndex(status);

  return (
    <div className="processing-page">
      <div className="processing-header">
        <h2>Analysing Your Data</h2>
        <p>This usually takes 1–3 minutes. You can leave this tab open.</p>
      </div>

      <div className="pipeline-stages">
        {STAGES.map((stage, i) => {
          const isCompleted = i < activeIdx;
          const isActive    = i === activeIdx;
          const isPending   = i > activeIdx;
          let cls = 'stage-item';
          if (isCompleted) cls += ' completed';
          else if (isActive) cls += ' active';
          else cls += ' pending';

          return (
            <div key={stage.key} className={cls}>
              <div className="stage-dot">
                {isCompleted ? '✓' : isActive ? '' : <span style={{color:'var(--text-3)', fontSize:11}}>{i+1}</span>}
              </div>
              <div className="stage-info">
                <div className="stage-name">{stage.label}</div>
                {(isCompleted || isActive) && (
                  <div className="stage-desc">{stage.desc}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="processing-job-id">Job ID: {jobId}</div>
    </div>
  );
}
