import React from 'react';
import {AbsoluteFill, CalculateMetadataFunction, Sequence, useVideoConfig} from 'remotion';
import {Background} from './components/Background';
import {Captions} from './components/Captions';
import {SceneRenderer} from './SceneRenderer';
import {ensureFonts, fontFamily} from './theme';
import {FPS, VideoProps} from './types';

/** The video is as long as the narration: calculated from timing.json, never the other way round. */
export const calcMeta: CalculateMetadataFunction<VideoProps> = ({props}) => ({
  durationInFrames: Math.max(30, Math.ceil(props.timing.total_sec * FPS)),
});

export const Video: React.FC<VideoProps> = ({scenes, timing, words, images, style}) => {
  const {fps, durationInFrames} = useVideoConfig();
  ensureFonts(style);
  return (
    <AbsoluteFill style={{backgroundColor: style.palette.bg, fontFamily: fontFamily(style)}}>
      <Background style={style} />
      {scenes.map((scene, i) => {
        const span = timing.scenes[i];
        if (!span) return null;
        const from = Math.round((span.start_ms / 1000) * fps);
        const end = i === scenes.length - 1 ? durationInFrames : Math.round((span.end_ms / 1000) * fps);
        const dur = Math.max(1, end - from);
        return (
          <Sequence key={scene.id} from={from} durationInFrames={dur} layout="none">
            <SceneRenderer scene={scene} style={style} image={images[scene.id]} dur={dur} />
          </Sequence>
        );
      })}
      <Captions words={words} style={style} />
    </AbsoluteFill>
  );
};
