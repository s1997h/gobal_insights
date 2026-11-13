import React from 'react';

/**
 * A code-drawn cartoon character in the flat "doodle" style: round head, dot eyes, simple
 * clothes, thin limbs. Every part is a plain SVG shape, so one look stays identical across
 * every video and every pose costs nothing to render.
 *
 * Units: the character stands on y = 0 and is about 300 units tall; place it with x, y, scale.
 */

export type Hair = 'short' | 'spiky' | 'long' | 'bob' | 'ponytail' | 'curly' | 'bald';
export type Top = 'hoodie' | 'sweater' | 'tee';
export type Expression = 'neutral' | 'happy' | 'worried' | 'shocked' | 'zombie';
export type Pose = 'stand' | 'walk' | 'wave' | 'scared' | 'point' | 'zombie';

export interface Look {
  skin: string;
  hair: Hair;
  hairColor: string;
  top: Top;
  topColor: string;
  pants: string;
  shoes?: string;
  glasses?: boolean;
  torn?: boolean; // ragged hem, for zombies
}

export interface CharacterProps {
  look: Look;
  pose: Pose;
  expression: Expression;
  x: number;
  y: number;
  scale?: number;
  /** seconds since the shot started; drives walk cycles, waves and blinks */
  t: number;
  /** offsets blinks and cycles so a crowd doesn't move in lockstep */
  seed?: number;
  /** where the eyes look: -1 left, 0 ahead, 1 right */
  facing?: number;
  /** extra walk motion when the pose is walk or zombie */
  moving?: boolean;
}

export const INK = '#2a2a2e';
const SW = 2.6;

const darken = (hex: string, k: number) => {
  const n = parseInt(hex.replace('#', ''), 16);
  const c = (v: number) => Math.max(0, Math.min(255, Math.round(v * k)));
  return `rgb(${c((n >> 16) & 255)}, ${c((n >> 8) & 255)}, ${c(n & 255)})`;
};

const blink = (t: number, seed: number) => {
  const period = 3.1 + (seed % 5) * 0.41;
  const phase = (t + seed * 0.73) % period;
  return phase < 0.11 ? 0.12 : 1;
};

// --- hair, drawn around a head centred on 0,0 with radius 44 ---------------------------------
const hairBack = (hair: Hair, color: string) => {
  const p = {fill: color, stroke: INK, strokeWidth: SW, strokeLinejoin: 'round' as const};
  if (hair === 'long') return <path d="M -48 -8 C -52 -52 52 -52 48 -8 L 52 62 Q 0 72 -52 62 Z" {...p} />;
  if (hair === 'bob') return <path d="M -49 -8 C -52 -52 52 -52 49 -8 L 51 34 Q 0 42 -51 34 Z" {...p} />;
  if (hair === 'ponytail')
    return (
      <g>
        <ellipse cx={46} cy={6} rx={13} ry={28} transform="rotate(-22 46 6)" {...p} />
        <circle cx={40} cy={-18} r={5} fill={darken(color, 0.7)} stroke={INK} strokeWidth={SW} />
      </g>
    );
  return null;
};

const hairFront = (hair: Hair, color: string) => {
  const p = {fill: color, stroke: INK, strokeWidth: SW, strokeLinejoin: 'round' as const};
  switch (hair) {
    case 'short':
      return <path d="M -45 4 C -49 -36 -26 -55 0 -55 C 28 -55 51 -36 45 6 L 40 -10 C 30 -25 14 -30 2 -27 C -8 -21 -20 -22 -30 -29 C -36 -20 -41 -9 -45 4 Z" {...p} />;
    case 'spiky':
      return <path d="M -46 2 C -50 -36 -28 -58 0 -58 C 30 -58 52 -36 46 2 L 38 -15 L 31 -7 L 23 -24 L 13 -13 L 4 -28 L -6 -15 L -15 -28 L -24 -15 L -32 -24 L -39 -9 Z" {...p} />;
    case 'long':
      return <path d="M -46 6 C -48 -36 -24 -54 2 -54 C 28 -54 48 -36 46 6 C 41 -9 34 -20 22 -28 C 6 -21 -14 -19 -30 -31 C -38 -21 -43 -9 -46 6 Z" {...p} />;
    case 'bob':
      return <path d="M -47 10 C -49 -36 -24 -54 2 -54 C 28 -54 49 -36 47 10 C 44 -6 40 -14 30 -20 C 14 -16 -10 -16 -28 -24 C -38 -14 -44 -2 -47 10 Z" {...p} />;
    case 'ponytail':
      return <path d="M -45 0 C -48 -38 -24 -55 2 -55 C 28 -55 49 -38 45 0 C 40 -16 30 -26 16 -30 C 2 -24 -18 -24 -34 -26 C -40 -18 -43 -9 -45 0 Z" {...p} />;
    case 'curly':
      return (
        <g {...p}>
          {[-84, -56, -28, 0, 28, 56, 84].map((deg, i) => {
            const a = ((deg - 90) * Math.PI) / 180;
            return <circle key={i} cx={Math.cos(a) * 37} cy={Math.sin(a) * 37 - 10} r={14} />;
          })}
        </g>
      );
    default:
      return null;
  }
};

// --- face -----------------------------------------------------------------------------------
const Face: React.FC<{expression: Expression; facing: number; open: number; glasses?: boolean}> = ({
  expression,
  facing,
  open,
  glasses,
}) => {
  const dx = facing * 6;
  const eyes = [-14 + dx, 14 + dx];
  const line = {stroke: INK, strokeWidth: 2.4, strokeLinecap: 'round' as const, fill: 'none'};
  let brows: React.ReactNode;
  if (expression === 'worried')
    brows = (
      <>
        <path d={`M ${eyes[0] - 7} -14 L ${eyes[0] + 5} -19`} {...line} />
        <path d={`M ${eyes[1] - 5} -19 L ${eyes[1] + 7} -14`} {...line} />
      </>
    );
  else if (expression === 'shocked')
    brows = (
      <>
        <path d={`M ${eyes[0] - 7} -22 Q ${eyes[0]} -27 ${eyes[0] + 7} -22`} {...line} />
        <path d={`M ${eyes[1] - 7} -22 Q ${eyes[1]} -27 ${eyes[1] + 7} -22`} {...line} />
      </>
    );
  else if (expression === 'zombie')
    brows = (
      <>
        <path d={`M ${eyes[0] - 7} -19 L ${eyes[0] + 6} -15`} {...line} />
        <path d={`M ${eyes[1] - 6} -15 L ${eyes[1] + 7} -19`} {...line} />
      </>
    );
  else
    brows = (
      <>
        <path d={`M ${eyes[0] - 6} -16 L ${eyes[0] + 6} -16`} {...line} />
        <path d={`M ${eyes[1] - 6} -16 L ${eyes[1] + 6} -16`} {...line} />
      </>
    );

  const eye = (cx: number, i: number) => {
    if (expression === 'shocked')
      return (
        <g key={i}>
          <circle cx={cx} cy={-3} r={8.5} fill="#ffffff" stroke={INK} strokeWidth={2} />
          <circle cx={cx + dx * 0.3} cy={-3} r={3.4} fill={INK} />
        </g>
      );
    if (expression === 'zombie')
      return (
        <g key={i}>
          <circle cx={cx} cy={-3} r={7} fill="#f3f0d8" stroke={INK} strokeWidth={2} />
          <circle cx={cx + 1} cy={-2} r={1.6} fill={INK} />
        </g>
      );
    return <ellipse key={i} cx={cx} cy={-3} rx={3.6} ry={4.6 * open} fill={INK} />;
  };

  let mouth: React.ReactNode;
  const m = dx * 0.6;
  if (expression === 'happy') mouth = <path d={`M ${m - 10} 13 Q ${m} 22 ${m + 10} 13`} {...line} />;
  else if (expression === 'worried') mouth = <path d={`M ${m - 8} 19 Q ${m} 13 ${m + 8} 19`} {...line} />;
  else if (expression === 'shocked') mouth = <ellipse cx={m} cy={18} rx={6} ry={8} fill="#5b2b2b" stroke={INK} strokeWidth={2} />;
  else if (expression === 'zombie') mouth = <path d={`M ${m - 11} 17 L ${m - 5} 13 L ${m} 18 L ${m + 5} 13 L ${m + 11} 17`} {...line} />;
  else mouth = <path d={`M ${m - 6} 15 L ${m + 6} 15`} {...line} />;

  return (
    <g>
      {brows}
      {eyes.map(eye)}
      {mouth}
      {glasses && (
        <g fill="none" stroke={INK} strokeWidth={2.2}>
          <circle cx={eyes[0]} cy={-3} r={10} />
          <circle cx={eyes[1]} cy={-3} r={10} />
          <path d={`M ${eyes[0] + 10} -4 L ${eyes[1] - 10} -4`} />
        </g>
      )}
    </g>
  );
};

// --- body -----------------------------------------------------------------------------------
const ARM_LEN = 82;
const LEG_LEN = 104;

const Arm: React.FC<{x: number; angle: number; sleeve: string; hand: string; tee: boolean; top: string}> = ({
  x,
  angle,
  sleeve,
  hand,
  tee,
  top,
}) => (
  <g transform={`translate(${x} -186) rotate(${angle})`}>
    <rect x={-6.5} y={-4} width={13} height={ARM_LEN} rx={6.5} fill={sleeve} stroke={INK} strokeWidth={SW} />
    {tee && <rect x={-8} y={-6} width={16} height={30} rx={7} fill={top} stroke={INK} strokeWidth={SW} />}
    <circle cx={0} cy={ARM_LEN + 2} r={8} fill={hand} stroke={INK} strokeWidth={SW} />
  </g>
);

const Leg: React.FC<{x: number; lift: number; pants: string; shoes: string; side: number}> = ({x, lift, pants, shoes, side}) => {
  const len = LEG_LEN * (1 - 0.14 * lift);
  return (
    <g transform={`translate(${x} -112)`}>
      <rect x={-9.5} y={-4} width={19} height={len + 4} rx={6} fill={pants} stroke={INK} strokeWidth={SW} />
      <ellipse cx={side * 5} cy={len + 1} rx={15} ry={7} fill={shoes} stroke={INK} strokeWidth={SW} />
    </g>
  );
};

export const Character: React.FC<CharacterProps> = ({
  look,
  pose,
  expression,
  x,
  y,
  scale = 1,
  t,
  seed = 0,
  facing = 0,
  moving = false,
}) => {
  const tt = t + seed * 0.37;
  const walking = moving && (pose === 'walk' || pose === 'zombie');
  const stepHz = pose === 'zombie' ? 1.1 : 1.8;
  const ph = tt * Math.PI * 2 * stepHz;
  const s = Math.sin(ph);

  // arm lift: degrees outward from hanging straight down
  let liftL = 8;
  let liftR = 8;
  let bob = 0;
  let sway = 0;
  let shake = 0;
  const legLift = [0, 0];
  if (walking) {
    legLift[0] = Math.max(0, s);
    legLift[1] = Math.max(0, -s);
    bob = -4 * Math.abs(s);
    liftL += 6 * s;
    liftR -= 6 * s;
  }
  if (pose === 'wave') liftR = 150 + 18 * Math.sin(tt * Math.PI * 2 * 2.6);
  if (pose === 'point') liftR = 100;
  if (pose === 'scared') {
    liftL = 140 + 3 * Math.sin(tt * 70);
    liftR = 140 + 3 * Math.cos(tt * 63);
    shake = 1.6 * Math.sin(tt * 55);
  }
  if (pose === 'zombie') {
    liftL = 92 + 6 * Math.sin(tt * 2.1);
    liftR = 96 + 6 * Math.cos(tt * 1.9);
    sway = 3.5 * Math.sin(tt * 1.6);
  }
  if (pose === 'stand' || (pose === 'walk' && !walking)) bob = -1.2 * Math.sin(tt * 2.2); // breathing

  const shoes = look.shoes ?? INK;
  const sleeve = look.top === 'tee' ? look.skin : look.topColor;
  const torso = look.torn
    ? 'M -33 -196 Q -36 -196 -36 -186 L -33 -106 L -24 -98 L -16 -106 L -7 -96 L 2 -106 L 11 -97 L 20 -106 L 28 -98 L 33 -106 L 36 -186 Q 36 -196 33 -196 Z'
    : 'M -33 -196 Q -36 -196 -36 -186 L -33 -108 Q -33 -104 -29 -104 L 29 -104 Q 33 -104 33 -108 L 36 -186 Q 36 -196 33 -196 Z';

  return (
    <g transform={`translate(${x + shake} ${y}) scale(${scale})`}>
      <ellipse cx={0} cy={2} rx={40} ry={7} fill="#000" opacity={0.18} />
      <g transform={`rotate(${sway} 0 0) translate(0 ${bob})`}>
        <Leg x={-12} lift={legLift[0]} pants={look.pants} shoes={shoes} side={-1} />
        <Leg x={12} lift={legLift[1]} pants={look.pants} shoes={shoes} side={1} />
        <Arm x={-31} angle={liftL} sleeve={sleeve} hand={look.skin} tee={look.top === 'tee'} top={look.topColor} />
        <Arm x={31} angle={-liftR} sleeve={sleeve} hand={look.skin} tee={look.top === 'tee'} top={look.topColor} />
        <rect x={-6} y={-210} width={12} height={18} fill={look.skin} stroke={INK} strokeWidth={SW} />
        <path d={torso} fill={look.topColor} stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        {look.top === 'hoodie' && (
          <g>
            <path d="M -22 -196 Q 0 -170 22 -196 Z" fill={darken(look.topColor, 0.72)} stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
            <path d="M -7 -184 L -8 -164 M 7 -184 L 8 -164" stroke="#f4f1ea" strokeWidth={2.4} strokeLinecap="round" />
            <path d="M -20 -134 L 20 -134" stroke={darken(look.topColor, 0.7)} strokeWidth={2.2} />
          </g>
        )}
        {look.top === 'sweater' && (
          <path d="M -15 -196 L 0 -176 L 15 -196 Z" fill="#f4f1ea" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
        )}
        <g transform={`translate(0 -252) rotate(${pose === 'zombie' ? 8 : facing * 3})`}>
          {hairBack(look.hair, look.hairColor)}
          <circle cx={0} cy={0} r={44} fill={look.skin} stroke={INK} strokeWidth={SW} />
          <Face expression={expression} facing={facing} open={blink(t, seed)} glasses={look.glasses} />
          {hairFront(look.hair, look.hairColor)}
        </g>
      </g>
    </g>
  );
};
