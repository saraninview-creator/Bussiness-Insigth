// Shared types for all scene components
export type FindingType = 'insight' | 'problem' | 'suggestion';

export interface Finding {
  id: string;
  type: FindingType;
  text: string;
  chart_type: string;
  chart_data: Record<string, unknown>;
  timestamp: number;
  duration_seconds: number;
}

export interface ScriptSegment {
  finding_id: string;
  finding_type: FindingType;
  text: string;
  audio_file: string;
  start_ms: number;
  end_ms: number;
  duration_ms: number;
}

export interface RootProps {
  jobId: string;
  findings: Finding[];
  audioFile: string;
  segments: ScriptSegment[];
}

// Color palette (black/white theme, glow only on video player via CSS)
export const COLORS = {
  bg: '#0a0a0a',
  surface: '#111111',
  surfaceAlt: '#1a1a1a',
  border: '#2a2a2a',
  text: '#ffffff',
  textSecondary: '#aaaaaa',
  textMuted: '#666666',
  insight: '#4a9eff',    // blue accent
  problem: '#ff6b6b',    // red/coral accent
  suggestion: '#5dcaa5', // teal/green accent
  gridLine: '#1e1e1e',
};

export const ACCENT_FOR: Record<FindingType, string> = {
  insight: COLORS.insight,
  problem: COLORS.problem,
  suggestion: COLORS.suggestion,
};

export const LABEL_FOR: Record<FindingType, string> = {
  insight: 'INSIGHT',
  problem: 'PROBLEM',
  suggestion: 'SUGGESTION',
};

export const ICON_FOR: Record<FindingType, string> = {
  insight: '↗',
  problem: '⚠',
  suggestion: '→',
};
