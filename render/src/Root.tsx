import React from 'react';
import {Composition, Still} from 'remotion';
import {Video, calcMeta} from './Video';
import {Thumbnail} from './Thumbnail';
import {sampleThumb, sampleVideo} from './sample';
import {FPS} from './types';
import {CartoonTest} from './cartoon/CartoonTest';
import {Episode, calcEpisode, sampleEpisode} from './cartoon/Episode';
import {EpisodeShort, calcShort, sampleShort} from './cartoon/EpisodeShort';
import {MoneyThumb} from './cartoon/MoneyThumb';
import {EpisodeThumb, sampleEpisodeThumb} from './cartoon/EpisodeThumb';
import {ChannelAvatar, ChannelBanner, sampleAvatar, sampleBanner} from './cartoon/ChannelAvatar';

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
    <Composition id="Episode" component={Episode} width={1920} height={1080} fps={FPS} durationInFrames={180} defaultProps={sampleEpisode} calculateMetadata={calcEpisode} />
    <Still id="ChannelBanner" component={ChannelBanner} width={2560} height={1440} defaultProps={sampleBanner} />
    <Still id="ChannelAvatar" component={ChannelAvatar} width={800} height={800} defaultProps={sampleAvatar} />
    <Composition id="EpisodeShort" component={EpisodeShort} width={1080} height={1920} fps={FPS} durationInFrames={90} defaultProps={sampleShort} calculateMetadata={calcShort} />
    <Still id="MoneyThumb" component={MoneyThumb} width={1280} height={720} defaultProps={{top: 'PAYMENT', bottom: 'FAILED'}} />
    <Still id="EpisodeThumb" component={EpisodeThumb} width={1280} height={720} defaultProps={sampleEpisodeThumb} />
    <Still id="Thumbnail" component={Thumbnail} width={1280} height={720} defaultProps={sampleThumb} />
  </>
);
