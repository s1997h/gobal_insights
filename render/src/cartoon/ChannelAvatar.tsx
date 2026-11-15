import React from 'react';
import {AbsoluteFill, staticFile} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Character, INK} from './Character';
import {CAST} from './Cast';

/**
 * Channel profile picture, 800 x 800. YouTube shows it as a circle as small as 98 px, so everything
 * that matters sits inside the middle 80% and reads at thumbnail size: one shape, bold outlines.
 */

export type AvatarProps = {variant: 'bulb' | 'mascot' | 'monogram' | 'lab' | 'labmascot'; letters?: string};

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


/** A lab flask with "IF" on the glass and a question mark rising out of it: "The If Lab". */
const Flask: React.FC<{label?: string; s?: number}> = ({label = 'IF', s = 1}) => (
  <g transform={`scale(${s})`}>
    <defs>
      <clipPath id={`flask-in-${s}`}>
        <path d="M -48 -150 L -48 -40 L -205 220 Q -215 250 -185 250 L 185 250 Q 215 250 205 220 L 48 -40 L 48 -150 Z" />
      </clipPath>
    </defs>
    <path d="M -48 -150 L -48 -40 L -205 220 Q -215 250 -185 250 L 185 250 Q 215 250 205 220 L 48 -40 L 48 -150 Z" fill="#e8f6fb" />
    <g clipPath={`url(#flask-in-${s})`}>
      <path d="M -260 60 Q -170 30 -85 60 T 85 60 T 260 60 L 260 300 L -260 300 Z" fill={TEAL} />
      <path d="M -260 60 Q -170 30 -85 60 T 85 60 T 260 60" fill="none" stroke="#7fe0d6" strokeWidth={10} />
      {[[-110, 190, 14], [-40, 150, 10], [70, 200, 16], [120, 130, 9], [10, 100, 12]].map(([x, y, r], i) => (
        <circle key={i} cx={x} cy={y} r={r} fill="#ffffff" opacity={0.55} />
      ))}
      <path d="M -150 -10 L -110 -10 L -170 120" fill="none" stroke="#ffffff" strokeWidth={16} strokeLinecap="round" opacity={0.6} />
    </g>
    <path d="M -48 -150 L -48 -40 L -205 220 Q -215 250 -185 250 L 185 250 Q 215 250 205 220 L 48 -40 L 48 -150" fill="none" stroke={INK} strokeWidth={14} strokeLinejoin="round" />
    <rect x={-72} y={-178} width={144} height={36} rx={14} fill="#e8f6fb" stroke={INK} strokeWidth={14} />
    <text x={0} y={205} textAnchor="middle" fontFamily="Inter" fontWeight={900} fontSize={150} fill={CREAM} stroke={INK} strokeWidth={16} paintOrder="stroke" letterSpacing={-4}>
      {label}
    </text>
  </g>
);

const Lab: React.FC = () => (
  <svg viewBox="0 0 800 800" width="100%" height="100%">
    <Background />
    <Rays cx={400} cy={300} r0={230} r1={300} n={7} />
    {[[372, 268, 13], [418, 238, 10], [392, 212, 8]].map(([x, y, r], i) => (
      <circle key={i} cx={x} cy={y} r={r} fill={GOLD} stroke={INK} strokeWidth={5} />
    ))}
    <text x={400} y={205} textAnchor="middle" fontFamily="Inter" fontWeight={900} fontSize={230} fill={GOLD} stroke={INK} strokeWidth={18} paintOrder="stroke">
      ?
    </text>
    <g transform="translate(400 445)">
      <Flask />
    </g>
  </svg>
);

const LabMascot: React.FC = () => (
  <svg viewBox="0 0 800 800" width="100%" height="100%">
    <defs>
      <radialGradient id="av-teal" cx="50%" cy="40%" r="70%">
        <stop offset="0" stopColor="#5fd8cc" />
        <stop offset="1" stopColor="#1f8f84" />
      </radialGradient>
    </defs>
    <rect width={800} height={800} fill="url(#av-teal)" />
    {Array.from({length: 14}, (_, i) => {
      const a = (i / 14) * Math.PI * 2;
      const b = a + Math.PI / 28;
      return <path key={i} d={`M 400 380 L ${400 + Math.cos(a) * 900} ${380 + Math.sin(a) * 900} L ${400 + Math.cos(b) * 900} ${380 + Math.sin(b) * 900} Z`} fill="#ffffff" opacity={0.12} />;
    })}
    <g stroke={INK} strokeWidth={10} strokeLinejoin="round">
      <path d="M 170 820 Q 180 610 400 600 Q 620 610 630 820 Z" fill="#f4f1ea" />
      <path d="M 330 604 L 400 700 L 470 604" fill="none" />
      <path d="M 400 700 L 400 820" />
    </g>
    <Character look={CAST.you} pose="stand" expression="happy" x={400} y={380} scale={4.6} t={0.5} headOnly facing={0} />
    {/* lab goggles pushed up on the forehead */}
    <g stroke={INK} strokeWidth={10}>
      <path d="M 205 250 Q 400 205 595 250" fill="none" stroke="#3a3f4a" strokeWidth={22} />
      <rect x={262} y={196} width={120} height={78} rx={30} fill="#bfe7f5" />
      <rect x={418} y={196} width={120} height={78} rx={30} fill="#bfe7f5" />
      <path d="M 382 232 L 418 232" />
    </g>
    <g transform="translate(615 600) rotate(10)">
      <Flask s={0.42} label="?" />
    </g>
  </svg>
);

export const ChannelAvatar: React.FC<AvatarProps> = ({variant, letters = 'GI'}) => {
  fonts();
  return (
    <AbsoluteFill>
      {variant === 'bulb' ? <Bulb /> : variant === 'mascot' ? <Mascot /> : variant === 'lab' ? <Lab /> : variant === 'labmascot' ? <LabMascot /> : <Monogram letters={letters} />}
    </AbsoluteFill>
  );
};

export const sampleAvatar: AvatarProps = {variant: 'bulb'};
