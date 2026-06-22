// Histogram scene — animated bar reveal for outlier distribution
import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneShell} from '../components/SceneShell';
import {ACCENT_FOR, COLORS, Finding} from '../types';

export function HistogramScene({finding}: {finding: Finding}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const accent = ACCENT_FOR[finding.type];
  const cd = finding.chart_data as {
    bins: number[];
    counts: number[];
    outlier_lower: number;
    outlier_upper: number;
    column: string;
    mean?: number;
  };

  const bins = cd.bins ?? [];
  const counts = cd.counts ?? [];
  const maxCount = Math.max(...counts, 1);

  const W = 860, H = 280;
  const pad = {top: 20, right: 20, bottom: 40, left: 50};
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;
  const barW = innerW / Math.max(counts.length, 1);

  const drawProgress = (i: number) =>
    interpolate(frame, [fps * 0.15 + i * fps * 0.05, fps * 0.15 + i * fps * 0.05 + fps * 0.4], [0, 1], {
      extrapolateRight: 'clamp', extrapolateLeft: 'clamp',
    });

  return (
    <SceneShell findingType={finding.type} captionText={finding.text}>
      <svg width={W} height={H} style={{display: 'block'}}>
        {/* Baseline */}
        <line x1={pad.left} y1={pad.top + innerH} x2={pad.left + innerW} y2={pad.top + innerH}
          stroke={COLORS.border} strokeWidth={1} />

        {counts.map((c, i) => {
          const x = pad.left + i * barW;
          const h = (c / maxCount) * innerH * drawProgress(i);
          const y = pad.top + innerH - h;
          const binStart = bins[i] ?? 0;
          const isOutlier = bins[i] < cd.outlier_lower || (bins[i + 1] ?? bins[i]) > cd.outlier_upper;

          return (
            <g key={i}>
              <rect
                x={x + 1} y={y}
                width={barW - 2} height={h}
                fill={isOutlier ? COLORS.problem : accent}
                fillOpacity={isOutlier ? 0.9 : 0.6}
                rx={2}
              />
            </g>
          );
        })}

        {/* Outlier bounds markers */}
        {cd.outlier_lower !== undefined && bins.length > 0 && (() => {
          const lx = pad.left + ((cd.outlier_lower - bins[0]) / ((bins[bins.length - 1] ?? bins[0]) - bins[0])) * innerW;
          const ux = pad.left + ((cd.outlier_upper - bins[0]) / ((bins[bins.length - 1] ?? bins[0]) - bins[0])) * innerW;
          return (
            <>
              <line x1={Math.max(lx, pad.left)} y1={pad.top} x2={Math.max(lx, pad.left)} y2={pad.top + innerH}
                stroke="#ff6b6b" strokeWidth={1.5} strokeDasharray="4,4" />
              <line x1={Math.min(ux, pad.left + innerW)} y1={pad.top} x2={Math.min(ux, pad.left + innerW)} y2={pad.top + innerH}
                stroke="#ff6b6b" strokeWidth={1.5} strokeDasharray="4,4" />
              <text x={Math.max(lx, pad.left) + 4} y={pad.top + 14} fill="#ff6b6b" fontSize={10}>lower</text>
              <text x={Math.min(ux, pad.left + innerW) + 4} y={pad.top + 14} fill="#ff6b6b" fontSize={10}>upper</text>
            </>
          );
        })()}

        {/* X-axis labels */}
        {bins.filter((_, i) => i % 2 === 0).map((bin, i) => (
          <text key={i} x={pad.left + i * 2 * barW + barW} y={H - 6}
            textAnchor="middle" fill={COLORS.textMuted} fontSize={9}>
            {bin >= 1000 ? `${(bin / 1000).toFixed(1)}k` : bin.toFixed(0)}
          </text>
        ))}
      </svg>
    </SceneShell>
  );
}
