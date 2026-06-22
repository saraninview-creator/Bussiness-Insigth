// Line chart scene — animated draw-in of an SVG polyline
import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneShell} from '../components/SceneShell';
import {ACCENT_FOR, COLORS, Finding} from '../types';

interface LineSceneProps {
  finding: Finding;
}

export function LineScene({finding}: LineSceneProps) {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const accent = ACCENT_FOR[finding.type];
  const cd = finding.chart_data as {
    labels: string[];
    series: number[];
    highlight_idx: number;
    y_label: string;
    pct_change: number;
  };

  const labels = cd.labels ?? [];
  const series = cd.series ?? [];
  const highlightIdx = cd.highlight_idx ?? 0;

  const W = 860, H = 320;
  const pad = {top: 20, right: 20, bottom: 40, left: 56};
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;

  const minVal = Math.min(...series);
  const maxVal = Math.max(...series);
  const range = maxVal - minVal || 1;

  const points = series.map((v, i) => ({
    x: pad.left + (i / Math.max(series.length - 1, 1)) * innerW,
    y: pad.top + innerH - ((v - minVal) / range) * innerH,
  }));

  const polylineStr = points.map(p => `${p.x},${p.y}`).join(' ');
  const totalLen = 1200; // approximate path length

  // Animate stroke-dashoffset from totalLen → 0
  const drawProgress = interpolate(
    frame,
    [fps * 0.3, fps * 1.8],
    [0, 1],
    {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'}
  );
  const strokeDashoffset = totalLen * (1 - drawProgress);

  // Highlight dot appears after line is drawn
  const dotOpacity = interpolate(frame, [fps * 1.8, fps * 2.0], [0, 1], {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'});

  // Y-axis labels
  const yTicks = 4;
  const yTickValues = Array.from({length: yTicks + 1}, (_, i) => minVal + (range * i) / yTicks);

  // X-axis: show at most 6 labels
  const xStep = Math.max(1, Math.floor(labels.length / 6));
  const xTickIndices = labels.reduce((acc: number[], _, i) => {
    if (i % xStep === 0) acc.push(i);
    return acc;
  }, []);

  const pct = cd.pct_change ?? 0;
  const pctColor = pct >= 0 ? accent : '#ff6b6b';

  return (
    <SceneShell findingType={finding.type} captionText={finding.text}>
      {/* Stat number top-right */}
      <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: 8}}>
        <div style={{
          fontSize: 32,
          fontWeight: 800,
          color: pctColor,
          letterSpacing: -1,
        }}>
          {pct >= 0 ? '+' : ''}{pct.toFixed(1)}%
        </div>
      </div>

      <svg width={W} height={H} style={{display: 'block', overflow: 'visible'}}>
        {/* Y-axis lines */}
        {yTickValues.map((val, i) => {
          const y = pad.top + innerH - ((val - minVal) / range) * innerH;
          return (
            <g key={i}>
              <line x1={pad.left} y1={y} x2={pad.left + innerW} y2={y}
                stroke={COLORS.gridLine} strokeWidth={1} />
              <text x={pad.left - 8} y={y + 4} textAnchor="end"
                fill={COLORS.textMuted} fontSize={11}>
                {val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* X-axis labels */}
        {xTickIndices.map(i => (
          <text key={i} x={points[i]?.x ?? 0} y={H - 8} textAnchor="middle"
            fill={COLORS.textMuted} fontSize={10}>
            {labels[i]?.slice(5) ?? ''}
          </text>
        ))}

        {/* Animated polyline */}
        <polyline
          points={polylineStr}
          fill="none"
          stroke={accent}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={totalLen}
          strokeDashoffset={strokeDashoffset}
        />

        {/* Area fill (subtle) */}
        {points.length > 0 && (
          <polygon
            points={`${points[0].x},${pad.top + innerH} ${polylineStr} ${points[points.length - 1].x},${pad.top + innerH}`}
            fill={accent}
            fillOpacity={0.05}
          />
        )}

        {/* Highlight dot */}
        {points[highlightIdx] && (
          <circle
            cx={points[highlightIdx].x}
            cy={points[highlightIdx].y}
            r={6}
            fill={accent}
            opacity={dotOpacity}
          />
        )}
      </svg>
    </SceneShell>
  );
}
