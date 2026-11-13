import React from 'react';
import {Composition, Still} from 'remotion';
import {Video, calcMeta} from './Video';
import {Thumbnail} from './Thumbnail';
import {sampleThumb, sampleVideo} from './sample';
import {FPS} from './types';
import {CartoonTest} from './cartoon/CartoonTest';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Long"
      component={Video}
      width={1920}
      height={1080}
      fps={FPS}
      durationInFrames={270}
      defaultProps={sampleVideo('long')}
      calculateMetadata={calcMeta}
    />
    <Composition
      id="Short"
      component={Video}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={270}
      defaultProps={sampleVideo('short')}
      calculateMetadata={calcMeta}
    />
    <Composition id="CartoonTest" component={CartoonTest} width={1920} height={1080} fps={FPS} durationInFrames={240} />
    <Still id="Thumbnail" component={Thumbnail} width={1280} height={720} defaultProps={sampleThumb} />
  </>
);
