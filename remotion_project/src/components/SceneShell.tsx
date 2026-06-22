// Shared scene wrapper — dark background + grid + badge + caption
import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {ACCENT_FOR, COLORS, FindingType, ICON_FOR, LABEL_FOR} from '../types';

interface SceneShellProps {
  findingType: FindingType;
  captionText: string;
  children: React.ReactNode;
  fadeIn?: boolean;
}

export function SceneShell({findingType, captionText, children, fadeIn = true}: SceneShellProps) {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const accent = ACCENT_FOR[findingType];
  const label = LABEL_FOR[findingType];
  const icon = ICON_FOR[findingType];

  const opacity = fadeIn
    ? interpolate(frame, [0, fps * 0.4], [0, 1], {extrapolateRight: 'clamp'})
    : 1;

  // Fade out last 0.5s
  const fadeOut = interpolate(
    frame,
    [durationInFrames - fps * 0.5, durationInFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  const finalOpacity = opacity * fadeOut;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        backgroundColor: COLORS.bg,
        display: 'flex',
        flexDirection: 'column',
        opacity: finalOpacity,
        fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Subtle grid background */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `
          linear-gradient(${COLORS.gridLine} 1px, transparent 1px),
          linear-gradient(90deg, ${COLORS.gridLine} 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px',
        opacity: 0.4,
        pointerEvents: 'none',
      }} />

      {/* Header badge */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '28px 48px 0',
        zIndex: 1,
      }}>
        <div style={{
          backgroundColor: accent,
          color: '#0a0a0a',
          fontWeight: 800,
          fontSize: 13,
          letterSpacing: 2,
          padding: '6px 14px',
          borderRadius: 4,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}>
          <span>{icon}</span>
          <span>{label}</span>
        </div>
        <div style={{
          width: 1,
          height: 24,
          backgroundColor: COLORS.border,
        }} />
        <span style={{
          color: COLORS.textMuted,
          fontSize: 12,
          letterSpacing: 1,
          textTransform: 'uppercase',
        }}>
          DataNarrate Analysis
        </span>
      </div>

      {/* Chart area */}
      <div style={{flex: 1, padding: '20px 48px', zIndex: 1}}>
        {children}
      </div>

      {/* Caption */}
      <div style={{
        padding: '0 48px 32px',
        zIndex: 1,
        borderTop: `1px solid ${COLORS.border}`,
        paddingTop: 20,
        marginTop: 4,
      }}>
        <p style={{
          color: COLORS.textSecondary,
          fontSize: 18,
          lineHeight: 1.6,
          margin: 0,
          fontWeight: 400,
        }}>
          {captionText}
        </p>
      </div>
    </div>
  );
}
