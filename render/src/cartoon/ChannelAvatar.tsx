import React from 'react';
import {AbsoluteFill, staticFile} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Character, INK} from './Character';
import {CAST} from './Cast';

/**
 * Channel profile picture, 800 x 800. YouTube shows it as a circle as small as 98 px, so everything
 * that matters sits inside the middle 80% and reads at thumbnail size: one shape, bold outlines.
 */

export type AvatarProps = {variant: 'bulb' | 'mascot' | 'monogram'; letters?: string};

let loaded = false;
const fonts = () => {
  if (loaded) return;
  loaded = true;
  loadFont({family: 'Inter', url: staticFile('fonts/Inter-ExtraBold.otf'), weight: '900'}).catch(() => undefined);
};

const NAVY = '#0b1b33';
const NAVY2 = '#1b3a66';
const GOLD = '#f2b84b';
const TEAL = '#2ec4b6';
const CREAM = '#fffaf0';

// Simple doodle continents on a globe of radius r centred on 0,0
const SHAPES = [
  "M -0.78 -0.32 C -0.66 -0.62 -0.3 -0.72 -0.08 -0.56 C 0.0 -0.48 -0.12 -0.38 -0.18 -0.3 C -0.24 -0.2 -0.3 -0.12 -0.36 -0.02 C -0.44 -0.06 -0.52 -0.12 -0.6 -0.14 C -0.7 -0.18 -0.8 -0.22 -0.78 -0.32 Z",
  "M -0.34 0.06 C -0.2 0.04 -0.06 0.14 -0.08 0.3 C -0.1 0.48 -0.2 0.66 -0.28 0.8 C -0.34 0.62 -0.44 0.38 -0.44 0.2 C -0.44 0.12 -0.4 0.07 -0.34 0.06 Z",
  "M 0.14 -0.56 C 0.28 -0.68 0.5 -0.64 0.56 -0.48 C 0.46 -0.4 0.3 -0.4 0.2 -0.36 C 0.1 -0.4 0.08 -0.5 0.14 -0.56 Z",
  "M 0.12 -0.28 C 0.3 -0.33 0.55 -0.26 0.6 -0.06 C 0.63 0.14 0.5 0.3 0.43 0.5 C 0.38 0.63 0.3 0.67 0.26 0.55 C 0.22 0.4 0.24 0.26 0.15 0.16 C 0.04 0.05 0.0 -0.16 0.12 -0.28 Z",
  "M 0.6 -0.62 C 0.82 -0.6 1.0 -0.4 0.98 -0.18 C 0.86 -0.16 0.76 -0.26 0.66 -0.36 C 0.6 -0.44 0.56 -0.54 0.6 -0.62 Z",
];

// Simple doodle continents (the Americas, Europe, Africa, a bit of Asia) on a globe of radius r at 0,0
const Continents: React.FC<{r: number; fill: string}> = ({r, fill}) => (
  <g fill={fill} stroke={INK} strokeWidth={0.035} strokeLinejoin="round" transform={`scale(${r})`}>
    {SHAPES.map((d, i) => (
      <path key={i} d={d} />
    ))}
  </g>
);

const Globe: React.FC<{r: number}> = ({r}) => (
  <g>
    <defs>
      <clipPath id={`globe-${r}`}>
        <circle r={r} />
      </clipPath>
    </defs>
    <circle r={r} fill={TEAL} />
    <g clipPath={`url(#globe-${r})`}>
      <Continents r={r} fill={GOLD} />
      <g fill="none" stroke="#ffffff" strokeOpacity={0.35} strokeWidth={r * 0.025}>
        <ellipse rx={r * 0.45} ry={r} />
        <path d={`M ${-r} 0 L ${r} 0 M ${-r} ${-r * 0.5} Q 0 ${-r * 0.42} ${r} ${-r * 0.5} M ${-r} ${r * 0.5} Q 0 ${r * 0.58} ${r} ${r * 0.5}`} />
      </g>
      <ellipse cx={-r * 0.35} cy={-r * 0.45} rx={r * 0.22} ry={r * 0.12} fill="#ffffff" opacity={0.35} transform={`rotate(-30 ${-r * 0.35} ${-r * 0.45})`} />
    </g>
    <circle r={r} fill="none" stroke={INK} strokeWidth={r * 0.06} />
  </g>
);

const Rays: React.FC<{cx: number; cy: number; r0: number; r1: number; n?: number}> = ({cx, cy, r0, r1, n = 9}) => (
  <g stroke={GOLD} strokeWidth={22} strokeLinecap="round">
    {Array.from({length: n}, (_, i) => {
      const a = Math.PI + (i / (n - 1)) * Math.PI; // upper half
      return <path key={i} d={`M ${cx + Math.cos(a) * r0} ${cy + Math.sin(a) * r0} L ${cx + Math.cos(a) * r1} ${cy + Math.sin(a) * r1}`} />;
    })}
  </g>
);

const Background: React.FC = () => (
  <>
    <defs>
      <radialGradient id="av-bg" cx="50%" cy="42%" r="70%">
        <stop offset="0" stopColor={NAVY2} />
        <stop offset="1" stopColor={NAVY} />
      </radialGradient>
    </defs>
    <rect width={800} height={800} fill="url(#av-bg)" />
  </>
);

/** A lightbulb whose glass is a globe: "global" + "insight" in one shape. */
const Bulb: React.FC = () => (
  <svg viewBox="0 0 800 800" width="100%" height="100%">
    <Background />
    <Rays cx={400} cy={350} r0={250} r1={320} />
    <g transform="translate(400 350)">
      <Globe r={205} />
    </g>
    {/* neck and screw base */}
    <g stroke={INK} strokeWidth={12} strokeLinejoin="round">
      <path d="M 318 535 Q 400 575 482 535 L 470 600 L 330 600 Z" fill={TEAL} />
      <rect x={322} y={596} width={156} height={38} rx={14} fill="#c9d0da" />
      <rect x={330} y={630} width={140} height={36} rx={14} fill="#aeb6c2" />
      <path d="M 360 664 L 440 664 L 420 702 L 380 702 Z" fill={INK} />
    </g>
  </svg>
);

/** The cartoon narrator from the videos, curious, with a little globe. */
const Mascot: React.FC = () => (
  <svg viewBox="0 0 800 800" width="100%" height="100%">
    <defs>
      <radialGradient id="av-gold" cx="50%" cy="40%" r="70%">
        <stop offset="0" stopColor="#ffe066" />
        <stop offset="1" stopColor="#f2a33a" />
      </radialGradient>
    </defs>
    <rect width={800} height={800} fill="url(#av-gold)" />
    {Array.from({length: 14}, (_, i) => {
      const a = (i / 14) * Math.PI * 2;
      const b = a + Math.PI / 28;
      return <path key={i} d={`M 400 380 L ${400 + Math.cos(a) * 900} ${380 + Math.sin(a) * 900} L ${400 + Math.cos(b) * 900} ${380 + Math.sin(b) * 900} Z`} fill="#ffffff" opacity={0.16} />;
    })}
    {/* shoulders in the teal hoodie, cropped by the circle */}
    <g stroke={INK} strokeWidth={10} strokeLinejoin="round">
      <path d="M 170 820 Q 180 610 400 600 Q 620 610 630 820 Z" fill="#3aa59b" />
      <path d="M 320 604 Q 400 690 480 604 Z" fill="#2a7a72" />
      <path d="M 372 640 L 368 720 M 428 640 L 432 720" stroke="#f4f1ea" strokeWidth={9} strokeLinecap="round" />
    </g>
    <Character look={CAST.you} pose="stand" expression="happy" x={400} y={380} scale={4.6} t={0.5} headOnly facing={0} />
    <g transform="translate(612 210) rotate(-14)">
      <Globe r={92} />
    </g>
  </svg>
);

/** Bold initials over a globe, for when the name should do the work. */
const Monogram: React.FC<{letters: string}> = ({letters}) => (
  <svg viewBox="0 0 800 800" width="100%" height="100%">
    <Background />
    <g transform="translate(400 400)">
      <Globe r={290} />
    </g>
    <text x={400} y={492} textAnchor="middle" fontFamily="Inter" fontWeight={900} fontSize={300} fill={CREAM} stroke={INK} strokeWidth={30} paintOrder="stroke" letterSpacing={-12}>
      {letters}
    </text>
  </svg>
);

export const ChannelAvatar: React.FC<AvatarProps> = ({variant, letters = 'GI'}) => {
  fonts();
  return (
    <AbsoluteFill>
      {variant === 'bulb' ? <Bulb /> : variant === 'mascot' ? <Mascot /> : <Monogram letters={letters} />}
    </AbsoluteFill>
  );
};

export const sampleAvatar: AvatarProps = {variant: 'bulb'};
