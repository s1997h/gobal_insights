import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import type {Scene, Style} from '../types';
import {rgba, useLayout} from '../theme';

/** No picture: slow concentric rings give the eye something calm while the captions carry the line. */
export const CaptionsOnly: React.FC<{scene: Scene; style: Style; dur: number}> = ({style}) => {
  const frame = useCurrentFrame();
  const {w, h, portrait} = useLayout();
  const cx = w / 2;
  const cy = portrait ? h * 0.4 : h * 0.4;
  const base = Math.min(w, h) * 0.18;
  return (
    <AbsoluteFill>
      <svg width={w} height={h}>
        {[0, 1, 2, 3].map((i) => {
          const t = ((frame / 90 + i * 0.25) % 1 + 1) % 1;
          const r = base + t * base * 2.2;
          return <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={rgba(style.palette.teal, 0.5 * (1 - t))} strokeWidth={6} />;
        })}
        <circle cx={cx} cy={cy} r={base * 0.42} fill={rgba(style.palette.gold, 0.9)} />
      </svg>
    </AbsoluteFill>
  );
};
