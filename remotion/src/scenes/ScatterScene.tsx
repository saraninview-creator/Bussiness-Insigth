// Scatter plot scene — animated dot appear for correlation findings
import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneShell} from '../components/SceneShell';
import {ACCENT_FOR, COLORS, Finding} from '../types';

export function ScatterScene({finding}: {finding: Finding}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const accent = ACCENT_FOR[finding.type];
  const cd = finding.chart_data as {
    points: {x: number; y: number}[];
    x_label: string;
    y_label: string;
    r: number;
    direction: string;
  };

  const points = cd.points ?? [];
  if (points.length === 0) return <SceneShell findingType={finding.type} captionText={finding.text}><div /></SceneShell>;

  const xs = points.map(p => p.x);
  const ys = points.map(p => p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const W = 860, H = 300;
  const pad = {top: 20, right: 30, bottom: 40, left: 60};
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;

  const toSvg = (x: number, y: number) => ({
    x: pad.left + ((x - minX) / Math.max(maxX - minX, 1)) * innerW,
    y: pad.top + innerH - ((y - minY) / Math.max(maxY - minY, 1)) * innerH,
  });

  // Dots pop in with staggered delay
  const dotProgress = (i: number) =>
    interpolate(frame, [fps * 0.2 + i * fps * 0.04, fps * 0.2 + i * fps * 0.04 + fps * 0.2], [0, 1], {
      extrapolateRight: 'clamp', extrapolateLeft: 'clamp',
    });

  // Trend line (basic regression)
  const n = points.length;
  const sumX = xs.reduce((a, b) => a + b, 0);
  const sumY = ys.reduce((a, b) => a + b, 0);
  const sumXY = points.reduce((a, p) => a + p.x * p.y, 0);
  const sumX2 = xs.reduce((a, b) => a + b * b, 0);
  const slope = (n * sumXY - sumX * sumY) / Math.max(n * sumX2 - sumX * sumX, 1e-9);
  const intercept = (sumY - slope * sumX) / n;

  const lineP1 = toSvg(minX, slope * minX + intercept);
  const lineP2 = toSvg(maxX, slope * maxX + intercept);
  const lineProgress = interpolate(frame, [fps * 1.2, fps * 1.8], [0, 1], {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'});

  return (
    <SceneShell findingType={finding.type} captionText={finding.text}>
      <div style={{marginBottom: 6, textAlign: 'right', color: accent, fontWeight: 700, fontSize: 22}}>
        r = {cd.r?.toFixed(2)}
        <span style={{color: COLORS.textMuted, fontSize: 13, fontWeight: 400, marginLeft: 8}}>
          ({cd.direction} correlation)
        </span>
      </div>
      <svg width={W} height={H} style={{display: 'block'}}>
        {/* Axes */}
        <line x1={pad.left} y1={pad.top} x2={pad.left} y2={pad.top + innerH}
          stroke={COLORS.border} strokeWidth={1} />
        <line x1={pad.left} y1={pad.top + innerH} x2={pad.left + innerW} y2={pad.top + innerH}
          stroke={COLORS.border} strokeWidth={1} />

        {/* Axis labels */}
        <text x={W / 2} y={H - 4} textAnchor="middle" fill={COLORS.textMuted} fontSize={11}>{cd.x_label}</text>
        <text x={10} y={pad.top + innerH / 2} textAnchor="middle" fill={COLORS.textMuted} fontSize={11}
          transform={`rotate(-90, 10, ${pad.top + innerH / 2})`}>{cd.y_label}</text>

        {/* Trend line (appears after dots) */}
        {lineProgress > 0 && (
          <line
            x1={lineP1.x} y1={lineP1.y}
            x2={lineP1.x + (lineP2.x - lineP1.x) * lineProgress}
            y2={lineP1.y + (lineP2.y - lineP1.y) * lineProgress}
            stroke={accent} strokeWidth={1.5} strokeDasharray="6,4" opacity={0.6} />
        )}

        {/* Scatter dots */}
        {points.map((p, i) => {
          const {x, y} = toSvg(p.x, p.y);
          const prog = dotProgress(i);
          return (
            <circle key={i} cx={x} cy={y} r={4 * prog}
              fill={accent} fillOpacity={0.7} />
          );
        })}
      </svg>
    </SceneShell>
  );
}
