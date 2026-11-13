import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import type {Scene, Style} from './types';
import {OnScreenText} from './components/OnScreenText';
import {TitleCard} from './scenes/TitleCard';
import {YouReaction} from './scenes/YouReaction';
import {Diagram} from './scenes/Diagram';
import {NumberCounter} from './scenes/NumberCounter';
import {Compare} from './scenes/Compare';
import {CaptionsOnly} from './scenes/CaptionsOnly';
import {StillPlayer} from './scenes/StillPlayer';
import {HeroClip} from './scenes/HeroClip';

type Props = {scene: Scene; style: Style; image?: string; dur: number};

/** Picks the component from visual.type and visual.template. Every colour and font comes from `style`. */
export const SceneRenderer: React.FC<Props> = ({scene, style, image, dur}) => {
  const frame = useCurrentFrame();
  const v = scene.visual;
  let body: React.ReactNode;
  if (v.type === 'template') {
    switch (v.template) {
      case 'title_card':
        body = <TitleCard scene={scene} style={style} dur={dur} />;
        break;
      case 'you_reaction':
        body = <YouReaction scene={scene} style={style} dur={dur} />;
        break;
      case 'diagram':
        body = <Diagram scene={scene} style={style} dur={dur} />;
        break;
      case 'number_counter':
        body = <NumberCounter scene={scene} style={style} dur={dur} />;
        break;
      case 'compare':
        body = <Compare scene={scene} style={style} dur={dur} />;
        break;
      default:
        body = <CaptionsOnly scene={scene} style={style} dur={dur} />;
    }
  } else if (v.type === 'still') {
    body = <StillPlayer scene={scene} style={style} src={image} dur={dur} />;
  } else {
    body = <HeroClip scene={scene} style={style} src={image} dur={dur} />;
  }
  const fadeIn = interpolate(frame, [0, 6], [0, 1], {extrapolateRight: 'clamp'});
  const showText = !!scene.on_screen_text && v.template !== 'title_card';
  return (
    <AbsoluteFill style={{opacity: fadeIn}}>
      {body}
      {showText ? <OnScreenText text={scene.on_screen_text as string} style={style} /> : null}
    </AbsoluteFill>
  );
};
