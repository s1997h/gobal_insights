import React from 'react';
import {INK, darken} from './Character';

/**
 * Sets for the episode renderer, drawn in code on a 1920 x 1080 canvas. Flat colours and no blur
 * filters, so a frame renders fast. Characters stand on y = 1000 unless a set says otherwise.
 * `layer="fg"` draws the few pieces that go in front of the actors (a shower curtain).
 */

export type SetOpt = Record<string, unknown>;
export type SetProps = {opt: SetOpt; t: number; p: number; layer: 'bg' | 'fg'};

const k = {stroke: INK, strokeWidth: 3, strokeLinejoin: 'round' as const};
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const ease = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x));

const Floor: React.FC<{color: string; y?: number; boards?: boolean}> = ({color, y = 900, boards = true}) => (
  <g>
    <rect x={0} y={y} width={1920} height={1080 - y} fill={color} />
    <rect x={0} y={y - 6} width={1920} height={12} fill={darken(color, 0.8)} />
    {boards &&
      Array.from({length: 7}, (_, i) => (
        <path key={i} d={`M ${i * 300 - 40} ${y + 10} L ${i * 300 - 140} 1080`} stroke={darken(color, 0.86)} strokeWidth={3} />
      ))}
  </g>
);

const Window: React.FC<{x: number; y: number; w: number; h: number; sky: string; night?: boolean; sun?: boolean}> = ({x, y, w, h, sky, night, sun}) => (
  <g>
    <rect x={x - 14} y={y - 14} width={w + 28} height={h + 28} rx={6} fill="#f7f1e3" {...k} />
    <rect x={x} y={y} width={w} height={h} fill={sky} {...k} />
    {night && (
      <g>
        <circle cx={x + w * 0.7} cy={y + h * 0.3} r={Math.min(w, h) * 0.12} fill="#fff6c9" />
        <circle cx={x + w * 0.66} cy={y + h * 0.27} r={Math.min(w, h) * 0.12} fill={sky} />
        {[0.2, 0.35, 0.5, 0.82, 0.14].map((f, i) => (
          <circle key={i} cx={x + w * f} cy={y + h * (0.2 + ((i * 37) % 50) / 100)} r={3} fill="#fff6c9" />
        ))}
      </g>
    )}
    {sun && <circle cx={x + w * 0.72} cy={y + h * 0.35} r={Math.min(w, h) * 0.14} fill="#ffd66b" />}
    {!night && (
      <g fill="#ffffff" opacity={0.9}>
        <ellipse cx={x + w * 0.3} cy={y + h * 0.6} rx={w * 0.14} ry={h * 0.06} />
        <ellipse cx={x + w * 0.38} cy={y + h * 0.56} rx={w * 0.1} ry={h * 0.06} />
      </g>
    )}
    <path d={`M ${x + w / 2} ${y} L ${x + w / 2} ${y + h} M ${x} ${y + h / 2} L ${x + w} ${y + h / 2}`} stroke="#f7f1e3" strokeWidth={12} />
    <rect x={x} y={y} width={w} height={h} fill="none" {...k} />
  </g>
);

const Frame: React.FC<{x: number; y: number; w: number; h: number; c: string}> = ({x, y, w, h, c}) => (
  <g>
    <rect x={x} y={y} width={w} height={h} fill="#f7f1e3" {...k} />
    <rect x={x + 10} y={y + 10} width={w - 20} height={h - 20} fill={c} />
    <path d={`M ${x + 10} ${y + h - 10} L ${x + w * 0.45} ${y + h * 0.45} L ${x + w * 0.65} ${y + h * 0.65} L ${x + w * 0.8} ${y + h * 0.5} L ${x + w - 10} ${y + h - 10} Z`} fill={darken(c, 0.7)} />
  </g>
);

const Plant: React.FC<{x: number; y: number; s?: number}> = ({x, y, s = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    {[-40, -15, 10, 35].map((a, i) => (
      <ellipse key={i} cx={Math.sin((a * Math.PI) / 180) * 50} cy={-110 - Math.cos((a * Math.PI) / 180) * 30} rx={22} ry={52} transform={`rotate(${a} ${Math.sin((a * Math.PI) / 180) * 50} ${-110 - Math.cos((a * Math.PI) / 180) * 30})`} fill={i % 2 ? '#5fae5a' : '#4c9a4a'} {...k} />
    ))}
    <path d="M -38 -70 L 38 -70 L 30 0 L -30 0 Z" fill="#d9774f" {...k} />
  </g>
);

// --------------------------------------------------------------------------------------- studio
export const Studio: React.FC<SetProps> = ({layer}) => {
  if (layer === 'fg') return null;
  return (
    <g>
      <defs>
        <radialGradient id="studio-bg" cx="50%" cy="45%" r="75%">
          <stop offset="0" stopColor="#1b3a66" />
          <stop offset="1" stopColor="#0b1b33" />
        </radialGradient>
        <pattern id="studio-dots" width="48" height="48" patternUnits="userSpaceOnUse">
          <circle cx="24" cy="24" r="2.2" fill="#ffffff" opacity="0.07" />
        </pattern>
      </defs>
      <rect width={1920} height={1080} fill="url(#studio-bg)" />
      <rect width={1920} height={1080} fill="url(#studio-dots)" />
      <ellipse cx={960} cy={1010} rx={900} ry={70} fill="#ffffff" opacity={0.05} />
    </g>
  );
};

// ------------------------------------------------------------------------------------- bedroom
export const Bedroom: React.FC<SetProps> = ({opt, layer}) => {
  if (layer === 'fg') return null;
  const night = opt.time === 'night';
  const wall = night ? '#34405f' : '#f1d3a9';
  const big = !!opt.window_big;
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      <rect x={0} y={0} width={1920} height={1080} fill={night ? '#1c2440' : '#ffffff'} opacity={night ? 0.25 : 0.0} />
      {Array.from({length: 12}, (_, i) => (
        <rect key={i} x={i * 170 + 40} y={0} width={70} height={900} fill={darken(wall, 0.96)} />
      ))}
      <Window x={big ? 760 : 1540} y={big ? 170 : 210} w={big ? 420 : 240} h={big ? 380 : 260} sky={night ? '#1d2a4a' : '#9fd6f2'} night={night} sun={!night} />
      {!big && <Frame x={260} y={240} w={200} h={150} c={night ? '#5a6e91' : '#8fc7a0'} />}
      <Floor color={night ? '#5b4a44' : '#b98656'} y={900} />
      <ellipse cx={980} cy={1010} rx={520} ry={44} fill={night ? '#6f5578' : '#d9a1a1'} opacity={0.75} />
      {night && <rect width={1920} height={1080} fill="#0b1433" opacity={0.28} />}
    </g>
  );
};

// ---------------------------------------------------------------------------------- living room
export const Living: React.FC<SetProps> = ({opt, layer}) => {
  if (layer === 'fg') return null;
  const eve = opt.time === 'evening';
  const wall = eve ? '#7c6f98' : '#cfe3d4';
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      <rect x={0} y={640} width={1920} height={260} fill={darken(wall, 0.92)} />
      <path d="M 0 640 L 1920 640" stroke={darken(wall, 0.78)} strokeWidth={8} />
      <Window x={1460} y={180} w={300} h={300} sky={eve ? '#e59a6c' : '#9fd6f2'} sun={!eve} />
      <Frame x={180} y={230} w={170} h={220} c={eve ? '#b4a3c9' : '#f2c56b'} />
      <Frame x={390} y={300} w={140} h={110} c={eve ? '#9a8bb8' : '#87b9e6'} />
      <Plant x={1780} y={905} s={1.1} />
      {eve && (
        <g>
          <rect x={1300} y={560} width={14} height={340} fill="#3a3a3e" />
          <path d="M 1250 560 L 1364 560 L 1340 470 L 1274 470 Z" fill="#ffd98a" {...k} />
          <circle cx={1307} cy={600} r={260} fill="#ffd98a" opacity={0.12} />
        </g>
      )}
      <Floor color={eve ? '#6e4d3d' : '#a7724c'} y={900} />
      <ellipse cx={900} cy={1010} rx={560} ry={46} fill={eve ? '#a9798a' : '#e8b07a'} opacity={0.8} />
    </g>
  );
};

// ---------------------------------------------------------------------------------------- street
const BUILDINGS = ['#e9a57a', '#9fb7d6', '#e3c56f', '#c58f9f', '#8fc0a6', '#d99a6c', '#a9a2d6', '#e7b98c'];
export const Street: React.FC<SetProps> = ({opt, layer, t}) => {
  if (layer === 'fg') return null;
  const dusk = !!opt.dusk;
  const shelter = !!opt.shelter;
  return (
    <g>
      <defs>
        <linearGradient id={dusk ? 'sky-dusk' : 'sky-day'} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={dusk ? '#2c2f63' : '#7fc8ee'} />
          <stop offset="1" stopColor={dusk ? '#f09a6a' : '#cfeefb'} />
        </linearGradient>
      </defs>
      <rect width={1920} height={1080} fill={`url(#${dusk ? 'sky-dusk' : 'sky-day'})`} />
      {!dusk && (
        <g fill="#ffffff" opacity={0.95}>
          {[0, 1, 2].map((i) => {
            const cx = ((i * 700 + t * 12) % 2300) - 200;
            return (
              <g key={i}>
                <ellipse cx={cx} cy={140 + i * 50} rx={110} ry={34} />
                <ellipse cx={cx + 70} cy={120 + i * 50} rx={70} ry={34} />
              </g>
            );
          })}
        </g>
      )}
      {BUILDINGS.map((c, i) => {
        const w = 220 + ((i * 47) % 60);
        const h = 420 + ((i * 113) % 260);
        const x = i * 250 - 30;
        const base = 860;
        const col = dusk ? darken(c, 0.6) : c;
        return (
          <g key={i}>
            <rect x={x} y={base - h} width={w} height={h} fill={col} {...k} />
            <rect x={x - 8} y={base - h - 18} width={w + 16} height={22} fill={darken(col, 0.8)} {...k} />
            {Array.from({length: Math.floor(h / 110)}, (_, r) =>
              [0, 1, 2].map((cIdx) => {
                const lit = dusk && (r * 3 + cIdx + i) % 3 !== 0;
                return (
                  <rect key={`${r}-${cIdx}`} x={x + 24 + cIdx * ((w - 48) / 3)} y={base - h + 30 + r * 110} width={(w - 48) / 3 - 18} height={60} rx={4}
                    fill={lit ? '#ffd98a' : dusk ? '#3a3f63' : '#d8eef8'} stroke={INK} strokeWidth={2.4} />
                );
              }),
            )}
          </g>
        );
      })}
      <rect x={0} y={856} width={1920} height={190} fill={dusk ? '#8d8a8f' : '#cfc9c1'} />
      {Array.from({length: 10}, (_, i) => <path key={i} d={`M ${i * 220} 860 L ${i * 220 - 60} 1046`} stroke={dusk ? '#7c797e' : '#bab3aa'} strokeWidth={4} />)}
      <rect x={0} y={1040} width={1920} height={12} fill="#8c8780" />
      <rect x={0} y={1050} width={1920} height={30} fill="#55585e" />
      <g>
        <rect x={1700} y={420} width={16} height={440} fill="#4a4f5a" {...k} />
        <path d="M 1708 430 Q 1708 400 1660 400 L 1630 400" fill="none" stroke="#4a4f5a" strokeWidth={14} />
        <path d="M 1600 396 L 1660 396 L 1650 420 L 1610 420 Z" fill={dusk ? '#ffe9a8' : '#e7e7e7'} {...k} />
        {dusk && <circle cx={1630} cy={430} r={70} fill="#ffe9a8" opacity={0.22} />}
      </g>
      <g>
        <rect x={150} y={640} width={26} height={220} fill="#8b5a3c" {...k} />
        <circle cx={163} cy={600} r={110} fill={dusk ? '#3f6a4a' : '#5fae5a'} {...k} />
        <circle cx={120} cy={570} r={26} fill={dusk ? '#4b7c56' : '#7cc576'} />
      </g>
      {shelter && (
        <g>
          <rect x={560} y={560} width={720} height={26} fill="#4a4f5a" {...k} />
          <rect x={580} y={586} width={14} height={300} fill="#4a4f5a" {...k} />
          <rect x={1246} y={586} width={14} height={300} fill="#4a4f5a" {...k} />
          <rect x={600} y={600} width={640} height={250} fill="#cfe9f5" opacity={0.45} {...k} />
          <rect x={1320} y={430} width={12} height={460} fill="#4a4f5a" {...k} />
          <circle cx={1326} cy={420} r={44} fill="#2ec4b6" {...k} />
          <rect x={1306} y={404} width={40} height={32} rx={4} fill="#ffffff" />
          <path d="M 1314 412 L 1338 412 M 1314 422 L 1338 422" stroke={INK} strokeWidth={4} />
        </g>
      )}
    </g>
  );
};

// ------------------------------------------------------------------------------------------ cafe
export const Cafe: React.FC<SetProps> = ({opt, layer}) => {
  if (layer === 'fg') return null;
  const eve = !!opt.evening;
  const wall = eve ? '#b9775a' : '#f0c9a0';
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      <rect x={0} y={560} width={1920} height={340} fill={darken(wall, 0.9)} />
      {Array.from({length: 24}, (_, i) => (
        <rect key={i} x={i * 80} y={560} width={80} height={340} fill="none" stroke={darken(wall, 0.8)} strokeWidth={3} />
      ))}
      <rect x={160} y={150} width={420} height={280} rx={10} fill="#2f4a3a" stroke="#7a5236" strokeWidth={14} />
      <path d="M 200 210 L 340 210 M 200 260 L 470 260 M 200 310 L 420 310 M 200 360 L 380 360" stroke="#f4f1ea" strokeWidth={6} strokeLinecap="round" opacity={0.85} />
      <Window x={1240} y={170} w={480} h={300} sky={eve ? '#33406b' : '#9fd6f2'} night={eve} sun={!eve} />
      {[620, 960, 1300].map((x) => (
        <g key={x}>
          <path d={`M ${x} 0 L ${x} 120`} stroke={INK} strokeWidth={3} />
          <path d={`M ${x - 46} 160 Q ${x} 104 ${x + 46} 160 Z`} fill={eve ? '#ffcf7a' : '#2ec4b6'} {...k} />
          {eve && <circle cx={x} cy={170} r={130} fill="#ffcf7a" opacity={0.16} />}
        </g>
      ))}
      <Plant x={1820} y={905} s={1.0} />
      <Floor color={eve ? '#5e4334' : '#8a6448'} y={900} />
      {eve && <rect width={1920} height={1080} fill="#2a1a10" opacity={0.18} />}
    </g>
  );
};

// ------------------------------------------------------------------------------------------ park
export const Park: React.FC<SetProps> = ({opt, layer, t}) => {
  if (layer === 'fg') return null;
  const grey = !!opt.grey;
  const c = (col: string, g: string) => (grey ? g : col);
  return (
    <g>
      <rect width={1920} height={1080} fill={c('#9ad7f3', '#b9bfc5')} />
      {!grey && <circle cx={1580} cy={180} r={80} fill="#ffd66b" />}
      <g fill="#ffffff" opacity={grey ? 0.5 : 0.95}>
        {[0, 1].map((i) => {
          const cx = ((i * 900 + t * 10) % 2300) - 200;
          return (
            <g key={i}>
              <ellipse cx={cx} cy={170 + i * 60} rx={120} ry={36} />
              <ellipse cx={cx + 80} cy={148 + i * 60} rx={80} ry={36} />
            </g>
          );
        })}
      </g>
      <path d="M 0 640 C 360 540 700 640 1040 590 C 1380 540 1660 620 1920 580 L 1920 1080 L 0 1080 Z" fill={c('#7cc576', '#9aa39a')} {...k} />
      <path d="M 0 760 C 420 690 820 780 1220 730 C 1520 690 1760 760 1920 730 L 1920 1080 L 0 1080 Z" fill={c('#5fae5a', '#8b938b')} {...k} />
      {[260, 640, 1400, 1760].map((x, i) => (
        <g key={x} transform={`translate(${x} ${700 + (i % 2) * 30}) scale(${0.9 + (i % 2) * 0.2})`}>
          <rect x={-12} y={-20} width={24} height={120} fill={c('#8b5a3c', '#6d6a66')} {...k} />
          <circle cx={0} cy={-80} r={84} fill={c('#4c9a4a', '#7d857d')} {...k} />
          <circle cx={-30} cy={-104} r={20} fill={c('#68b866', '#8f978f')} />
        </g>
      ))}
      <path d="M 700 1080 C 820 960 1000 900 1180 860 L 1300 860 C 1140 920 1000 990 960 1080 Z" fill={c('#e8d3a8', '#b8b2a6')} />
      <rect x={0} y={900} width={1920} height={180} fill={c('#5fae5a', '#8b938b')} opacity={0.0} />
    </g>
  );
};

// ---------------------------------------------------------------------------------------- office
export const Office: React.FC<SetProps> = ({opt, layer, t}) => {
  if (layer === 'fg') return null;
  const waiting = !!opt.waiting;
  const wall = waiting ? '#d8e3ea' : '#e6e0f0';
  const ang = t * 40;
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      <rect x={0} y={600} width={1920} height={300} fill={darken(wall, 0.93)} />
      <path d="M 0 600 L 1920 600" stroke={darken(wall, 0.8)} strokeWidth={6} />
      <Window x={1320} y={170} w={380} h={300} sky="#9fd6f2" sun />
      <g transform="translate(400 240)">
        <circle r={86} fill="#ffffff" {...k} strokeWidth={6} />
        {Array.from({length: 12}, (_, i) => (
          <path key={i} d={`M 0 -72 L 0 -62`} transform={`rotate(${i * 30})`} stroke={INK} strokeWidth={4} />
        ))}
        <path d="M 0 0 L 0 -50" transform={`rotate(${ang * 0.08})`} stroke={INK} strokeWidth={7} strokeLinecap="round" />
        <path d="M 0 0 L 0 -66" transform={`rotate(${ang})`} stroke="#e9625a" strokeWidth={4} strokeLinecap="round" />
        <circle r={7} fill={INK} />
      </g>
      {waiting && (
        <g>
          <rect x={640} y={420} width={420} height={120} rx={8} fill="#2ec4b6" {...k} />
          <text x={850} y={500} textAnchor="middle" fontSize={56} fontWeight={800} fill="#ffffff" fontFamily="Inter">WAITING</text>
        </g>
      )}
      <Plant x={160} y={905} s={1.1} />
      <Floor color={waiting ? '#9aa6b2' : '#8a7f98'} y={900} boards={!waiting} />
    </g>
  );
};

// --------------------------------------------------------------------------------------- kitchen
export const Kitchen: React.FC<SetProps> = ({layer}) => {
  if (layer === 'fg') return null;
  return (
    <g>
      <rect width={1920} height={1080} fill="#fbe2bd" />
      {Array.from({length: 30}, (_, i) => (
        <rect key={i} x={(i % 15) * 128} y={560 + Math.floor(i / 15) * 64} width={128} height={64} fill="#fff4e0" stroke="#e8cfa6" strokeWidth={3} />
      ))}
      <rect x={0} y={140} width={1920} height={240} fill="#7fb7a8" {...k} />
      {Array.from({length: 8}, (_, i) => (
        <g key={i}>
          <rect x={i * 240 + 20} y={160} width={200} height={200} rx={8} fill="#8fc7b8" {...k} />
          <circle cx={i * 240 + 200} cy={260} r={8} fill={INK} />
        </g>
      ))}
      <rect x={0} y={680} width={1920} height={40} fill="#e7d9c3" {...k} />
      <rect x={0} y={718} width={1920} height={190} fill="#7fb7a8" {...k} />
      {Array.from({length: 8}, (_, i) => (
        <rect key={i} x={i * 240 + 20} y={736} width={200} height={150} rx={8} fill="#8fc7b8" {...k} />
      ))}
      <g transform="translate(1640 0)">
        <rect x={0} y={300} width={260} height={600} rx={18} fill="#eef3f6" {...k} />
        <path d="M 0 520 L 260 520" {...k} />
        <rect x={20} y={340} width={14} height={120} rx={6} fill="#b9bec7" {...k} />
        <rect x={20} y={560} width={14} height={160} rx={6} fill="#b9bec7" {...k} />
      </g>
      <Floor color="#c49a6c" y={900} boards={false} />
    </g>
  );
};

// -------------------------------------------------------------------------------------- bathroom
export const Bathroom: React.FC<SetProps> = ({opt, layer, t}) => {
  const shower = !!opt.shower;
  if (layer === 'fg') {
    if (!shower) return null;
    return (
      <g>
        <path d={`M 380 790 ${Array.from({length: 12}, (_, i) => `Q ${430 + i * 100} ${820 + (i % 2 ? 26 : -10)} ${480 + i * 100} 790`).join(' ')} L 1580 1080 L 380 1080 Z`} fill="#f5a9b8" {...k} />
        {Array.from({length: 12}, (_, i) => (
          <path key={i} d={`M ${430 + i * 100} 820 L ${420 + i * 100} 1080`} stroke="#e48ea0" strokeWidth={6} />
        ))}
        {Array.from({length: 18}, (_, i) => {
          const x = 760 + ((i * 53) % 420);
          const y = 260 + (((t * 600 + i * 97) % 380));
          return <path key={`d${i}`} d={`M ${x} ${y} q 6 12 0 16 q -6 -4 0 -16`} fill="#9fd6f2" stroke={INK} strokeWidth={1.5} />;
        })}
      </g>
    );
  }
  return (
    <g>
      <rect width={1920} height={1080} fill="#cfe9f0" />
      {Array.from({length: 15 * 9}, (_, i) => (
        <rect key={i} x={(i % 15) * 128} y={Math.floor(i / 15) * 120} width={128} height={120} fill="none" stroke="#b6d8e1" strokeWidth={3} />
      ))}
      {shower ? (
        <g>
          <path d="M 360 780 L 1600 780" stroke="#b9bec7" strokeWidth={14} strokeLinecap="round" />
          <path d="M 1080 120 L 1080 200 Q 1080 230 1050 230 L 1000 230" fill="none" stroke="#b9bec7" strokeWidth={14} strokeLinecap="round" />
          <ellipse cx={990} cy={236} rx={46} ry={16} fill="#d7dbe2" {...k} />
        </g>
      ) : (
        <g>
          <rect x={1260} y={200} width={300} height={360} rx={140} fill="#e9f6fb" stroke="#b9bec7" strokeWidth={14} />
          <rect x={1220} y={640} width={380} height={60} rx={12} fill="#ffffff" {...k} />
          <rect x={1330} y={700} width={160} height={200} fill="#ffffff" {...k} />
          <rect x={200} y={300} width={22} height={260} fill="#b9bec7" />
          <rect x={160} y={320} width={110} height={220} rx={10} fill="#f2b84b" {...k} />
        </g>
      )}
      <Floor color="#9cc3cf" y={900} boards={false} />
    </g>
  );
};

// ---------------------------------------------------------------------------------------- drawer
export const Drawer: React.FC<SetProps> = ({opt, p, t, layer}) => {
  if (layer === 'fg') return null;
  const range = (opt.open as number[] | undefined) ?? [0, 0];
  const open = lerp(range[0], range[1], ease(p * 1.25));
  const shake = opt.shake ? Math.sin(t * 60) * 3 * (Math.sin(t * 3) > 0.3 ? 1 : 0) : 0;
  const glow = !!opt.glow;
  const phone = opt.phone !== false;
  const dy = open * 300; // the drawer front slides down/forward
  return (
    <g>
      <rect width={1920} height={1080} fill="#3d3550" />
      <rect x={0} y={0} width={1920} height={1080} fill="#1a1530" opacity={0.25} />
      {/* dresser body */}
      <rect x={300} y={140} width={1320} height={980} rx={20} fill="#b0784a" {...k} strokeWidth={5} />
      <rect x={300} y={140} width={1320} height={60} rx={14} fill="#c68a57" {...k} strokeWidth={5} />
      {/* the opening */}
      <rect x={420} y={300} width={1080} height={340} rx={10} fill="#3a2516" {...k} strokeWidth={5} />
      {/* inside, revealed as the front moves down */}
      <g>
        <rect x={440} y={320} width={1040} height={300} fill="#5b3b25" />
        {phone && (
          <g transform={`translate(${960 + shake} ${470}) rotate(-8)`}>
            <rect x={-150} y={-70} width={300} height={140} rx={22} fill="#30343c" {...k} strokeWidth={5} />
            <rect x={-136} y={-58} width={272} height={116} rx={14} fill={glow ? '#9fd6f2' : '#1d2026'} />
            {glow && <circle cx={0} cy={0} r={200} fill="#9fd6f2" opacity={0.18} />}
          </g>
        )}
        {glow && !phone && <circle cx={960} cy={470} r={260} fill="#ffd98a" opacity={0.2} />}
      </g>
      {/* drawer front */}
      <g transform={`translate(0 ${dy})`}>
        <rect x={400} y={290} width={1120} height={360} rx={14} fill="#c68a57" {...k} strokeWidth={5} />
        <rect x={440} y={330} width={1040} height={280} rx={10} fill="none" stroke={darken('#c68a57', 0.8)} strokeWidth={6} />
        <rect x={860} y={440} width={200} height={40} rx={20} fill="#e3c27a" {...k} strokeWidth={4} />
      </g>
      {/* lower drawer, hidden by the front once it slides down */}
      <rect x={400} y={720} width={1120} height={330} rx={14} fill="#c68a57" {...k} strokeWidth={5} opacity={open > 0.6 ? 0 : 1} />
      <rect x={860} y={860} width={200} height={40} rx={20} fill="#e3c27a" {...k} strokeWidth={4} opacity={open > 0.6 ? 0 : 1} />
    </g>
  );
};

export const SETS: Record<string, React.FC<SetProps>> = {
  studio: Studio,
  bedroom: Bedroom,
  living: Living,
  street: Street,
  bus_stop: (props) => <Street {...props} opt={{...props.opt, shelter: true}} />,
  cafe: Cafe,
  park: Park,
  office: Office,
  kitchen: Kitchen,
  bathroom: Bathroom,
  shower: (props) => <Bathroom {...props} opt={{...props.opt, shower: true}} />,
  drawer: Drawer,
};
