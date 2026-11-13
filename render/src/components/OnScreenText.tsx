import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Style} from '../types';
import {fontFamily, rgba, useLayout} from '../theme';

/** Short big callout shown by a scene (the scene's on_screen_text). Stays in the safe area in portrait. */
export const OnScreenText: React.FC<{text: string; style: Style}> = ({text, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {portrait, u, h} = useLayout();
  const p = spring({frame: frame - 6, fps, config: {damping: 14, stiffness: 140}});
  return (
    <AbsoluteFill style={{alignItems: 'center', pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          top: portrait ? h * 0.2 : h * 0.1,
          maxWidth: '86%',
          textAlign: 'center',
          fontFamily: fontFamily(style),
          fontWeight: 800,
          fontSize: (portrait ? 84 : 84) * u,
          color: style.palette.gold,
          background: rgba(style.palette.bg, 0.55),
          padding: `${10 * u}px ${34 * u}px`,
          borderRadius: 24 * u,
          opacity: Math.min(1, p),
          transform: `scale(${0.8 + 0.2 * p})`,
          letterSpacing: 1,
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
