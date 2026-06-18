// Stat card scene — large number with sub-stat, fade-in counter animation
import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {SceneShell} from '../components/SceneShell';
import {ACCENT_FOR, COLORS, Finding} from '../types';

export function StatCardScene({finding}: {finding: Finding}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const accent = ACCENT_FOR[finding.type];
  const cd = finding.chart_data as {
    stat_label: string;
    stat_value: string;
    sub_label: string;
    sub_value: string;
    column: string;
    total_rows: number;
  };

  const labelOpacity = interpolate(frame, [fps * 0.2, fps * 0.6], [0, 1], {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'});
  const mainOpacity = interpolate(frame, [fps * 0.5, fps * 1.0], [0, 1], {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'});
  const subOpacity = interpolate(frame, [fps * 0.8, fps * 1.4], [0, 1], {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'});
  const scale = interpolate(frame, [fps * 0.5, fps * 1.1], [0.7, 1], {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'});

  return (
    <SceneShell findingType={finding.type} captionText={finding.text}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        gap: 16,
      }}>
        <div style={{opacity: labelOpacity, color: COLORS.textMuted, fontSize: 14, letterSpacing: 2, textTransform: 'uppercase'}}>
          {cd.stat_label}
        </div>

        <div style={{
          opacity: mainOpacity,
          transform: `scale(${scale})`,
          fontSize: 96,
          fontWeight: 800,
          color: accent,
          letterSpacing: -4,
          lineHeight: 1,
        }}>
          {cd.stat_value}
        </div>

        <div style={{
          opacity: subOpacity,
          display: 'flex',
          gap: 32,
          marginTop: 8,
        }}>
          <div style={{textAlign: 'center'}}>
            <div style={{color: COLORS.textMuted, fontSize: 12, marginBottom: 4}}>{cd.sub_label}</div>
            <div style={{color: COLORS.text, fontSize: 24, fontWeight: 700}}>{cd.sub_value}</div>
          </div>
          {cd.total_rows > 0 && (
            <div style={{textAlign: 'center'}}>
              <div style={{color: COLORS.textMuted, fontSize: 12, marginBottom: 4}}>Total Rows</div>
              <div style={{color: COLORS.text, fontSize: 24, fontWeight: 700}}>{cd.total_rows.toLocaleString()}</div>
            </div>
          )}
        </div>

        {/* Column pill */}
        {cd.column && (
          <div style={{
            opacity: subOpacity,
            marginTop: 12,
            backgroundColor: COLORS.surfaceAlt,
            border: `1px solid ${COLORS.border}`,
            borderRadius: 20,
            padding: '6px 16px',
            color: COLORS.textSecondary,
            fontSize: 13,
          }}>
            Column: <strong style={{color: COLORS.text}}>{cd.column}</strong>
          </div>
        )}
      </div>
    </SceneShell>
  );
}
