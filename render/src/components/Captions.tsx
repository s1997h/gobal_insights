import React, {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Style, Word} from '../types';
import {fontFamily, rgba, useLayout} from '../theme';

type Line = {words: Word[]; start: number; end: number};

/** Group words into short lines. A line never crosses a sentence end or a scene boundary. */
export const groupLines = (words: Word[], maxWords: number): Line[] => {
  const lines: Line[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length) {
      lines.push({words: cur, start: cur[0].start_ms, end: cur[cur.length - 1].end_ms});
      cur = [];
    }
  };
  for (const w of words) {
    if (cur.length && cur[cur.length - 1].scene_id !== w.scene_id) flush();
    cur.push(w);
    if (cur.length >= maxWords || /[.!?]["')]?$/.test(w.word)) flush();
  }
  flush();
  return lines;
};

/** The line to show at time t (ms), or null. A line stays up until the next one starts, or 500 ms after its last word. */
export const lineAt = (lines: Line[], t: number): Line | null => {
  let lo = 0;
  let hi = lines.length - 1;
  let idx = -1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (lines[mid].start <= t) {
      idx = mid;
      lo = mid + 1;
    } else hi = mid - 1;
  }
  if (idx < 0) return null;
  const line = lines[idx];
  const next = lines[idx + 1];
  const until = Math.min(next ? next.start : Infinity, line.end + 500);
  return t < until ? line : null;
};

export const Captions: React.FC<{words: Word[]; style: Style}> = ({words, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {portrait, u, h} = useLayout();
  const lines = useMemo(() => groupLines(words, style.captions.max_words_per_line), [words, style]);
  const t = (frame / fps) * 1000;
  const line = lineAt(lines, t);
  if (!line) return null;

  let active = -1;
  line.words.forEach((w, i) => {
    if (w.start_ms <= t) active = i;
  });

  const fontSize = (portrait ? 66 : 66) * u;
  const centered = style.captions.position === 'center' || portrait;
  const pos: React.CSSProperties = centered
    ? {top: h * (portrait ? 0.62 : 0.5)}
    : {bottom: h * 0.075};

  return (
    <AbsoluteFill style={{pointerEvents: 'none', alignItems: 'center'}}>
      <div
        style={{
          position: 'absolute',
          ...pos,
          maxWidth: '88%',
          textAlign: 'center',
          fontFamily: fontFamily(style),
          fontWeight: 800,
          fontSize,
          lineHeight: 1.15,
          color: style.palette.ink,
          background: rgba(style.palette.bg, 0.62),
          padding: `${14 * u}px ${30 * u}px`,
          borderRadius: 26 * u,
          textShadow: '0 4px 18px rgba(0,0,0,0.5)',
        }}
      >
        {line.words.map((w, i) => (
          <React.Fragment key={`${w.start_ms}-${i}`}>
            <span
              style={{
                display: 'inline-block',
                color: i === active ? style.captions.highlight : style.palette.ink,
              }}
            >
              {w.word}
            </span>
            {i < line.words.length - 1 ? ' ' : ''}
          </React.Fragment>
        ))}
      </div>
    </AbsoluteFill>
  );
};
