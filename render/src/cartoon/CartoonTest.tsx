import React from 'react';
import {AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Character, type Look} from './Character';
import {Car, ParkingLot, Vignette} from './Sets';

/** A two-shot style test: the cast, a set, a prop, walking, reactions and a zombie. */

export const CAST: Record<string, Look> = {
  you: {skin: '#f2e8dc', hair: 'short', hairColor: '#3b2a20', top: 'hoodie', topColor: '#3aa59b', pants: '#2f3a4f'},
  maya: {skin: '#f2e8dc', hair: 'long', hairColor: '#6b4529', top: 'hoodie', topColor: '#2f4a7a', pants: '#262b36'},
  leo: {skin: '#f2e8dc', hair: 'curly', hairColor: '#7a4a2a', top: 'sweater', topColor: '#4f7a43', pants: '#2b3242'},
  zoe: {skin: '#f2e8dc', hair: 'ponytail', hairColor: '#c8692e', top: 'hoodie', topColor: '#6a4f8f', pants: '#2b3242'},
  sam: {skin: '#f2e8dc', hair: 'spiky', hairColor: '#2a2522', top: 'sweater', topColor: '#2f4a7a', pants: '#262b36', glasses: true},
  ana: {skin: '#f2e8dc', hair: 'bob', hairColor: '#2a2220', top: 'tee', topColor: '#b5524a', pants: '#3a3f4a'},
  zombie: {skin: '#a8bf92', hair: 'short', hairColor: '#3a3f2a', top: 'tee', topColor: '#6d6a5e', pants: '#3b3d33', torn: true},
};

const Camera: React.FC<{from: number; to: number; dur: number; children: React.ReactNode}> = ({from, to, dur, children}) => {
  const f = useCurrentFrame();
  const z = interpolate(f, [0, dur], [from, to], {extrapolateRight: 'clamp'});
  return <g transform={`translate(960 600) scale(${z}) translate(-960 -600)`}>{children}</g>;
};

const ShotArrive: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const x = interpolate(f, [0, 80], [-90, 760], {extrapolateRight: 'clamp'});
  const walking = f < 80;
  return (
    <svg viewBox="0 0 1920 1080" width="100%" height="100%">
      <Camera from={1} to={1.04} dur={120}>
        <ParkingLot />
        <Car x={1460} y={985} scale={1.3} />
        <Character
          look={CAST.you}
          pose="walk"
          moving={walking}
          expression={f < 100 ? 'neutral' : 'worried'}
          facing={f < 92 ? 0 : 1}
          x={x}
          y={1000}
          scale={1.25}
          t={t}
        />
      </Camera>
      <Vignette />
    </svg>
  );
};

const ShotCrowd: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const row = ['leo', 'maya', 'you', 'zoe', 'sam', 'ana'];
  const zx = interpolate(f, [15, 120], [2080, 1700], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <svg viewBox="0 0 1920 1080" width="100%" height="100%">
      <Camera from={1} to={1.06} dur={120}>
        <ParkingLot />
        {row.map((who, i) => {
          const turn = f > 12 + i * 3 ? 1 : 0;
          const shocked = f > 40 + (row.length - i) * 4;
          const scared = f > 58 + (row.length - i) * 4;
          return (
            <Character
              key={who}
              look={CAST[who]}
              pose={scared ? 'scared' : 'stand'}
              expression={shocked ? 'shocked' : 'neutral'}
              facing={turn}
              x={190 + i * 255}
              y={1000}
              scale={1.25}
              t={t}
              seed={i * 3 + 1}
            />
          );
        })}
        <Character look={CAST.zombie} pose="zombie" moving expression="zombie" facing={-1} x={zx} y={1005} scale={1.27} t={t} seed={9} />
      </Camera>
      <Vignette dusk={0.18} />
    </svg>
  );
};

export const CartoonTest: React.FC = () => (
  <AbsoluteFill style={{backgroundColor: '#000'}}>
    <Sequence durationInFrames={120}>
      <ShotArrive />
    </Sequence>
    <Sequence from={120} durationInFrames={120}>
      <ShotCrowd />
    </Sequence>
  </AbsoluteFill>
);
