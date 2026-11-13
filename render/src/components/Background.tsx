import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Style} from '../types';
import {mix, rgba} from '../theme';

/** Calm navy gradient with slowly drifting colour glows. Cheap radial gradients, no blur filters. */
export const Background: React.FC<{style: Style}> = ({style}) => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const t = frame / 30;
  const {palette} = style;
  const glows = [
    {x: 0.15, y: 0.2, r: 0.55, c: palette.teal, ph: 0, a: 0.16},
    {x: 0.85, y: 0.8, r: 0.6, c: palette.gold, ph: 2, a: 0.12},
    {x: 0.65, y: 0.05, r: 0.4, c: palette.teal, ph: 4, a: 0.08},
  ];
  return (
    <AbsoluteFill style={{background: `linear-gradient(160deg, ${palette.bg} 0%, ${mix(palette.bg, '#ffffff', 0.07)} 100%)`}}>
      {glows.map((g, i) => {
        const size = Math.max(width, height) * g.r * 2;
        const cx = (g.x + Math.sin(t * 0.25 + g.ph) * 0.03) * width;
        const cy = (g.y + Math.cos(t * 0.2 + g.ph) * 0.03) * height;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: cx - size / 2,
              top: cy - size / 2,
              width: size,
              height: size,
              background: `radial-gradient(circle, ${rgba(g.c, g.a)} 0%, ${rgba(g.c, 0)} 65%)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
