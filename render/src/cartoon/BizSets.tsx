import React from 'react';
import {INK, darken} from './Character';
import type {SetProps} from './Places';
import type {PropSpec} from './Props';

/**
 * Sets and props for company stories: a lab, a factory floor, a boardroom, a store, a garage and a
 * launch stage. Each set takes `opt.sign`, a short name (a company, a product) written on the wall,
 * the banner or the screen, so the viewer always knows whose story this is.
 */

const k = {stroke: INK, strokeWidth: 3, strokeLinejoin: 'round' as const};
const FONT = 'Inter, Helvetica Neue, Arial, sans-serif';
const sign = (opt: SetProps['opt']) => String(opt.sign ?? '').toUpperCase().slice(0, 14);
const fit = (text: string, size: number, room: number) => Math.min(size, room / Math.max(1, text.length * 0.74));

const Floor: React.FC<{c: string; y?: number}> = ({c, y = 900}) => (
  <g>
    <rect x={0} y={y} width={1920} height={1080 - y} fill={c} />
    <path d={`M 0 ${y} L 1920 ${y}`} stroke={INK} strokeWidth={4} />
  </g>
);

const WallSign: React.FC<{x: number; y: number; text: string; bg?: string; fg?: string; w?: number}> = ({x, y, text, bg = '#fffaf0', fg = INK, w = 460}) =>
  text ? (
    <g transform={`translate(${x} ${y})`}>
      <rect x={-w / 2} y={-52} width={w} height={104} rx={14} fill={bg} {...k} strokeWidth={5} />
      <text x={0} y={fit(text, 64, w - 50) * 0.36} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(text, 64, w - 50)} fill={fg}>{text}</text>
    </g>
  ) : null;

// ------------------------------------------------------------------------------------------ lab
export const Lab: React.FC<SetProps> = ({opt, layer, t}) => {
  if (layer === 'fg') return null;
  const wall = '#dfe8e4';
  const blink = Math.sin(t * 5) > 0;
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      <rect x={0} y={640} width={1920} height={260} fill={darken(wall, 0.92)} />
      {/* pegboard with tools */}
      <rect x={110} y={150} width={520} height={330} rx={10} fill="#c9a26b" {...k} />
      {Array.from({length: 40}, (_, i) => <circle key={i} cx={150 + (i % 10) * 50} cy={190 + Math.floor(i / 10) * 80} r={4} fill="#8a6a3c" />)}
      <path d="M 200 220 L 200 330 M 180 220 L 220 220" stroke={INK} strokeWidth={10} strokeLinecap="round" />
      <path d="M 300 230 L 360 330" stroke="#8a8f98" strokeWidth={14} strokeLinecap="round" />
      <circle cx={300} cy={230} r={20} fill="none" stroke="#8a8f98" strokeWidth={10} />
      <rect x={430} y={220} width={120} height={26} rx={6} fill="#e9625a" {...k} />
      <rect x={460} y={246} width={20} height={110} fill="#8a8f98" {...k} />
      {/* blueprint */}
      <rect x={1240} y={150} width={500} height={320} rx={8} fill="#3d6fb6" {...k} />
      <g stroke="#cfe2ff" strokeWidth={4} fill="none">
        <rect x={1300} y={210} width={220} height={140} rx={10} />
        <circle cx={1410} cy={280} r={46} />
        <path d="M 1560 220 L 1690 220 M 1560 260 L 1690 260 M 1560 300 L 1650 300 M 1300 400 L 1690 400" />
      </g>
      <WallSign x={935} y={230} text={sign(opt)} w={500} />
      {/* workbench with a prototype */}
      <rect x={160} y={700} width={1600} height={44} rx={6} fill="#b98a5a" {...k} />
      {[220, 940, 1660].map((x) => <rect key={x} x={x} y={744} width={40} height={156} fill="#8a6a3c" {...k} />)}
      <rect x={1180} y={600} width={220} height={100} rx={10} fill="#4a4f5a" {...k} />
      <circle cx={1240} cy={650} r={30} fill="#1d2230" {...k} />
      <circle cx={1360} cy={630} r={9} fill={blink ? '#e9625a' : '#6b2a2a'} />
      <path d="M 1400 640 C 1470 600 1500 700 1560 690" stroke={INK} strokeWidth={5} fill="none" />
      <rect x={320} y={640} width={150} height={60} rx={6} fill="#fffaf0" {...k} />
      <path d="M 340 660 L 450 660 M 340 680 L 420 680" stroke="#9aa0aa" strokeWidth={5} />
      {/* lamp */}
      <path d="M 800 0 L 800 110" stroke={INK} strokeWidth={5} />
      <path d="M 730 170 L 760 110 L 840 110 L 870 170 Z" fill="#f2b84b" {...k} />
      <path d="M 730 170 L 620 640 L 980 640 L 870 170 Z" fill="#fff4c2" opacity={0.22} />
      <Floor c="#9a8f86" />
    </g>
  );
};

// -------------------------------------------------------------------------------------- factory
export const Factory: React.FC<SetProps> = ({opt, layer, t}) => {
  if (layer === 'fg') return null;
  const wall = '#cfd6dc';
  const shift = (t * 90) % 260;
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      {[150, 600, 1470].map((x) => (
        <g key={x}>
          <path d={`M ${x} 480 L ${x} 250 A 150 150 0 0 1 ${x + 300} 250 L ${x + 300} 480 Z`} fill="#bfe3f5" {...k} strokeWidth={5} />
          <path d={`M ${x + 150} 100 L ${x + 150} 480 M ${x} 300 L ${x + 300} 300 M ${x} 390 L ${x + 300} 390`} stroke={INK} strokeWidth={4} />
        </g>
      ))}
      <WallSign x={1185} y={290} text={sign(opt)} w={440} bg="#27336b" fg="#fffaf0" />
      {/* pipes */}
      <path d="M 0 70 L 1920 70" stroke="#8a8f98" strokeWidth={34} />
      <path d="M 0 70 L 1920 70" stroke={INK} strokeWidth={3} transform="translate(0 -17)" />
      <path d="M 0 70 L 1920 70" stroke={INK} strokeWidth={3} transform="translate(0 17)" />
      {[420, 1380].map((x) => <rect key={x} x={x} y={46} width={30} height={48} fill="#6d727b" {...k} />)}
      {/* conveyor with boxes */}
      <rect x={0} y={560} width={1920} height={330} fill={darken(wall, 0.9)} />
      <g>
        {Array.from({length: 9}, (_, i) => {
          const x = -260 + i * 260 + shift;
          return (
            <g key={i} transform={`translate(${x} 0)`}>
              <rect x={0} y={640} width={130} height={110} rx={6} fill={['#e3c56f', '#e9a57a', '#9fb7d6'][i % 3]} {...k} />
              <path d="M 0 676 L 130 676" stroke={INK} strokeWidth={3} />
              <rect x={45} y={640} width={40} height={36} fill="#fffaf0" {...k} strokeWidth={2} />
            </g>
          );
        })}
      </g>
      <rect x={-10} y={750} width={1940} height={40} rx={18} fill="#3f444d" {...k} />
      {Array.from({length: 16}, (_, i) => (
        <g key={i} transform={`translate(${60 + i * 120} 770) rotate(${t * 180})`}>
          <circle r={15} fill="#8a8f98" {...k} />
          <path d="M -15 0 L 15 0" stroke={INK} strokeWidth={3} />
        </g>
      ))}
      {[200, 960, 1720].map((x) => <rect key={x} x={x - 16} y={790} width={32} height={110} fill="#5a5f69" {...k} />)}
      <Floor c="#8d939c" />
      {Array.from({length: 12}, (_, i) => <path key={i} d={`M ${i * 170} 1080 L ${i * 170 + 70} 1000 L ${i * 170 + 150} 1000 L ${i * 170 + 80} 1080 Z`} fill="#f2b84b" opacity={0.55} />)}
    </g>
  );
};

// ------------------------------------------------------------------------------------ boardroom
export const Boardroom: React.FC<SetProps> = ({opt, layer}) => {
  if (layer === 'fg') return null;
  const wall = '#5b4636';
  const down = !!opt.down;
  const line = down ? 'M 40 60 L 130 80 L 220 70 L 310 150 L 400 210' : 'M 40 210 L 130 170 L 220 180 L 310 100 L 400 50';
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      {Array.from({length: 9}, (_, i) => <path key={i} d={`M ${i * 240} 0 L ${i * 240} 900`} stroke={darken(wall, 0.85)} strokeWidth={5} />)}
      {/* skyline window */}
      <rect x={110} y={140} width={760} height={420} rx={8} fill="#9fd6f2" {...k} strokeWidth={6} />
      {[150, 250, 330, 450, 540, 660, 760].map((x, i) => (
        <rect key={x} x={x} y={560 - (150 + ((i * 67) % 190))} width={80} height={150 + ((i * 67) % 190)} fill={['#6f86a8', '#8aa0bd', '#57708f'][i % 3]} stroke={INK} strokeWidth={2} />
      ))}
      <path d="M 490 140 L 490 560" stroke={INK} strokeWidth={6} />
      {/* screen with a chart */}
      <g transform="translate(1180 150)">
        <rect x={0} y={0} width={560} height={400} rx={12} fill="#fffaf0" {...k} strokeWidth={6} />
        <text x={280} y={70} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(sign(opt) || 'SALES', 52, 480)} fill={INK}>{sign(opt) || 'SALES'}</text>
        <g transform="translate(60 110)">
          <path d="M 0 0 L 0 240 L 440 240" stroke={INK} strokeWidth={5} fill="none" />
          <path d={line} stroke={down ? '#e9625a' : '#2ec4b6'} strokeWidth={12} fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </g>
      </g>
      {/* long table and chairs */}
      {[300, 620, 1300, 1620].map((x) => <rect key={x} x={x - 60} y={640} width={120} height={170} rx={24} fill="#2a2a2e" {...k} />)}
      <path d="M 120 800 L 1800 800 L 1880 900 L 40 900 Z" fill="#8a5a3a" {...k} strokeWidth={5} />
      <rect x={40} y={900} width={1840} height={34} fill="#6d452b" {...k} />
      <Floor c="#3d3f52" y={934} />
    </g>
  );
};

// ---------------------------------------------------------------------------------------- store
const PRODUCTS = ['#e9625a', '#2ec4b6', '#f2b84b', '#5b8def', '#c58f9f', '#8fc0a6'];
export const Store: React.FC<SetProps> = ({opt, layer}) => {
  if (layer === 'fg') return null;
  const wall = '#f6ead6';
  const name = sign(opt);
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      <rect x={0} y={0} width={1920} height={130} fill="#e9625a" />
      <path d="M 0 130 L 1920 130" stroke={INK} strokeWidth={5} />
      <text x={960} y={92} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(name || 'OPEN', 78, 1500)} fill="#fffaf0">{name || 'OPEN'}</text>
      {[200, 330, 460].map((y, r) => (
        <g key={y}>
          {Array.from({length: 22}, (_, i) => {
            const h = 70 + ((i * 31 + r * 17) % 40);
            const gap = i === 7 || i === 15;
            return gap ? null : <rect key={i} x={70 + i * 82} y={y + 110 - h} width={62} height={h} rx={6} fill={PRODUCTS[(i + r * 2) % PRODUCTS.length]} {...k} strokeWidth={2.5} />;
          })}
          <rect x={40} y={y + 110} width={1840} height={20} fill="#b98a5a" {...k} />
          {Array.from({length: 6}, (_, i) => <rect key={i} x={150 + i * 310} y={y + 112} width={70} height={30} rx={4} fill="#fffaf0" {...k} strokeWidth={2} />)}
        </g>
      ))}
      {/* checkout */}
      <rect x={1330} y={690} width={520} height={210} rx={10} fill="#27336b" {...k} strokeWidth={5} />
      <rect x={1310} y={672} width={560} height={30} rx={8} fill="#8a8f98" {...k} />
      <rect x={1640} y={590} width={130} height={84} rx={8} fill="#2a2a2e" {...k} />
      <rect x={1654} y={602} width={102} height={46} rx={4} fill="#9fe6c9" />
      <Floor c="#d9cdb8" />
      {Array.from({length: 8}, (_, i) => <path key={i} d={`M ${i * 260} 900 L ${i * 260 - 60} 1080`} stroke="#c4b79f" strokeWidth={4} />)}
    </g>
  );
};

// --------------------------------------------------------------------------------------- garage
export const Garage: React.FC<SetProps> = ({opt, layer, t}) => {
  if (layer === 'fg') return null;
  const wall = '#c9c2b6';
  const sway = Math.sin(t * 1.4) * 4;
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      {Array.from({length: 7}, (_, r) => Array.from({length: 13}, (_, c) => (
        <rect key={`${r}-${c}`} x={c * 160 - (r % 2) * 80} y={r * 130} width={160} height={130} fill="none" stroke={darken(wall, 0.9)} strokeWidth={3} />
      )))}
      {/* roller door, half open to the street */}
      <rect x={1080} y={170} width={700} height={730} fill="#bfe3f5" {...k} strokeWidth={6} />
      <rect x={1080} y={720} width={700} height={180} fill="#9bbf8f" />
      <path d="M 1080 720 L 1780 720" stroke={INK} strokeWidth={3} />
      {Array.from({length: 7}, (_, i) => <rect key={i} x={1080} y={170 + i * 54} width={700} height={54} fill="#8a8f98" {...k} />)}
      {/* workbench with a first product */}
      <rect x={120} y={690} width={760} height={40} rx={6} fill="#b98a5a" {...k} />
      {[160, 820].map((x) => <rect key={x} x={x} y={730} width={36} height={170} fill="#8a6a3c" {...k} />)}
      <rect x={220} y={590} width={190} height={100} rx={8} fill="#fffaf0" {...k} />
      <rect x={240} y={608} width={150} height={56} rx={4} fill="#27336b" />
      <rect x={520} y={620} width={110} height={70} rx={6} fill="#e3c56f" {...k} />
      <rect x={640} y={640} width={90} height={50} rx={6} fill="#e9a57a" {...k} />
      <rect x={150} y={330} width={520} height={24} fill="#8a6a3c" {...k} />
      {[190, 290, 380, 500, 580].map((x, i) => <rect key={x} x={x} y={330 - 60 - (i % 2) * 30} width={64} height={60 + (i % 2) * 30} rx={6} fill={PRODUCTS[i]} {...k} strokeWidth={2.5} />)}
      {sign(opt) && (
        <g transform="translate(410 470) rotate(-3)">
          <rect x={-220} y={-52} width={440} height={104} fill="#d9b178" {...k} strokeWidth={5} />
          <text x={0} y={22} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(sign(opt), 62, 400)} fill={INK}>{sign(opt)}</text>
        </g>
      )}
      <g transform={`translate(${940 + sway} 0)`}>
        <path d="M 0 0 L 0 120" stroke={INK} strokeWidth={4} />
        <circle cx={0} cy={146} r={28} fill="#fff4c2" {...k} />
      </g>
      <Floor c="#8f8a82" />
      <ellipse cx={520} cy={990} rx={260} ry={26} fill="#000" opacity={0.08} />
    </g>
  );
};

// ---------------------------------------------------------------------------------------- stage
export const Stage: React.FC<SetProps> = ({opt, layer, t}) => {
  if (layer === 'fg') {
    return (
      <g fill="#070b16">
        {Array.from({length: 13}, (_, i) => {
          const x = 40 + i * 155;
          const y = 1010 + ((i * 37) % 40);
          return (
            <g key={i}>
              <circle cx={x} cy={y} r={44} />
              <path d={`M ${x - 80} 1090 Q ${x} ${y + 10} ${x + 80} 1090 Z`} />
            </g>
          );
        })}
      </g>
    );
  }
  const name = sign(opt) || 'ONE MORE THING';
  const glow = 0.16 + Math.sin(t * 2) * 0.04;
  return (
    <g>
      <rect width={1920} height={1080} fill="#101630" />
      <path d="M 300 0 L 60 900 L 820 900 Z" fill="#fff4c2" opacity={glow} />
      <path d="M 1620 0 L 1100 900 L 1860 900 Z" fill="#9fd6f2" opacity={glow} />
      <rect x={470} y={130} width={980} height={470} rx={16} fill="#fffaf0" {...k} strokeWidth={8} />
      <text x={960} y={365 + fit(name, 130, 880) * 0.34} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(name, 130, 880)} fill={INK}>{name}</text>
      <rect x={0} y={880} width={1920} height={200} fill="#2a2140" />
      <path d="M 0 880 L 1920 880" stroke="#f2b84b" strokeWidth={8} />
      <ellipse cx={960} cy={1000} rx={520} ry={40} fill="#fff4c2" opacity={0.14} />
    </g>
  );
};

export const BIZ_SETS: Record<string, React.FC<SetProps>> = {
  lab: Lab,
  factory: Factory,
  boardroom: Boardroom,
  store: Store,
  garage: Garage,
  stage: Stage,
};

// ---------------------------------------------------------------------------------------- props
type P = {spec: PropSpec; t: number; p: number; fps: number};

/** A boxed product on a plinth, with its name on the box. PropView places and scales it. */
const Product: React.FC<P> = ({spec, t}) => {
  const label = String(spec.label ?? '').toUpperCase().slice(0, 12);
  const bob = Math.sin(t * 2.2) * 6;
  return (
    <g>
      <rect x={-120} y={-250} width={240} height={250} rx={8} fill="#fffaf0" {...k} strokeWidth={5} />
      <rect x={-140} y={-270} width={280} height={30} rx={8} fill="#e3ddd0" {...k} />
      <g transform={`translate(0 ${-420 + bob})`}>
        {Array.from({length: 10}, (_, i) => <path key={i} d="M 0 -150 L 0 -128" transform={`rotate(${i * 36 + t * 14})`} stroke="#f2b84b" strokeWidth={7} strokeLinecap="round" />)}
        <rect x={-105} y={-105} width={210} height={210} rx={18} fill="#2ec4b6" {...k} strokeWidth={6} />
        <rect x={-105} y={-30} width={210} height={64} fill="#fffaf0" stroke={INK} strokeWidth={4} />
        <text x={0} y={fit(label, 44, 190) * 0.36 + 2} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(label, 44, 190)} fill={INK}>{label}</text>
      </g>
    </g>
  );
};

/** An easel chart whose line draws itself up or down over the shot. */
const ChartBoard: React.FC<P> = ({spec, p}) => {
  const down = !!spec.down;
  const label = String(spec.label ?? '').toUpperCase().slice(0, 14);
  const pts = down ? [[0, 30], [80, 50], [160, 40], [240, 130], [320, 200]] : [[0, 200], [80, 160], [160, 170], [240, 90], [320, 30]];
  const q = Math.max(0, Math.min(1, (p - 0.1) / 0.5));
  const n = Math.max(1, Math.round(q * (pts.length - 1)));
  const d = pts.slice(0, n + 1).map(([x, y], i) => `${i ? 'L' : 'M'} ${x} ${y}`).join(' ');
  return (
    <g>
      <path d="M -150 0 L -90 -420 M 150 0 L 90 -420 M 0 0 L 0 -380" stroke="#8a6a3c" strokeWidth={14} strokeLinecap="round" />
      <rect x={-220} y={-640} width={440} height={360} rx={12} fill="#fffaf0" {...k} strokeWidth={6} />
      <text x={0} y={-580} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(label, 44, 400)} fill={INK}>{label}</text>
      <g transform="translate(-160 -540)">
        <path d="M 0 0 L 0 220 L 330 220" stroke={INK} strokeWidth={5} fill="none" />
        <path d={d} stroke={down ? '#e9625a' : '#2ec4b6'} strokeWidth={12} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </g>
    </g>
  );
};

export const BIZ_PROPS: Record<string, React.FC<P>> = {product: Product, chart_board: ChartBoard};
