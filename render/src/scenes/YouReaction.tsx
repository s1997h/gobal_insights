import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Mood, Scene, Style} from '../types';
import {fontFamily, rgba, useLayout} from '../theme';
import {You} from '../components/You';

const MOODS: Mood[] = ['neutral', 'shocked', 'happy', 'worried'];

export const YouReaction: React.FC<{scene: Scene; style: Style; dur: number}> = ({scene, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {portrait, w, h} = useLayout();
  const raw = scene.visual.props?.mood;
  const mood: Mood = MOODS.includes(raw) ? raw : 'neutral';
  const charH = portrait ? h * 0.34 : h * 0.6;
  const cy = portrait ? h * 0.43 : h * 0.47;
  const halo = spring({frame, fps, config: {damping: 18}});
  const haloSize = charH * 1.05 * halo;
  return (
    <AbsoluteFill style={{fontFamily: fontFamily(style)}}>
      <div
        style={{
          position: 'absolute',
          left: w / 2 - haloSize / 2,
          top: cy - haloSize * 0.5,
          width: haloSize,
          height: haloSize,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${rgba(style.palette.teal, 0.28)} 0%, ${rgba(style.palette.teal, 0)} 70%)`,
        }}
      />
      <div style={{position: 'absolute', left: 0, right: 0, top: cy - charH / 2, display: 'flex', justifyContent: 'center'}}>
        <You mood={mood} height={charH} />
      </div>
    </AbsoluteFill>
  );
};
