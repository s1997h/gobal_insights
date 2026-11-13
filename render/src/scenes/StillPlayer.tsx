import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';
import type {Scene, Style} from '../types';
import {fontFamily, rgba, useLayout} from '../theme';

/** A generated still with a slow push-in. Falls back to a plain panel if the image is missing. */
export const StillPlayer: React.FC<{scene: Scene; style: Style; src?: string; dur: number}> = ({scene, style, src, dur}) => {
  const frame = useCurrentFrame();
  const {u} = useLayout();
  const zoom = interpolate(frame, [0, Math.max(30, dur)], [1.0, 1.1], {extrapolateRight: 'clamp'});
  if (!src) {
    return (
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', fontFamily: fontFamily(style)}}>
        <div style={{color: rgba(style.palette.ink, 0.6), fontSize: 36 * u, maxWidth: '70%', textAlign: 'center'}}>
          {scene.visual.prompt}
        </div>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom})`}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse at center, ${rgba(style.palette.bg, 0)} 55%, ${rgba(style.palette.bg, 0.65)} 100%)`}} />
    </AbsoluteFill>
  );
};
