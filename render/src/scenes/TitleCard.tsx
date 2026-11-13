import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene, Style} from '../types';
import {fontFamily, useLayout} from '../theme';

export const TitleCard: React.FC<{scene: Scene; style: Style; dur: number}> = ({scene, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {portrait, u, h, safeTop} = useLayout();
  const props = scene.visual.props ?? {};
  const title: string = props.title ?? scene.on_screen_text ?? scene.narration.split(/[.!?]/)[0];
  const subtitle: string | undefined = props.subtitle;
  const p = spring({frame, fps, config: {damping: 200}});
  const bar = interpolate(p, [0, 1], [0, 260 * u]);
  const size = (title.length > 40 ? 88 : 108) * (portrait ? 0.95 : 1.1) * u;
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', fontFamily: fontFamily(style), paddingBottom: portrait ? h * 0.16 : 0}}>
      <div
        style={{
          position: 'absolute',
          top: safeTop + 10 * u,
          fontSize: 30 * u,
          letterSpacing: 8 * u,
          textTransform: 'uppercase',
          color: style.palette.teal,
          fontWeight: 700,
          opacity: p,
        }}
      >
        {style.channel_name}
      </div>
      <div style={{maxWidth: '82%', textAlign: 'center', transform: `translateY(${(1 - p) * 40 * u}px)`, opacity: p}}>
        <div style={{fontSize: size, fontWeight: 800, lineHeight: 1.08, color: style.palette.ink}}>{title}</div>
        <div style={{width: bar, height: 10 * u, background: style.palette.gold, borderRadius: 6 * u, margin: `${34 * u}px auto 0`}} />
        {subtitle ? (
          <div
            style={{
              marginTop: 30 * u,
              fontSize: 42 * u,
              letterSpacing: 6 * u,
              textTransform: 'uppercase',
              color: style.palette.teal,
              fontWeight: 600,
            }}
          >
            {subtitle}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
