import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import type {Scene, Style} from '../types';
import {fontFamily, useLayout} from '../theme';

export const NumberCounter: React.FC<{scene: Scene; style: Style; dur: number}> = ({scene, style, dur}) => {
  const frame = useCurrentFrame();
  const {u, w, h, portrait} = useLayout();
  const p = scene.visual.props ?? {};
  const from: number = typeof p.from === 'number' ? p.from : 0;
  const to: number = typeof p.to === 'number' ? p.to : 0;
  const decimals: number = typeof p.decimals === 'number' ? p.decimals : Number.isInteger(from) && Number.isInteger(to) ? 0 : 1;
  const end = Math.max(24, Math.round(dur * 0.6));
  const value = interpolate(frame, [8, end], [from, to], {
    easing: Easing.out(Easing.cubic),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const text = `${p.prefix ?? ''}${value.toLocaleString('en-US', {minimumFractionDigits: decimals, maximumFractionDigits: decimals})}${p.suffix ?? ''}`;
  const base = (portrait ? 200 : 230) * u;
  const size = Math.min(base, (w * 0.86) / (Math.max(1, text.length) * 0.62));
  const appear = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', fontFamily: fontFamily(style)}}>
      <div style={{position: 'absolute', top: portrait ? h * 0.33 : h * 0.26, width: '100%', textAlign: 'center', opacity: appear}}>
        <div
          style={{
            fontSize: size,
            fontWeight: 800,
            color: style.palette.gold,
            fontVariantNumeric: 'tabular-nums',
            lineHeight: 1.05,
          }}
        >
          {text}
        </div>
        {p.label ? (
          <div style={{marginTop: 18 * u, fontSize: 46 * u, letterSpacing: 6 * u, textTransform: 'uppercase', color: style.palette.teal, fontWeight: 700}}>
            {p.label}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
