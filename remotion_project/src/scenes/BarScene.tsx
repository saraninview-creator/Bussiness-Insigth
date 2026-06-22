// Bar chart scene — animated bar height reveal
import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneShell} from '../components/SceneShell';
import {ACCENT_FOR, COLORS, Finding} from '../types';

export function BarScene({finding}: {finding: Finding}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const accent = ACCENT_FOR[finding.type];
  const cd = finding.chart_data as {
    labels: string[];
    values: number[];
    highlight_label: string;
    y_label: string;
  };

  const labels = (cd.labels ?? []).slice(0, 8);
  const values = (cd.values ?? []).slice(0, 8);
  const highlightLabel = cd.highlight_label ?? '';

  const maxVal = Math.max(...values, 1);

  // Staggered bar grow animation
  const drawProgress = (barIdx: number) =>
    interpolate(
      frame,
      [fps * 0.2 + barIdx * fps * 0.08, fps * 0.2 + barIdx * fps * 0.08 + fps * 0.5],
      [0, 1],
      {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'}
    );

  const W = 860, H = 300;
  const barAreaH = 220;
  const barW = Math.min(70, (W - 80) / Math.max(labels.length, 1) - 12);
  const gap = (W - 60) / Math.max(labels.length, 1);

  return (
    <SceneShell findingType={finding.type} captionText={finding.text}>
      <svg width={W} height={H} style={{display: 'block', overflow: 'visible'}}>
        {/* Baseline */}
        <line x1={40} y1={barAreaH} x2={W - 20} y2={barAreaH}
          stroke={COLORS.border} strokeWidth={1} />

        {labels.map((label, i) => {
          const pct = values[i] / maxVal;
          const progress = drawProgress(i);
          const barH = pct * barAreaH * progress;
          const x = 40 + i * gap + (gap - barW) / 2;
          const y = barAreaH - barH;
          const isHighlight = label === highlightLabel;
          const barColor = isHighlight ? accent : COLORS.surfaceAlt;
          const textColor = isHighlight ? accent : COLORS.textMuted;

          return (
            <g key={i}>
              <rect
                x={x} y={y}
                width={barW} height={barH}
                fill={barColor}
                rx={3}
                fillOpacity={isHighlight ? 1 : 0.7}
              />
              {/* Value label on top */}
              {progress > 0.7 && (
                <text x={x + barW / 2} y={y - 6} textAnchor="middle"
                  fill={textColor} fontSize={12} fontWeight={isHighlight ? 700 : 400}>
                  {values[i].toFixed(1)}%
                </text>
              )}
              {/* X label */}
              <text
                x={x + barW / 2}
                y={barAreaH + 18}
                textAnchor="middle"
                fill={textColor}
                fontSize={10}
                fontWeight={isHighlight ? 700 : 400}
              >
                {label.length > 10 ? label.slice(0, 9) + '…' : label}
              </text>
            </g>
          );
        })}
      </svg>
    </SceneShell>
  );
}
