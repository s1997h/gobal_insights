import React from 'react';
import {AbsoluteFill, staticFile} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Character, INK, type Expression, type Pose} from './Character';
import {CAST} from './Cast';
import {PROPS, type PropSpec} from './Props';

/**
 * Thumbnail for money episodes, 1280 x 720: up to three words, one face, one object.
 * `object` picks the object (default: a phone that just failed to pay); `mood` picks the face.
 */
export type MoneyThumbProps = {top: string; bottom: string; amount?: string; object?: string; mood?: 'shocked' | 'joy' | 'worried'};

// object -> [prop spec, scale, dx, dy] tuned so each sits in the same spot at about the same size
const OBJECTS: Record<string, [Omit<PropSpec, 'x' | 'y'>, number, number, number]> = {
  phone_fail: [{t: 'pay_phone', at: 0, tilt: 0, bare: true}, 0.86, 0, 0],
  phone_ok: [{t: 'pay_phone', at: 0, ok: true, tilt: 0, bare: true}, 0.86, 0, 0],
  wallet: [{t: 'wallet', label: '?'}, 0.8, -70, 10],
  banknote: [{t: 'note', val: '100', glow: true}, 0.95, -80, -30],
  ledger: [{t: 'khata', lines: [['You', '240'], ['Flat 302', '118'], ['Mrs Rao', '64']], from: 0, to: 0.5}, 0.62, -70, 0],
  mystery: [{t: 'khata', mystery: true, glow: true}, 0.62, -70, -60],
  balance_locked: [{t: 'balance', at: 0, amount: '42,318'}, 0.85, -80, -70],
  cheque: [{t: 'cheque', val: '5,000'}, 1.7, -70, -40],
  calendar: [{t: 'calendar', flip: [1, 2]}, 1.05, -50, -10],
};
const FACES: Record<string, [Pose, Expression]> = {shocked: ['scared', 'shocked'], joy: ['cheer', 'joy'], worried: ['think', 'worried']};

let loaded = false;
const fonts = () => {
  if (loaded) return;
  loaded = true;
  loadFont({family: 'Inter', url: staticFile('fonts/Inter-ExtraBold.otf'), weight: '900'}).catch(() => undefined);
};

export const MoneyThumb: React.FC<MoneyThumbProps> = ({top, bottom, amount, object = 'phone_fail', mood = 'shocked'}) => {
  fonts();
  const [spec, k, dx, dy] = OBJECTS[object] ?? OBJECTS.phone_fail;
  const Obj = PROPS[spec.t as string];
  const full = {...spec, x: 0, y: 0, ...(amount && spec.t === 'pay_phone' ? {amount} : {})} as PropSpec;
  const [pose, expr] = FACES[mood] ?? FACES.shocked;
  // long words shrink to stay clear of the face
  const fit = (text: string, size: number, room: number) => Math.min(size, Math.floor(room / Math.max(1, text.length * 0.66)));
  const topSize = fit(top, 150, 640);
  const bottomSize = fit(bottom, 190, 700);
  const s = 3.1;
  const cx = 1040;
  const feet = 1190;
  const headY = feet - 252 * s;
  return (
    <AbsoluteFill>
      <svg viewBox="0 0 1280 720" width="100%" height="100%">
        <defs>
          <radialGradient id="mt-bg" cx="72%" cy="45%" r="85%">
            <stop offset="0" stopColor="#ffe066" />
            <stop offset="0.5" stopColor="#ffb238" />
            <stop offset="1" stopColor="#e9443a" />
          </radialGradient>
        </defs>
        <rect width={1280} height={720} fill="url(#mt-bg)" />
        {Array.from({length: 16}, (_, i) => {
          const a = (i / 16) * Math.PI * 2;
          const b = a + Math.PI / 32;
          return <path key={i} d={`M ${cx} ${headY} L ${cx + Math.cos(a) * 1700} ${headY + Math.sin(a) * 1700} L ${cx + Math.cos(b) * 1700} ${headY + Math.sin(b) * 1700} Z`} fill="#ffffff" opacity={0.14} />;
        })}
        <Character look={CAST.you} pose={pose} expression={expr} x={cx} y={feet} scale={s} t={0.4} />
        {[
          [cx + 122, headY - 60, 1.3],
          [cx - 130, headY - 30, 1.0],
        ].map(([x, y, k], i) => (
          <path key={i} d={`M ${x} ${y} q ${14 * k} ${30 * k} 0 ${40 * k} q ${-14 * k} ${-10 * k} 0 ${-40 * k}`} fill="#7cc7ff" stroke={INK} strokeWidth={4} />
        ))}
        <g transform={`translate(${560 + dx} ${590 + dy}) rotate(8) scale(${k})`}>
          <Obj spec={full} t={1} p={1} fps={30} />
        </g>
        <g transform="translate(40 190) rotate(-4)">
          <text x={0} y={0} fontFamily="Inter" fontWeight={900} fontSize={topSize} fill="#ffffff" stroke={INK} strokeWidth={22} paintOrder="stroke" letterSpacing={-5}>{top}</text>
          <text x={0} y={Math.round(bottomSize * 0.74 + 24)} fontFamily="Inter" fontWeight={900} fontSize={bottomSize} fill="#e9443a" stroke={INK} strokeWidth={24} paintOrder="stroke" letterSpacing={-6}>{bottom}</text>
        </g>
      </svg>
    </AbsoluteFill>
  );
};
