import React from 'react';
import {AbsoluteFill, staticFile} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Character, INK, type Expression, type Pose} from './Character';
import {CAST} from './Cast';

/**
 * Thumbnail, 1280 x 720: one face, one object, at most three words. A hot background holds
 * contrast at feed size; the words never repeat the title.
 */

export type EpisodeThumbProps = {
  words: string; // e.g. "DAY 4..."
  highlight?: string; // the part drawn in red, e.g. "4"
  expr?: Expression;
  pose?: Pose;
};

let loaded = false;
const fonts = () => {
  if (loaded) return;
  loaded = true;
  loadFont({family: 'Inter', url: staticFile('fonts/Inter-ExtraBold.otf'), weight: '900'}).catch(() => undefined);
};

const ChainedPhone: React.FC = () => {
  const link = (x: number, y: number, r: number, i: number) => (
    <ellipse key={i} cx={x} cy={y} rx={26} ry={15} transform={`rotate(${r} ${x} ${y})`} fill="none" stroke="#5d6470" strokeWidth={11} />
  );
  return (
    <g>
      <rect x={-120} y={-215} width={240} height={430} rx={36} fill="#30343c" stroke={INK} strokeWidth={8} />
      <rect x={-100} y={-188} width={200} height={376} rx={20} fill="#9fd6f2" />
      {[0, 1, 2].map((i) => (
        <g key={i}>
          <rect x={-80} y={-150 + i * 70} width={160} height={46} rx={12} fill="#ffffff" stroke={INK} strokeWidth={3} />
          <circle cx={-56} cy={-127 + i * 70} r={12} fill={['#e9625a', '#2ec4b6', '#f2b84b'][i]} />
        </g>
      ))}
      <g>
        {Array.from({length: 9}, (_, i) => link(-150 + i * 38, -40 + i * 12, 18 + (i % 2) * 60, i))}
        {Array.from({length: 9}, (_, i) => link(150 - i * 38, 60 + i * 10, -18 - (i % 2) * 60, i + 20))}
      </g>
      <g transform="translate(20 70)">
        <path d="M -34 -20 L -34 -52 C -34 -96 34 -96 34 -52 L 34 -20" fill="none" stroke="#8b929c" strokeWidth={16} />
        <rect x={-58} y={-24} width={116} height={96} rx={16} fill="#f2b84b" stroke={INK} strokeWidth={7} />
        <circle cx={0} cy={16} r={11} fill={INK} />
        <rect x={-5} y={18} width={10} height={26} fill={INK} />
      </g>
    </g>
  );
};

export const EpisodeThumb: React.FC<EpisodeThumbProps> = ({words, highlight, expr = 'shocked', pose = 'scared'}) => {
  fonts();
  const parts = highlight && words.includes(highlight) ? words.split(highlight) : [words];
  const s = 3.15;
  const cx = 975;
  const feet = 1180;
  const headY = feet - 252 * s;
  return (
    <AbsoluteFill>
      <svg viewBox="0 0 1280 720" width="100%" height="100%">
        <defs>
          <radialGradient id="th-bg" cx="70%" cy="45%" r="80%">
            <stop offset="0" stopColor="#ffe066" />
            <stop offset="0.55" stopColor="#ffb238" />
            <stop offset="1" stopColor="#f2603a" />
          </radialGradient>
        </defs>
        <rect width={1280} height={720} fill="url(#th-bg)" />
        {Array.from({length: 16}, (_, i) => {
          const a = (i / 16) * Math.PI * 2;
          const b = a + Math.PI / 32;
          return <path key={i} d={`M ${cx} ${headY} L ${cx + Math.cos(a) * 1600} ${headY + Math.sin(a) * 1600} L ${cx + Math.cos(b) * 1600} ${headY + Math.sin(b) * 1600} Z`} fill="#ffffff" opacity={0.13} />;
        })}
        <Character look={CAST.you} pose={pose} expression={expr} x={cx} y={feet} scale={s} t={0.4} />
        {/* tired eyes and sweat */}
        <g stroke="#7a4f8f" strokeWidth={5} fill="none" strokeLinecap="round" opacity={0.75}>
          <path d={`M ${cx - 14 * s - 16} ${headY + 10 * s} Q ${cx - 14 * s} ${headY + 16 * s} ${cx - 14 * s + 16} ${headY + 10 * s}`} />
          <path d={`M ${cx + 14 * s - 16} ${headY + 10 * s} Q ${cx + 14 * s} ${headY + 16 * s} ${cx + 14 * s + 16} ${headY + 10 * s}`} />
        </g>
        {[
          [cx + 118, headY - 70, 1.3],
          [cx - 128, headY - 40, 1.0],
        ].map(([x, y, k], i) => (
          <path key={i} d={`M ${x} ${y} q ${14 * k} ${30 * k} 0 ${40 * k} q ${-14 * k} ${-10 * k} 0 ${-40 * k}`} fill="#7cc7ff" stroke={INK} strokeWidth={4} />
        ))}
        <g transform="translate(330 470) rotate(-12) scale(0.95)">
          <ChainedPhone />
        </g>
        <g transform="translate(46 190) rotate(-5)">
          <text x={0} y={0} fontFamily="Inter" fontWeight={900} fontSize={182} fill="#ffffff" stroke={INK} strokeWidth={22} paintOrder="stroke" letterSpacing={-6}>
            {parts.length > 1 ? (
              <>
                {parts[0]}
                <tspan fill="#e9443a">{highlight}</tspan>
                {parts[1]}
              </>
            ) : (
              words
            )}
          </text>
        </g>
      </svg>
    </AbsoluteFill>
  );
};

export const sampleEpisodeThumb: EpisodeThumbProps = {words: 'DAY 4...', highlight: '4'};
