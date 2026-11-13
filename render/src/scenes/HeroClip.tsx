import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile} from 'remotion';
import type {Scene, Style} from '../types';
import {StillPlayer} from './StillPlayer';

/** Generated motion for the few moments that carry the story. Plays an mp4 if one was provided, else shows a still. */
export const HeroClip: React.FC<{scene: Scene; style: Style; src?: string; dur: number}> = ({scene, style, src, dur}) => {
  if (src && src.endsWith('.mp4')) {
    return (
      <AbsoluteFill>
        <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
    );
  }
  return <StillPlayer scene={scene} style={style} src={src} dur={dur} />;
};
