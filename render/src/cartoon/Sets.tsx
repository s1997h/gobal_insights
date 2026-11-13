import React from 'react';
import {INK} from './Character';

/** Backgrounds and props, drawn in code on a 1920 x 1080 canvas. Far layers are blurred for depth. */

const WALLS = ['#b98a6e', '#9fb0c4', '#c9b3a5', '#a8735f', '#b9955f', '#9fb0c4', '#c9b3a5', '#a8735f', '#b98a6e'];

export const ParkingLot: React.FC = () => (
  <g>
    <defs>
      <linearGradient id="pl-sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#7d929c" />
        <stop offset="1" stopColor="#aab9bd" />
      </linearGradient>
      <linearGradient id="pl-road" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#585b60" />
        <stop offset="1" stopColor="#45484d" />
      </linearGradient>
      <filter id="pl-far" x="-5%" y="-5%" width="110%" height="110%">
        <feGaussianBlur stdDeviation="3.2" />
      </filter>
      <filter id="pl-mid" x="-50%" y="-5%" width="200%" height="110%">
        <feGaussianBlur stdDeviation="1.3" />
      </filter>
    </defs>
    <rect width={1920} height={1080} fill="url(#pl-sky)" />
    <g filter="url(#pl-far)">
      <path d="M 0 570 C 320 520 640 600 960 565 C 1290 530 1600 600 1920 555 L 1920 720 L 0 720 Z" fill="#5e7b5b" />
      {WALLS.map((c, i) => {
        const w = 150 + ((i * 37) % 30);
        const h = 112 + ((i * 53) % 26);
        const x = 30 + i * 220 + ((i * 29) % 40);
        const base = 650;
        return (
          <g key={i} stroke="#3a3a3a" strokeWidth={2.4} strokeLinejoin="round">
            <rect x={x} y={base - h} width={w} height={h} fill={c} />
            <path d={`M ${x - 14} ${base - h} L ${x + w / 2} ${base - h - 54} L ${x + w + 14} ${base - h} Z`} fill="#8b4636" />
          </g>
        );
      })}
      <rect x={0} y={648} width={1920} height={62} fill="#59764f" />
    </g>
    <rect x={0} y={702} width={1920} height={12} fill="#8d9095" />
    <rect x={0} y={712} width={1920} height={368} fill="url(#pl-road)" />
    {Array.from({length: 9}, (_, k) => {
      const x0 = 110 + k * 250;
      return <path key={k} d={`M ${x0} 770 L ${x0 - 70} 1080`} stroke="#d9d9d4" strokeWidth={9} opacity={0.85} />;
    })}
    <g filter="url(#pl-mid)" fill="#7b8087" stroke="#3a3a3a" strokeWidth={2}>
      <rect x={150} y={-10} width={14} height={712} />
      <rect x={960} y={-10} width={14} height={712} />
      <rect x={1770} y={-10} width={14} height={712} />
    </g>
  </g>
);

export const Car: React.FC<{x: number; y: number; scale?: number; color?: string}> = ({x, y, scale = 1, color = '#b9584a'}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`} stroke={INK} strokeWidth={2.6} strokeLinejoin="round">
    <ellipse cx={3} cy={0} rx={160} ry={10} fill="#000" opacity={0.2} stroke="none" />
    <path
      d="M -150 -22 Q -150 -54 -120 -58 L -82 -62 L -52 -102 Q -46 -110 -32 -110 L 60 -110 Q 74 -110 82 -100 L 112 -62 L 136 -58 Q 156 -54 156 -26 L 156 -16 Q 156 -8 148 -8 L -142 -8 Q -150 -8 -150 -16 Z"
      fill={color}
    />
    <path d="M -42 -98 L -66 -64 L 4 -64 L 4 -98 Z" fill="#a9c3d1" />
    <path d="M 14 -98 L 14 -64 L 98 -64 L 74 -98 Z" fill="#a9c3d1" />
    <rect x={140} y={-50} width={12} height={10} rx={3} fill="#f3e3a0" />
    {[-92, 98].map((cx) => (
      <g key={cx}>
        <circle cx={cx} cy={-8} r={26} fill={INK} />
        <circle cx={cx} cy={-8} r={11} fill="#9a9ea4" />
      </g>
    ))}
  </g>
);

/** Soft dark corners, drawn last over everything. */
export const Vignette: React.FC<{dusk?: number}> = ({dusk = 0}) => (
  <g>
    <defs>
      <radialGradient id="vig" cx="50%" cy="46%" r="72%">
        <stop offset="0.55" stopColor="#000" stopOpacity={0} />
        <stop offset="1" stopColor="#000" stopOpacity={0.45} />
      </radialGradient>
    </defs>
    {dusk > 0 && <rect width={1920} height={1080} fill="#0b1b33" opacity={dusk} />}
    <rect width={1920} height={1080} fill="url(#vig)" />
  </g>
);
