import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene, Style} from '../types';
import {fontFamily, rgba, useLayout} from '../theme';

type Side = {label: string; points: string[]};

export const Compare: React.FC<{scene: Scene; style: Style; dur: number}> = ({scene, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {portrait, u, w, h} = useLayout();
  const props = scene.visual.props ?? {};
  const left: Side = props.left ?? {label: '', points: []};
  const right: Side = props.right ?? {label: '', points: []};

  const cardW = portrait ? w * 0.84 : w * 0.38;
  const cardH = portrait ? h * 0.175 : h * 0.4;
  const positions = portrait
    ? [
        {x: (w - cardW) / 2, y: h * 0.25},
        {x: (w - cardW) / 2, y: h * 0.25 + cardH + 90 * u},
      ]
    : [
        {x: w / 2 - cardW - 50 * u, y: h * 0.27},
        {x: w / 2 + 50 * u, y: h * 0.27},
      ];

  const card = (side: Side, i: number, color: string) => {
    const p = spring({frame: frame - i * 10, fps, config: {damping: 16}});
    return (
      <div
        key={i}
        style={{
          position: 'absolute',
          left: positions[i].x,
          top: positions[i].y,
          width: cardW,
          height: cardH,
          borderRadius: 28 * u,
          background: rgba(style.palette.bg, 0.82),
          border: `${5 * u}px solid ${color}`,
          padding: `${22 * u}px ${34 * u}px`,
          boxSizing: 'border-box',
          transform: `translateY(${(1 - p) * 50 * u}px)`,
          opacity: Math.min(1, p),
          overflow: 'hidden',
        }}
      >
        <div style={{fontSize: (portrait ? 46 : 52) * u, fontWeight: 800, color, textTransform: 'uppercase', letterSpacing: 2}}>{side.label}</div>
        <ul style={{margin: `${12 * u}px 0 0`, paddingLeft: 38 * u, color: style.palette.ink, fontSize: (portrait ? 36 : 40) * u, fontWeight: 600, lineHeight: 1.35}}>
          {side.points.slice(0, 4).map((pt, k) => {
            const pp = spring({frame: frame - (14 + i * 10 + k * 8), fps, config: {damping: 20}});
            return (
              <li key={k} style={{opacity: Math.min(1, pp)}}>
                {pt}
              </li>
            );
          })}
        </ul>
      </div>
    );
  };

  const vs = spring({frame: frame - 6, fps, config: {damping: 12}});
  const vsSize = 96 * u;
  const vsPos = portrait
    ? {left: w / 2 - vsSize / 2, top: positions[0].y + cardH + 45 * u - vsSize / 2}
    : {left: w / 2 - vsSize / 2, top: positions[0].y + cardH / 2 - vsSize / 2};
  return (
    <AbsoluteFill style={{fontFamily: fontFamily(style)}}>
      {card(left, 0, style.palette.teal)}
      {card(right, 1, style.palette.gold)}
      <div
        style={{
          position: 'absolute',
          ...vsPos,
          width: vsSize,
          height: vsSize,
          borderRadius: '50%',
          background: style.palette.gold,
          color: style.palette.bg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          fontSize: 40 * u,
          transform: `scale(${vs})`,
        }}
      >
        VS
      </div>
    </AbsoluteFill>
  );
};
