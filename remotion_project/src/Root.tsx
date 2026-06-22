// Root composition — sequences all scenes and attaches the audio track
import React from 'react';
import {Audio, Composition, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {BarScene} from './scenes/BarScene';
import {HistogramScene} from './scenes/HistogramScene';
import {LineScene} from './scenes/LineScene';
import {ScatterScene} from './scenes/ScatterScene';
import {StatCardScene} from './scenes/StatCardScene';
import {Finding, RootProps} from './types';

const FPS = 30;

function SceneRouter({finding}: {finding: Finding}) {
  switch (finding.chart_type) {
    case 'line':
      return <LineScene finding={finding} />;
    case 'bar':
      return <BarScene finding={finding} />;
    case 'histogram':
      return <HistogramScene finding={finding} />;
    case 'scatter':
      return <ScatterScene finding={finding} />;
    case 'stat_card':
    default:
      return <StatCardScene finding={finding} />;
  }
}

function DataNarrateVideo({findings, audioFile, segments}: RootProps) {
  const {width, height} = useVideoConfig();

  // Calculate per-finding durations from segment timings
  const sceneDurations = findings.map((f, i) => {
    const seg = segments?.[i];
    if (seg?.duration_ms) {
      // Add 1 second buffer per scene for transitions
      return Math.round((seg.duration_ms / 1000 + 1) * FPS);
    }
    // Fallback: 5 seconds per scene
    return 5 * FPS;
  });

  let currentFrame = 0;
  const sequences = findings.map((finding, i) => {
    const from = currentFrame;
    const duration = sceneDurations[i] ?? 5 * FPS;
    currentFrame += duration;
    return {finding, from, duration};
  });

  return (
    <div style={{width, height, backgroundColor: '#0a0a0a', position: 'relative'}}>
      {/* Scene sequences and individual per-scene audio */}
      {sequences.map(({finding, from, duration}, i) => {
        const seg = segments?.[i];
        let audioSrc = seg?.audio_file || '';
        // If it's an absolute path, format it correctly for Remotion
        if (audioSrc && !audioSrc.startsWith('http') && !audioSrc.startsWith('data:') && !audioSrc.startsWith('file://')) {
          audioSrc = 'file:///' + audioSrc.replace(/\\/g, '/').replace(/^\/?/, '');
        }
        
        return (
          <Sequence key={finding.id ?? i} from={from} durationInFrames={duration}>
            <div style={{position: 'absolute', inset: 0}}>
              <SceneRouter finding={finding} />
            </div>
            {audioSrc && <Audio src={audioSrc} />}
          </Sequence>
        );
      })}
    </div>
  );
}

export function DataNarrateRoot() {
  // Default props for Remotion Studio preview
  const defaultFindings: Finding[] = [
    {
      id: 'demo1',
      type: 'insight',
      text: 'Revenue shows a strong upward trend of 34.5% over the analysis period.',
      chart_type: 'line',
      chart_data: {
        labels: ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
        series: [10000, 11200, 12400, 13800, 15200, 13450],
        highlight_idx: 4,
        y_label: 'Revenue',
        pct_change: 34.5,
      },
      timestamp: 0,
      duration_seconds: 6,
    },
    {
      id: 'demo2',
      type: 'problem',
      text: 'The Sales column has 15.2% missing values, affecting 1,520 records.',
      chart_type: 'stat_card',
      chart_data: {
        stat_label: 'Missing Values',
        stat_value: '15.2%',
        sub_label: 'Affected Records',
        sub_value: '1,520',
        column: 'Sales',
        total_rows: 10000,
      },
      timestamp: 7,
      duration_seconds: 5,
    },
    {
      id: 'demo3',
      type: 'suggestion',
      text: 'Investigate root causes of the Sales data gap and implement automated validation.',
      chart_type: 'stat_card',
      chart_data: {
        stat_label: 'Suggestion',
        stat_value: 'Fix',
        sub_label: 'Impact',
        sub_value: 'High',
        column: 'Sales',
        total_rows: 10000,
      },
      timestamp: 13,
      duration_seconds: 5,
    },
  ];

  const defaultSegments = defaultFindings.map((f, i) => ({
    finding_id: f.id,
    finding_type: f.type,
    text: f.text,
    audio_file: '',
    start_ms: i * 6000,
    end_ms: i * 6000 + 6000,
    duration_ms: 6000,
  }));

  // Total duration = sum of all scene durations
  const totalDurationFrames = defaultFindings.reduce((acc, _, i) => {
    return acc + Math.round((defaultSegments[i].duration_ms / 1000 + 1) * FPS);
  }, 0);

  return (
    <Composition
      id="DataNarrate"
      component={DataNarrateVideo}
      durationInFrames={totalDurationFrames}
      fps={FPS}
      width={1280}
      height={720}
      calculateMetadata={({props}) => {
        const currentFps = 30;
        const findings = (props.findings as Finding[]) || [];
        const segments = (props.segments as any[]) || [];
        const frames = findings.reduce((acc: number, _: any, i: number) => {
          const seg = segments[i];
          if (seg?.duration_ms) {
            return acc + Math.round((seg.duration_ms / 1000 + 1) * currentFps);
          }
          return acc + 5 * currentFps;
        }, 0);
        return {
          durationInFrames: Math.max(Math.round(frames), 30),
          props
        };
      }}
      defaultProps={{
        jobId: 'demo',
        findings: defaultFindings,
        audioFile: '',
        segments: defaultSegments,
      }}
    />
  );
}
