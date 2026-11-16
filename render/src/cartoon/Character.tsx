import React from 'react';

/**
 * A code-drawn cartoon character in the flat "doodle" style: round head, dot eyes, simple
 * clothes, thin limbs. Every part is a plain SVG shape, so one look stays identical across
 * every video and every pose costs nothing to render.
 *
 * Units: the character stands on y = 0 and is about 300 units tall; place it with x, y, scale.
 * Arms are two segments solved with a little IK: a pose only says where each hand goes.
 */

export type Hair = 'short' | 'spiky' | 'long' | 'bob' | 'ponytail' | 'curly' | 'bald';
export type Top = 'hoodie' | 'sweater' | 'tee';
export type Expression = 'neutral' | 'happy' | 'worried' | 'shocked' | 'zombie' | 'bored' | 'sleep' | 'joy' | 'sad';
export type Pose =
  | 'stand' | 'walk' | 'wave' | 'scared' | 'point' | 'zombie' | 'reach' | 'phone' | 'hold' | 'read' | 'think'
  | 'cheer' | 'stretch' | 'shrug' | 'slump' | 'call'
  | 'sit' | 'sit_phone' | 'sit_read' | 'sit_look' | 'sit_desk';
export type Item = 'phone' | 'flip' | 'book' | 'map' | 'plate' | 'shampoo' | 'coffee';

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
  /** something in the hands */
  hold?: Item | null;
  /** blue phone light on the face */
  glow?: boolean;
  /** draw the head only (someone lying in bed) */
  headOnly?: boolean;
  /** shoulders bare (shower) */
  bare?: boolean;
}

export const INK = '#2a2a2e';
const SW = 2.6;
const LIMB = 13;
const UPPER = 46;
const FORE = 44;

export const darken = (hex: string, k: number) => {
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
const Face: React.FC<{expression: Expression; facing: number; look: number; open: number; glasses?: boolean}> = ({
  expression,
  facing,
  look,
  open,
  glasses,
}) => {
  const dx = facing * 6;
  const dy = look;
  const eyes = [-14 + dx, 14 + dx];
  const line = {stroke: INK, strokeWidth: 2.4, strokeLinecap: 'round' as const, fill: 'none'};
  const by = -16 + dy;
  let brows: React.ReactNode;
  if (expression === 'worried' || expression === 'sad')
    brows = (
      <>
        <path d={`M ${eyes[0] - 7} ${by + 2} L ${eyes[0] + 5} ${by - 3}`} {...line} />
        <path d={`M ${eyes[1] - 5} ${by - 3} L ${eyes[1] + 7} ${by + 2}`} {...line} />
      </>
    );
  else if (expression === 'shocked')
    brows = (
      <>
        <path d={`M ${eyes[0] - 7} ${by - 6} Q ${eyes[0]} ${by - 11} ${eyes[0] + 7} ${by - 6}`} {...line} />
        <path d={`M ${eyes[1] - 7} ${by - 6} Q ${eyes[1]} ${by - 11} ${eyes[1] + 7} ${by - 6}`} {...line} />
      </>
    );
  else if (expression === 'zombie')
    brows = (
      <>
        <path d={`M ${eyes[0] - 7} ${by - 3} L ${eyes[0] + 6} ${by + 1}`} {...line} />
        <path d={`M ${eyes[1] - 6} ${by + 1} L ${eyes[1] + 7} ${by - 3}`} {...line} />
      </>
    );
  else if (expression === 'joy' || expression === 'happy')
    brows = (
      <>
        <path d={`M ${eyes[0] - 6} ${by - 2} Q ${eyes[0]} ${by - 5} ${eyes[0] + 6} ${by - 2}`} {...line} />
        <path d={`M ${eyes[1] - 6} ${by - 2} Q ${eyes[1]} ${by - 5} ${eyes[1] + 6} ${by - 2}`} {...line} />
      </>
    );
  else if (expression === 'sleep') brows = null;
  else
    brows = (
      <>
        <path d={`M ${eyes[0] - 6} ${by} L ${eyes[0] + 6} ${by}`} {...line} />
        <path d={`M ${eyes[1] - 6} ${by} L ${eyes[1] + 6} ${by}`} {...line} />
      </>
    );

  const ey = -3 + dy;
  const eye = (cx: number, i: number) => {
    if (expression === 'shocked')
      return (
        <g key={i}>
          <circle cx={cx} cy={ey} r={8.5} fill="#ffffff" stroke={INK} strokeWidth={2} />
          <circle cx={cx + dx * 0.3} cy={ey} r={3.4} fill={INK} />
        </g>
      );
    if (expression === 'zombie')
      return (
        <g key={i}>
          <circle cx={cx} cy={ey} r={7} fill="#f3f0d8" stroke={INK} strokeWidth={2} />
          <circle cx={cx + 1} cy={ey + 1} r={1.6} fill={INK} />
        </g>
      );
    if (expression === 'sleep') return <path key={i} d={`M ${cx - 6} ${ey} Q ${cx} ${ey + 5} ${cx + 6} ${ey}`} {...line} />;
    if (expression === 'joy') return <path key={i} d={`M ${cx - 6} ${ey + 2} Q ${cx} ${ey - 6} ${cx + 6} ${ey + 2}`} {...line} />;
    if (expression === 'bored')
      return (
        <g key={i}>
          <ellipse cx={cx} cy={ey + 1.5} rx={3.6} ry={2.6 * open} fill={INK} />
          <path d={`M ${cx - 6} ${ey - 1} L ${cx + 6} ${ey - 1}`} {...line} />
        </g>
      );
    return <ellipse key={i} cx={cx} cy={ey} rx={3.6} ry={4.6 * open} fill={INK} />;
  };

  let mouth: React.ReactNode;
  const m = dx * 0.6;
  const my = dy * 0.6;
  if (expression === 'happy') mouth = <path d={`M ${m - 10} ${13 + my} Q ${m} ${22 + my} ${m + 10} ${13 + my}`} {...line} />;
  else if (expression === 'joy')
    mouth = <path d={`M ${m - 12} ${12 + my} Q ${m} ${28 + my} ${m + 12} ${12 + my} Z`} fill="#7a3434" stroke={INK} strokeWidth={2.2} strokeLinejoin="round" />;
  else if (expression === 'worried') mouth = <path d={`M ${m - 8} ${19 + my} Q ${m} ${13 + my} ${m + 8} ${19 + my}`} {...line} />;
  else if (expression === 'sad') mouth = <path d={`M ${m - 9} ${21 + my} Q ${m} ${12 + my} ${m + 9} ${21 + my}`} {...line} />;
  else if (expression === 'shocked') mouth = <ellipse cx={m} cy={18 + my} rx={6} ry={8} fill="#5b2b2b" stroke={INK} strokeWidth={2} />;
  else if (expression === 'zombie') mouth = <path d={`M ${m - 11} ${17 + my} L ${m - 5} ${13 + my} L ${m} ${18 + my} L ${m + 5} ${13 + my} L ${m + 11} ${17 + my}`} {...line} />;
  else if (expression === 'sleep') mouth = <ellipse cx={m} cy={17 + my} rx={3.5} ry={2.6} fill="#5b2b2b" />;
  else if (expression === 'bored') mouth = <path d={`M ${m - 7} ${16 + my} L ${m + 6} ${15 + my}`} {...line} />;
  else mouth = <path d={`M ${m - 6} ${15 + my} L ${m + 6} ${15 + my}`} {...line} />;

  return (
    <g>
      {brows}
      {eyes.map(eye)}
      {(expression === 'joy' || expression === 'happy') && (
        <g opacity={0.35} fill="#e46a6a">
          <ellipse cx={eyes[0] - 10} cy={8 + dy} rx={7} ry={4} />
          <ellipse cx={eyes[1] + 10} cy={8 + dy} rx={7} ry={4} />
        </g>
      )}
      {expression === 'sad' && <path d={`M ${eyes[1] + 3} ${ey + 7} q 3 6 0 9 q -3 -3 0 -9`} fill="#7cc7ff" stroke={INK} strokeWidth={1.4} />}
      {mouth}
      {glasses && (
        <g fill="none" stroke={INK} strokeWidth={2.2}>
          <circle cx={eyes[0]} cy={ey} r={10} />
          <circle cx={eyes[1]} cy={ey} r={10} />
          <path d={`M ${eyes[0] + 10} ${ey - 1} L ${eyes[1] - 10} ${ey - 1}`} />
        </g>
      )}
    </g>
  );
};

// --- held items, drawn centred on 0,0 at the hand ----------------------------------------------
export const ItemShape: React.FC<{item: Item; glow?: boolean}> = ({item, glow}) => {
  const k = {stroke: INK, strokeWidth: 2.4, strokeLinejoin: 'round' as const};
  switch (item) {
    case 'phone':
      return (
        <g>
          <rect x={-15} y={-27} width={30} height={52} rx={6} fill="#30343c" {...k} />
          <circle cx={-6} cy={-18} r={3} fill="#5b616c" />
          {glow && <rect x={-13} y={-25} width={26} height={48} rx={5} fill="#9fd8ff" opacity={0.15} />}
        </g>
      );
    case 'flip':
      return (
        <g>
          <rect x={-11} y={-30} width={22} height={30} rx={4} fill="#8a96a8" {...k} />
          <rect x={-11} y={-2} width={22} height={30} rx={4} fill="#7a8698" {...k} />
          <rect x={-6} y={-25} width={12} height={14} rx={2} fill="#bfe3c9" stroke={INK} strokeWidth={1.4} />
        </g>
      );
    case 'book':
      return (
        <g>
          <path d="M -40 -22 Q -20 -30 0 -22 L 0 18 Q -20 10 -40 18 Z" fill="#fbf6ea" {...k} />
          <path d="M 40 -22 Q 20 -30 0 -22 L 0 18 Q 20 10 40 18 Z" fill="#fbf6ea" {...k} />
          <path d="M -34 -12 L -8 -14 M -34 -4 L -8 -6 M -34 4 L -8 2 M 8 -14 L 34 -12 M 8 -6 L 34 -4 M 8 2 L 34 4" stroke="#9a9488" strokeWidth={1.6} />
          <path d="M -42 18 L -42 24 Q -20 16 0 24 Q 20 16 42 24 L 42 18" fill="#c0573f" {...k} />
        </g>
      );
    case 'map':
      return (
        <g>
          <path d="M -46 -30 L -16 -36 L 16 -30 L 46 -36 L 46 26 L 16 32 L -16 26 L -46 32 Z" fill="#f5ecd2" {...k} />
          <path d="M -16 -36 L -16 26 M 16 -30 L 16 32" stroke="#b9ad8c" strokeWidth={1.6} />
          <path d="M -38 14 C -20 -6 0 18 14 -8 S 34 -20 40 -14" stroke="#d2574a" strokeWidth={3} fill="none" strokeDasharray="6 5" />
          <circle cx={40} cy={-14} r={5} fill="#d2574a" stroke={INK} strokeWidth={1.6} />
        </g>
      );
    case 'plate':
      return (
        <g>
          <ellipse cx={0} cy={0} rx={44} ry={13} fill="#f7f7f2" {...k} />
          <ellipse cx={-10} cy={-4} rx={14} ry={6} fill="#fffdf6" stroke={INK} strokeWidth={1.6} />
          <circle cx={-10} cy={-5} r={4.5} fill="#f2b43b" />
          <rect x={6} y={-8} width={22} height={7} rx={3} fill="#c27a45" stroke={INK} strokeWidth={1.6} />
        </g>
      );
    case 'shampoo':
      return (
        <g>
          <rect x={-14} y={-34} width={28} height={58} rx={9} fill="#6fc0b7" {...k} />
          <rect x={-6} y={-46} width={12} height={13} rx={2} fill="#f1f1f1" {...k} />
          <rect x={-10} y={-18} width={20} height={22} rx={3} fill="#fbf6ea" stroke={INK} strokeWidth={1.4} />
          <path d="M -6 -12 L 6 -12 M -6 -6 L 6 -6 M -6 0 L 3 0" stroke="#9a9488" strokeWidth={1.4} />
        </g>
      );
    case 'coffee':
      return (
        <g>
          <path d="M -16 -18 L 16 -18 L 13 20 Q 0 25 -13 20 Z" fill="#fbf6ea" {...k} />
          <rect x={-18} y={-24} width={36} height={8} rx={3} fill="#7b5236" {...k} />
          <rect x={-15} y={-4} width={30} height={10} fill="#c27a45" />
        </g>
      );
    default:
      return null;
  }
};

// --- two-bone arm ------------------------------------------------------------------------------
type V = [number, number];
const solveElbow = (s: V, t: V, side: number, bendDown = true): V => {
  const dx = t[0] - s[0];
  const dy = t[1] - s[1];
  let d = Math.hypot(dx, dy);
  d = Math.max(Math.abs(UPPER - FORE) + 2, Math.min(UPPER + FORE - 0.5, d));
  const base = Math.atan2(dy, dx);
  const a = Math.acos(Math.max(-1, Math.min(1, (UPPER * UPPER + d * d - FORE * FORE) / (2 * UPPER * d))));
  const c1: V = [s[0] + UPPER * Math.cos(base + a), s[1] + UPPER * Math.sin(base + a)];
  const c2: V = [s[0] + UPPER * Math.cos(base - a), s[1] + UPPER * Math.sin(base - a)];
  // prefer the elbow that sits outward (away from the body) and low
  const score = (c: V) => c[0] * side * 1.0 + (bendDown ? c[1] * 0.35 : -c[1] * 0.35);
  return score(c1) >= score(c2) ? c1 : c2;
};

const Arm: React.FC<{s: V; h: V; side: number; sleeve: string; skin: string; tee: boolean; top: string}> = ({s, h, side, sleeve, skin, tee, top}) => {
  // keep the hand within reach
  const dx = h[0] - s[0];
  const dy = h[1] - s[1];
  const d = Math.hypot(dx, dy);
  const max = UPPER + FORE - 1;
  const hand: V = d > max ? [s[0] + (dx / d) * max, s[1] + (dy / d) * max] : h;
  const e = solveElbow(s, hand, side);
  const path = `M ${s[0]} ${s[1]} L ${e[0]} ${e[1]} L ${hand[0]} ${hand[1]}`;
  const sleevePath = tee ? `M ${s[0]} ${s[1]} L ${s[0] + (e[0] - s[0]) * 0.55} ${s[1] + (e[1] - s[1]) * 0.55}` : null;
  return (
    <g strokeLinecap="round" strokeLinejoin="round" fill="none">
      <path d={path} stroke={INK} strokeWidth={LIMB + SW * 2} />
      <path d={path} stroke={tee ? skin : sleeve} strokeWidth={LIMB} />
      {sleevePath && (
        <>
          <path d={sleevePath} stroke={INK} strokeWidth={LIMB + 6 + SW * 2} />
          <path d={sleevePath} stroke={top} strokeWidth={LIMB + 6} />
        </>
      )}
      <circle cx={hand[0]} cy={hand[1]} r={8} fill={skin} stroke={INK} strokeWidth={SW} />
    </g>
  );
};

const Leg: React.FC<{x: number; top: number; len: number; pants: string; shoes: string; side: number}> = ({x, top, len, pants, shoes, side}) => (
  <g transform={`translate(${x} ${top})`}>
    <rect x={-9.5} y={-4} width={19} height={len + 4} rx={6} fill={pants} stroke={INK} strokeWidth={SW} />
    <ellipse cx={side * 5} cy={len + 1} rx={15} ry={7} fill={shoes} stroke={INK} strokeWidth={SW} />
  </g>
);

const LEG_LEN = 104;

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
  hold = null,
  glow = false,
  headOnly = false,
  bare = false,
}) => {
  const tt = t + seed * 0.37;
  const walking = moving && (pose === 'walk' || pose === 'zombie');
  const stepHz = pose === 'zombie' ? 1.1 : 1.8;
  const ph = tt * Math.PI * 2 * stepHz;
  const s = Math.sin(ph);
  const sitting = pose.startsWith('sit');
  const drop = sitting ? 50 : pose === 'slump' ? 6 : 0;

  // hand targets in body coordinates (before the sitting drop)
  const sh: {L: V; R: V} = {L: [-31, -186], R: [31, -186]};
  let R: V = [50, -106];
  let L: V = [-50, -106];
  let bob = 0;
  let sway = 0;
  let shake = 0;
  let lookDown = 0;
  let headTilt = facing * 3;
  const legLift = [0, 0];
  if (walking) {
    legLift[0] = Math.max(0, s);
    legLift[1] = Math.max(0, -s);
    bob = -4 * Math.abs(s);
    R = [48, -108 + 7 * s];
    L = [-48, -108 - 7 * s];
  }
  const breathe = -1.2 * Math.sin(tt * 2.2);
  switch (pose) {
    case 'wave':
      R = [72 + 14 * Math.sin(tt * Math.PI * 2 * 2.4), -292];
      break;
    case 'point':
      if (facing < 0) L = [-118, -206];
      else R = [118, -206];
      break;
    case 'scared':
      R = [42 + 2 * Math.sin(tt * 70), -282];
      L = [-42 + 2 * Math.cos(tt * 63), -282];
      shake = 1.6 * Math.sin(tt * 55);
      break;
    case 'zombie':
      R = [40, -172 + 5 * Math.sin(tt * 2.1)];
      L = [-40, -168 + 5 * Math.cos(tt * 1.9)];
      sway = 3.5 * Math.sin(tt * 1.6);
      headTilt = 8;
      break;
    case 'reach':
      R = [22, -114];
      headTilt = -6;
      lookDown = 4;
      break;
    case 'phone':
    case 'sit_phone':
      R = [10, -150];
      L = [-10, -150];
      lookDown = 6;
      headTilt = 4;
      break;
    case 'hold':
      R = [34, -152];
      break;
    case 'read':
    case 'sit_read':
      R = [30, -150];
      L = [-30, -150];
      lookDown = 5;
      break;
    case 'think':
      R = [12, -218];
      L = [16, -146];
      headTilt = -5;
      break;
    case 'cheer':
      R = [80, -300 + 6 * Math.sin(tt * 9)];
      L = [-80, -300 + 6 * Math.cos(tt * 9)];
      bob = -6 * Math.abs(Math.sin(tt * 4.5));
      break;
    case 'stretch':
      R = [74, -326];
      L = [-74, -326];
      break;
    case 'shrug':
      R = [80, -150];
      L = [-80, -150];
      break;
    case 'slump':
      R = [40, -96];
      L = [-40, -96];
      headTilt = -8;
      lookDown = 4;
      break;
    case 'call':
      R = [40, -256];
      headTilt = 6;
      break;
    case 'sit':
      R = [32, -108];
      L = [-32, -108];
      break;
    case 'sit_look':
      R = [26, -110];
      L = [-34, -108];
      lookDown = 7;
      headTilt = -6;
      break;
    case 'sit_desk':
      R = [56, -128];
      L = [-56, -128];
      break;
  }
  if (!walking && pose !== 'cheer') bob = breathe;

  const shoes = look.shoes ?? INK;
  const top = bare ? look.skin : look.topColor;
  const topKind: Top = bare ? 'tee' : look.top;
  const sleeve = topKind === 'tee' ? look.skin : top;
  const torso = look.torn
    ? 'M -33 -196 Q -36 -196 -36 -186 L -33 -106 L -24 -98 L -16 -106 L -7 -96 L 2 -106 L 11 -97 L 20 -106 L 28 -98 L 33 -106 L 36 -186 Q 36 -196 33 -196 Z'
    : 'M -33 -196 Q -36 -196 -36 -186 L -33 -108 Q -33 -104 -29 -104 L 29 -104 Q 33 -104 33 -108 L 36 -186 Q 36 -196 33 -196 Z';

  const head = (
    <g transform={`translate(0 -252) rotate(${headTilt})`}>
      {hairBack(look.hair, look.hairColor)}
      <circle cx={0} cy={0} r={44} fill={look.skin} stroke={INK} strokeWidth={SW} />
      <Face expression={expression} facing={facing} look={lookDown} open={blink(t, seed)} glasses={look.glasses} />
      {hairFront(look.hair, look.hairColor)}
      {glow && <ellipse cx={0} cy={10} rx={46} ry={40} fill="url(#phoneGlow)" />}
    </g>
  );

  if (headOnly) {
    return (
      <g transform={`translate(${x} ${y}) scale(${scale}) translate(0 252)`}>
        {head}
      </g>
    );
  }

  const twoHanded = hold && (pose === 'phone' || pose === 'sit_phone' || pose === 'read' || pose === 'sit_read');
  const itemAt: V = twoHanded ? [(R[0] + L[0]) / 2, Math.min(R[1], L[1]) - 8] : [R[0], R[1] - 10];
  const lowerBody = (v: V): V => [v[0], v[1] + drop];
  const Rd = lowerBody(R);
  const Ld = lowerBody(L);
  const shR = lowerBody(sh.R);
  const shL = lowerBody(sh.L);
  const legTop = sitting ? -62 : -112;
  const legLen = sitting ? 60 : LEG_LEN;

  return (
    <g transform={`translate(${x + shake} ${y}) scale(${scale})`}>
      <ellipse cx={0} cy={2} rx={40} ry={7} fill="#000" opacity={0.18} />
      <g transform={`rotate(${sway} 0 0) translate(0 ${bob})`}>
        <Leg x={sitting ? -16 : -12} top={legTop} len={legLen * (1 - 0.14 * legLift[0])} pants={look.pants} shoes={shoes} side={-1} />
        <Leg x={sitting ? 16 : 12} top={legTop} len={legLen * (1 - 0.14 * legLift[1])} pants={look.pants} shoes={shoes} side={1} />
        {sitting && <rect x={-34} y={-70} width={68} height={22} rx={9} fill={look.pants} stroke={INK} strokeWidth={SW} />}
        <g transform={`translate(0 ${drop})`}>
          <rect x={-6} y={-210} width={12} height={18} fill={look.skin} stroke={INK} strokeWidth={SW} />
          <path d={torso} fill={top} stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
          {topKind === 'hoodie' && (
            <g>
              <path d="M -22 -196 Q 0 -170 22 -196 Z" fill={darken(top, 0.72)} stroke={INK} strokeWidth={SW} strokeLinejoin="round" />
              <path d="M -7 -184 L -8 -164 M 7 -184 L 8 -164" stroke="#f4f1ea" strokeWidth={2.4} strokeLinecap="round" />
              <path d="M -20 -134 L 20 -134" stroke={darken(top, 0.7)} strokeWidth={2.2} />
            </g>
          )}
          {topKind === 'sweater' && <path d="M -15 -196 L 0 -176 L 15 -196 Z" fill="#f4f1ea" stroke={INK} strokeWidth={SW} strokeLinejoin="round" />}
          {head}
        </g>
        <Arm s={shL} h={Ld} side={-1} sleeve={sleeve} skin={look.skin} tee={topKind === 'tee'} top={top} />
        <Arm s={shR} h={Rd} side={1} sleeve={sleeve} skin={look.skin} tee={topKind === 'tee'} top={top} />
        {hold && (
          <g transform={`translate(${itemAt[0]} ${itemAt[1] + drop})`}>
            <ItemShape item={hold} glow={glow} />
          </g>
        )}
        {hold && (
          <g>
            <circle cx={Rd[0]} cy={Rd[1]} r={8} fill={look.skin} stroke={INK} strokeWidth={SW} />
            {twoHanded && <circle cx={Ld[0]} cy={Ld[1]} r={8} fill={look.skin} stroke={INK} strokeWidth={SW} />}
          </g>
        )}
      </g>
    </g>
  );
};
