import React from 'react';
import {INK, darken} from './Character';
import type {SetProps} from './Places';

/**
 * Sets for money and business stories: an Indian bazaar street, a kirana shop, a data centre,
 * a 1970s pub and a bank front. Each takes `tod` (time of day) so one street can run from dawn
 * to midnight, and drifts its far layer a little with shot progress for depth.
 */

const k = {stroke: INK, strokeWidth: 3, strokeLinejoin: 'round' as const};
const FONT = 'Inter, Helvetica Neue, Arial, sans-serif';

export type Tod = 'dawn' | 'day' | 'dusk' | 'night' | 'sepia';
const SKY: Record<Tod, [string, string]> = {
  dawn: ['#f39a7a', '#fde3c0'],
  day: ['#6fc0ec', '#d6f1fc'],
  dusk: ['#3b3f7a', '#f09a6a'],
  night: ['#0a1130', '#2a3670'],
  sepia: ['#d2ad78', '#f3e3c4'],
};

export const Sky: React.FC<{tod: Tod; t: number}> = ({tod, t}) => {
  const [a, b] = SKY[tod];
  const dark = tod === 'night';
  return (
    <g>
      <defs>
        <linearGradient id={`msky-${tod}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={a} />
          <stop offset="1" stopColor={b} />
        </linearGradient>
      </defs>
      <rect width={1920} height={1080} fill={`url(#msky-${tod})`} />
      {dark &&
        Array.from({length: 46}, (_, i) => {
          const x = (i * 397) % 1920;
          const y = (i * 151) % 460;
          const tw = 0.5 + 0.5 * Math.sin(t * 2 + i);
          return <circle key={i} cx={x} cy={y} r={1.6 + (i % 3)} fill="#fff" opacity={0.35 + tw * 0.5} />;
        })}
      {dark && (
        <g>
          <circle cx={1540} cy={170} r={150} fill="#fff7d6" opacity={0.08} />
          <circle cx={1540} cy={170} r={70} fill="#fff7d6" />
          <circle cx={1568} cy={150} r={62} fill={a} />
        </g>
      )}
      {tod === 'day' && (
        <g>
          <circle cx={1560} cy={160} r={130} fill="#fff6b8" opacity={0.35} />
          <circle cx={1560} cy={160} r={72} fill="#ffe27a" />
        </g>
      )}
      {tod === 'dawn' && (
        <g>
          <circle cx={1480} cy={420} r={200} fill="#ffe6a8" opacity={0.35} />
          <circle cx={1480} cy={420} r={96} fill="#ffd27a" />
        </g>
      )}
      {tod === 'dusk' && (
        <g>
          <circle cx={380} cy={470} r={220} fill="#ffb27a" opacity={0.3} />
          <circle cx={380} cy={470} r={100} fill="#ff8f5a" />
        </g>
      )}
      {(tod === 'day' || tod === 'dawn' || tod === 'sepia') && (
        <g fill="#ffffff" opacity={tod === 'sepia' ? 0.55 : 0.92}>
          {[0, 1, 2].map((i) => {
            const cx = ((i * 760 + t * 14) % 2400) - 240;
            return (
              <g key={i}>
                <ellipse cx={cx} cy={150 + i * 56} rx={120} ry={36} />
                <ellipse cx={cx + 80} cy={128 + i * 56} rx={76} ry={36} />
                <ellipse cx={cx - 70} cy={140 + i * 56} rx={60} ry={26} />
              </g>
            );
          })}
        </g>
      )}
    </g>
  );
};

const SHOPS: {name: string; c: string; aw: string}[] = [
  {name: 'MEDICAL', c: '#e8f1ea', aw: '#3f9d6b'},
  {name: 'KIRANA', c: '#f6e2b5', aw: '#e9625a'},
  {name: 'MOBILE', c: '#dfe6f5', aw: '#5b8def'},
  {name: 'SWEETS', c: '#f7d9c9', aw: '#f2b84b'},
  {name: 'TAILOR', c: '#e7dcf2', aw: '#8a63b8'},
  {name: 'BAKERY', c: '#f3e9d2', aw: '#2ec4b6'},
];

// --------------------------------------------------------------------------------------- bazaar
export const Bazaar: React.FC<SetProps> = ({opt, layer, t, p}) => {
  if (layer === 'fg') return null;
  const tod = ((opt.tod as Tod) ?? 'day') as Tod;
  const dark = tod === 'night' || tod === 'dusk';
  const shade = tod === 'night' ? 0.5 : tod === 'dusk' ? 0.72 : 1;
  const shut = !!opt.shut; // shutters down on every shop
  const drift = -40 * p;
  return (
    <g>
      <Sky tod={tod} t={t} />
      {/* far skyline, drifts for depth */}
      <g transform={`translate(${drift} 0)`} opacity={0.9}>
        {Array.from({length: 13}, (_, i) => {
          const w = 130 + ((i * 53) % 90);
          const h = 150 + ((i * 97) % 170);
          const x = i * 165 - 60;
          const c = darken(['#c6d6ea', '#d3cde6', '#e0d3c6'][i % 3], shade);
          return (
            <g key={i}>
              <rect x={x} y={600 - h} width={w} height={h + 20} fill={c} opacity={0.85} />
              {i % 3 === 0 && <rect x={x + w / 2 - 22} y={600 - h - 34} width={44} height={34} rx={6} fill={darken(c, 0.8)} />}
              {Array.from({length: Math.floor(h / 70)}, (_, r) => (
                <rect key={r} x={x + 16} y={600 - h + 22 + r * 70} width={w - 32} height={22} fill={dark && (r + i) % 2 === 0 ? '#ffd98a' : darken(c, 0.93)} opacity={0.9} />
              ))}
            </g>
          );
        })}
      </g>
      {/* shop row */}
      {SHOPS.map((s, i) => {
        const x = i * 330 - 30;
        const body = darken(s.c, shade);
        const aw = darken(s.aw, shade);
        const lit = dark && !shut;
        return (
          <g key={i}>
            <rect x={x} y={420} width={322} height={440} fill={body} {...k} />
            <rect x={x - 6} y={400} width={334} height={26} fill={darken(body, 0.82)} {...k} />
            <rect x={x + 26} y={434} width={270} height={70} rx={8} fill={darken('#fffaf0', shade)} {...k} />
            <text x={x + 161} y={484} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={42} fill={darken(s.aw, 0.7)} letterSpacing={2}>{s.name}</text>
            {/* opening */}
            <rect x={x + 30} y={590} width={262} height={270} fill={shut ? darken('#aab2bd', shade) : lit ? '#ffe9a8' : '#3b3340'} {...k} />
            {shut
              ? Array.from({length: 9}, (_, r) => <path key={r} d={`M ${x + 30} ${616 + r * 28} L ${x + 292} ${616 + r * 28}`} stroke={darken('#7d8590', shade)} strokeWidth={4} />)
              : [0, 1, 2].map((r) => (
                  <g key={r}>
                    <rect x={x + 44} y={640 + r * 62} width={234} height={8} fill={lit ? '#b98a4a' : '#5a4f5e'} />
                    {Array.from({length: 7}, (_, c) => (
                      <rect key={c} x={x + 50 + c * 32} y={612 + r * 62} width={22} height={28} rx={3}
                        fill={darken(['#e9625a', '#2ec4b6', '#f2b84b', '#5b8def', '#ffffff'][(c + r + i) % 5], lit ? 1 : 0.62)} />
                    ))}
                  </g>
                ))}
            {/* awning */}
            <path d={`M ${x + 6} 522 L ${x + 316} 522 L ${x + 336} 598 L ${x - 14} 598 Z`} fill={aw} {...k} />
            {Array.from({length: 5}, (_, c) => (
              <path key={c} d={`M ${x + 40 + c * 62} 522 L ${x + 30 + c * 66} 598 L ${x + 62 + c * 66} 598 L ${x + 70 + c * 62} 522 Z`} fill="#ffffff" opacity={0.85 * shade + 0.1} />
            ))}
            <path d={`M ${x - 14} 598 ${Array.from({length: 10}, (_, c) => `q 17.5 26 35 0`).join(' ')}`} fill={aw} {...k} />
          </g>
        );
      })}
      {/* wires and bunting */}
      <path d="M -20 330 Q 480 420 960 340 T 1940 330" fill="none" stroke={INK} strokeWidth={3} opacity={0.7} />
      <path d="M -20 372 Q 600 440 1200 372 T 1940 384" fill="none" stroke={INK} strokeWidth={3} opacity={0.5} />
      {Array.from({length: 15}, (_, i) => {
        const x = 60 + i * 128;
        const y = 340 + 44 * Math.sin((x / 1920) * Math.PI * 2) + 22;
        const sw = Math.sin(t * 2 + i) * 6;
        return <path key={i} d={`M ${x - 18} ${y} L ${x + 18} ${y} L ${x + sw} ${y + 40} Z`} fill={darken(['#e9625a', '#f2b84b', '#2ec4b6', '#5b8def'][i % 4], shade)} stroke={INK} strokeWidth={2} />;
      })}
      {/* pavement and road */}
      <rect x={0} y={856} width={1920} height={190} fill={darken('#d4cdc3', shade)} />
      {Array.from({length: 10}, (_, i) => <path key={i} d={`M ${i * 220} 860 L ${i * 220 - 60} 1046`} stroke={darken('#bdb5aa', shade)} strokeWidth={4} />)}
      <rect x={0} y={1040} width={1920} height={12} fill={darken('#8c8780', shade)} />
      <rect x={0} y={1050} width={1920} height={30} fill={darken('#55585e', shade)} />
      {/* lamp post */}
      <g>
        <rect x={1846} y={380} width={16} height={480} fill="#4a4f5a" {...k} />
        <path d="M 1854 392 Q 1854 356 1800 356 L 1770 356" fill="none" stroke="#4a4f5a" strokeWidth={14} />
        <path d="M 1738 352 L 1800 352 L 1790 378 L 1748 378 Z" fill={dark ? '#ffe9a8' : '#e7e7e7'} {...k} />
        {dark && <path d="M 1740 378 L 1798 378 L 1900 900 L 1620 900 Z" fill="#ffe9a8" opacity={0.16} />}
      </g>
    </g>
  );
};

// --------------------------------------------------------------------------------------- kirana
export const Kirana: React.FC<SetProps> = ({opt, layer, t}) => {
  const tod = ((opt.tod as Tod) ?? 'day') as Tod;
  const night = tod === 'night' || tod === 'dusk';
  if (layer === 'fg') {
    return (
      <g>
        {/* counter, in front of the shopkeeper */}
        <rect x={1010} y={742} width={910} height={48} rx={8} fill="#c98f52" {...k} />
        <rect x={1030} y={790} width={890} height={290} fill="#a8713c" {...k} />
        {Array.from({length: 5}, (_, i) => <rect key={i} x={1060 + i * 172} y={820} width={140} height={220} rx={8} fill="#b9814a" stroke={INK} strokeWidth={2.4} />)}
        {/* jars on the counter */}
        {[0, 1, 2].map((i) => (
          <g key={i} transform={`translate(${1090 + i * 86} 742)`}>
            <rect x={-30} y={-92} width={60} height={92} rx={12} fill="#e9f6fb" opacity={0.85} {...k} />
            <rect x={-26} y={-60} width={52} height={56} rx={8} fill={['#e9625a', '#f2b84b', '#8a5a3c'][i]} opacity={0.85} />
            <rect x={-32} y={-106} width={64} height={18} rx={6} fill="#e9625a" {...k} />
          </g>
        ))}
        {/* scale */}
        <g transform="translate(1790 742)">
          <rect x={-56} y={-26} width={112} height={26} rx={6} fill="#6d7480" {...k} />
          <rect x={-70} y={-40} width={140} height={14} rx={6} fill="#cfd6df" {...k} />
          <rect x={-24} y={-20} width={48} height={14} rx={3} fill="#bdf2c9" />
        </g>
      </g>
    );
  }
  const wall = night ? '#e6cf9c' : '#f3e2b8';
  return (
    <g>
      <rect width={1920} height={1080} fill={wall} />
      <rect x={0} y={0} width={1920} height={70} fill={darken(wall, 0.85)} />
      {/* shelves */}
      {[0, 1, 2, 3].map((r) => (
        <g key={r}>
          <rect x={60} y={250 + r * 150} width={1800} height={16} fill="#a8713c" {...k} />
          {Array.from({length: 26}, (_, c) => {
            const kind = (c * 7 + r * 3) % 5;
            const col = ['#e9625a', '#2ec4b6', '#f2b84b', '#5b8def', '#8a63b8', '#ffffff', '#3f9d6b'][(c + r * 2) % 7];
            const x = 86 + c * 68;
            const y = 250 + r * 150;
            if (kind === 0) return <g key={c}><rect x={x} y={y - 96} width={48} height={96} rx={10} fill="#e9f6fb" opacity={0.9} {...k} strokeWidth={2.4} /><rect x={x + 4} y={y - 62} width={40} height={58} rx={6} fill={col} opacity={0.85} /><rect x={x - 2} y={y - 108} width={52} height={16} rx={5} fill={darken(col, 0.8)} stroke={INK} strokeWidth={2} /></g>;
            if (kind === 1) return <g key={c}><rect x={x} y={y - 82} width={52} height={82} rx={4} fill={col} {...k} strokeWidth={2.4} /><rect x={x + 8} y={y - 62} width={36} height={22} rx={3} fill="#fff" opacity={0.85} /></g>;
            if (kind === 2) return <g key={c}><path d={`M ${x + 6} ${y} L ${x + 2} ${y - 70} Q ${x + 26} ${y - 92} ${x + 50} ${y - 70} L ${x + 46} ${y} Z`} fill={col} {...k} strokeWidth={2.4} /><circle cx={x + 26} cy={y - 40} r={12} fill="#fff" opacity={0.8} /></g>;
            if (kind === 3) return <g key={c}><rect x={x + 6} y={y - 104} width={36} height={104} rx={10} fill={col} {...k} strokeWidth={2.4} /><rect x={x + 16} y={y - 120} width={16} height={18} fill={darken(col, 0.7)} stroke={INK} strokeWidth={2} /></g>;
            return <g key={c}><rect x={x} y={y - 54} width={54} height={54} rx={6} fill={col} {...k} strokeWidth={2.4} /><rect x={x} y={y - 108} width={54} height={50} rx={6} fill={darken(col, 0.85)} {...k} strokeWidth={2.4} /></g>;
          })}
        </g>
      ))}
      {/* hanging snack strips */}
      {Array.from({length: 9}, (_, i) => {
        const x = 150 + i * 96;
        const sw = Math.sin(t * 1.3 + i) * 3;
        return (
          <g key={i} transform={`rotate(${sw} ${x} 70)`}>
            <path d={`M ${x} 70 L ${x} 96`} stroke={INK} strokeWidth={2} />
            {[0, 1, 2].map((j) => (
              <rect key={j} x={x - 24} y={96 + j * 44} width={48} height={40} rx={6} fill={['#f2b84b', '#e9625a', '#2ec4b6', '#5b8def'][(i + j) % 4]} stroke={INK} strokeWidth={2.2} />
            ))}
          </g>
        );
      })}
      {/* bulb */}
      <path d="M 1500 0 L 1500 96" stroke={INK} strokeWidth={3} />
      <circle cx={1500} cy={112} r={22} fill={night ? '#fff3b8' : '#f7f1e3'} {...k} />
      {night && <circle cx={1500} cy={112} r={180} fill="#fff3b8" opacity={0.2} />}
      {/* floor */}
      <rect x={0} y={900} width={1920} height={180} fill="#b99a78" />
      <rect x={0} y={894} width={1920} height={12} fill="#9a7d5c" />
      {Array.from({length: 12}, (_, i) => <path key={i} d={`M ${i * 180} 906 L ${i * 180 - 70} 1080`} stroke="#a88a68" strokeWidth={3} />)}
    </g>
  );
};

// ----------------------------------------------------------------------------------- data centre
export const DataCentre: React.FC<SetProps> = ({opt, layer, t, p}) => {
  if (layer === 'fg') return null;
  const faultAt = (opt.fault as number) ?? 2; // shot progress when rack 3 fails; >1 = never
  const failed = p >= faultAt;
  const allDown = !!opt.down;
  return (
    <g>
      <rect width={1920} height={1080} fill="#0c1730" />
      <rect x={0} y={880} width={1920} height={200} fill="#152548" />
      {Array.from({length: 14}, (_, i) => <path key={i} d={`M ${i * 160 - 80} 880 L ${i * 220 - 500} 1080`} stroke="#1f3564" strokeWidth={3} />)}
      {[0, 1, 2].map((i) => <path key={i} d={`M 0 ${930 + i * 50} L 1920 ${930 + i * 50}`} stroke="#1f3564" strokeWidth={3} />)}
      {/* ceiling lights */}
      {[0, 1, 2, 3].map((i) => (
        <g key={i}>
          <rect x={160 + i * 460} y={40} width={300} height={16} rx={8} fill="#bfe6ff" />
          <path d={`M ${160 + i * 460} 56 L ${460 + i * 460} 56 L ${560 + i * 460} 880 L ${60 + i * 460} 880 Z`} fill="#8fd3ff" opacity={0.05} />
        </g>
      ))}
      {/* racks */}
      {Array.from({length: 6}, (_, r) => {
        const x = 110 + r * 290;
        const bad = r === 3 && failed;
        const dead = allDown || bad;
        return (
          <g key={r}>
            <rect x={x} y={170} width={250} height={720} rx={10} fill="#22304f" {...k} />
            <rect x={x + 14} y={186} width={222} height={688} rx={6} fill="#141d33" />
            {Array.from({length: 11}, (_, u) => {
              const y = 200 + u * 60;
              return (
                <g key={u}>
                  <rect x={x + 22} y={y} width={206} height={46} rx={5} fill={bad && u === 4 ? '#5a1f1f' : '#2b3a5e'} stroke={INK} strokeWidth={2} />
                  {Array.from({length: 6}, (_, l) => {
                    const on = Math.sin(t * (5 + ((u * 3 + l * 7 + r) % 6)) + u * 1.7 + l * 2.3 + r) > 0;
                    const col = dead ? (bad && u === 4 && Math.sin(t * 18) > 0 ? '#ff4b3e' : '#3a2530') : on ? '#49e6a0' : '#1d5f47';
                    return <circle key={l} cx={x + 42 + l * 18} cy={y + 23} r={5} fill={col} />;
                  })}
                  <rect x={x + 160} y={y + 12} width={56} height={22} rx={3} fill="#1a2440" />
                  {[0, 1, 2].map((v) => <path key={v} d={`M ${x + 166 + v * 16} ${y + 16} L ${x + 166 + v * 16} ${y + 30}`} stroke="#3d5080" strokeWidth={4} />)}
                </g>
              );
            })}
            {bad && <rect x={x} y={170} width={250} height={720} rx={10} fill="#ff4b3e" opacity={0.1 + 0.08 * Math.sin(t * 18)} />}
          </g>
        );
      })}
      {/* cable trays */}
      <rect x={60} y={120} width={1800} height={22} fill="#2b3a5e" {...k} />
      {Array.from({length: 12}, (_, i) => <path key={i} d={`M ${170 + i * 145} 142 q 20 30 0 44`} fill="none" stroke={['#f2b84b', '#5b8def', '#2ec4b6'][i % 3]} strokeWidth={5} />)}
    </g>
  );
};

// ------------------------------------------------------------------------------------------ pub
export const Pub: React.FC<SetProps> = ({layer, t}) => {
  if (layer === 'fg') {
    return (
      <g>
        <rect x={960} y={720} width={960} height={50} rx={10} fill="#6b3f22" {...k} />
        <rect x={980} y={770} width={940} height={310} fill="#54301a" {...k} />
        {Array.from({length: 5}, (_, i) => <rect key={i} x={1010 + i * 180} y={800} width={150} height={250} rx={10} fill="#623920" stroke={INK} strokeWidth={2.4} />)}
        <rect x={980} y={1010} width={940} height={16} rx={8} fill="#c9a24a" {...k} strokeWidth={2.4} />
        {/* beer taps */}
        {[0, 1, 2].map((i) => (
          <g key={i} transform={`translate(${1500 + i * 70} 720)`}>
            <rect x={-8} y={-110} width={16} height={110} fill="#c9a24a" {...k} strokeWidth={2.4} />
            <rect x={-16} y={-150} width={32} height={48} rx={8} fill={['#2f4a3a', '#7a2f2f', '#1f1f24'][i]} {...k} strokeWidth={2.4} />
            <path d="M 8 -70 L 34 -70 L 34 -52" fill="none" stroke="#c9a24a" strokeWidth={8} />
          </g>
        ))}
        {/* pint */}
        <g transform="translate(1180 720)">
          <path d="M -26 0 L -30 -92 L 30 -92 L 26 0 Z" fill="#2a1a12" {...k} />
          <path d="M -30 -92 L 30 -92 L 29 -70 L -29 -70 Z" fill="#f6ecd2" {...k} />
        </g>
      </g>
    );
  }
  return (
    <g>
      <rect width={1920} height={1080} fill="#b88a55" />
      <rect x={0} y={560} width={1920} height={340} fill="#7a4b28" />
      {Array.from({length: 13}, (_, i) => <rect key={i} x={i * 150 + 14} y={590} width={122} height={280} rx={6} fill="#6b3f22" stroke={darken('#6b3f22', 0.8)} strokeWidth={4} />)}
      <rect x={0} y={548} width={1920} height={20} fill="#54301a" />
      {/* back bar with bottles */}
      <rect x={1040} y={150} width={820} height={380} rx={10} fill="#54301a" {...k} />
      <rect x={1064} y={174} width={772} height={332} fill="#e9d9b2" opacity={0.35} />
      {[0, 1].map((r) => (
        <g key={r}>
          <rect x={1064} y={320 + r * 170} width={772} height={14} fill="#3b2012" />
          {Array.from({length: 13}, (_, c) => {
            const x = 1090 + c * 57;
            const y = 320 + r * 170;
            const col = ['#2f6b4a', '#7a2f2f', '#c9a24a', '#2a2a3e', '#8a5a3c'][(c + r * 2) % 5];
            return (
              <g key={c}>
                <rect x={x} y={y - 86} width={34} height={86} rx={8} fill={col} {...k} strokeWidth={2.4} />
                <rect x={x + 10} y={y - 116} width={14} height={34} fill={col} {...k} strokeWidth={2.4} />
                <rect x={x + 4} y={y - 58} width={26} height={24} fill="#f6ecd2" opacity={0.9} />
              </g>
            );
          })}
        </g>
      ))}
      {/* window with warm light */}
      <rect x={120} y={150} width={360} height={320} rx={8} fill="#f3d58c" {...k} strokeWidth={8} />
      <path d="M 300 150 L 300 470 M 120 310 L 480 310" stroke={INK} strokeWidth={6} />
      <path d="M 120 470 L 480 470 L 700 900 L -40 900 Z" fill="#f3d58c" opacity={0.14} />
      {/* frames and a dartboard */}
      <rect x={580} y={190} width={150} height={190} fill="#f6ecd2" {...k} strokeWidth={8} />
      <path d="M 600 340 L 640 280 L 670 318 L 690 296 L 712 340 Z" fill="#8a9a7a" />
      <g transform="translate(860 290)">
        <circle r={78} fill="#2a2a2e" {...k} />
        <circle r={58} fill="#e9d9b2" />
        <circle r={36} fill="#7a2f2f" />
        <circle r={14} fill="#2f6b4a" />
      </g>
      {/* lamp */}
      <path d="M 760 0 L 760 60" stroke={INK} strokeWidth={4} />
      <path d="M 700 110 Q 760 30 820 110 Z" fill="#2f6b4a" {...k} />
      <circle cx={760} cy={120} r={150} fill="#ffe2a0" opacity={0.16 + 0.02 * Math.sin(t * 3)} />
      {/* floor */}
      <rect x={0} y={900} width={1920} height={180} fill="#4a2d1b" />
      {Array.from({length: 12}, (_, i) => <path key={i} d={`M ${i * 180} 906 L ${i * 180 - 70} 1080`} stroke="#3b2214" strokeWidth={4} />)}
    </g>
  );
};

// ------------------------------------------------------------------------------------ bank front
export const BankFront: React.FC<SetProps> = ({opt, layer, t}) => {
  if (layer === 'fg') return null;
  const tod = ((opt.tod as Tod) ?? 'sepia') as Tod;
  const sign = (opt.sign as string) ?? 'CLOSED';
  const sway = Math.sin(t * 1.6) * 4;
  return (
    <g>
      <Sky tod={tod} t={t} />
      <rect x={260} y={250} width={1400} height={650} fill="#e9dcc3" {...k} strokeWidth={5} />
      <path d="M 200 250 L 960 60 L 1720 250 Z" fill="#f2e7d0" {...k} strokeWidth={5} />
      <rect x={200} y={236} width={1520} height={36} fill="#d8c8a8" {...k} strokeWidth={5} />
      <rect x={640} y={150} width={640} height={70} rx={8} fill="#54301a" {...k} />
      <text x={960} y={202} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={54} fill="#f2e7d0" letterSpacing={14}>BANK</text>
      {[0, 1, 2, 3, 4, 5].map((i) => {
        const x = 330 + i * 250;
        return (
          <g key={i}>
            <rect x={x - 14} y={286} width={98} height={26} fill="#d8c8a8" {...k} />
            <rect x={x} y={312} width={70} height={540} fill="#f6eedd" {...k} />
            {[0, 1, 2].map((f) => <path key={f} d={`M ${x + 14 + f * 21} 322 L ${x + 14 + f * 21} 842`} stroke="#d8c8a8" strokeWidth={5} />)}
            <rect x={x - 14} y={852} width={98} height={30} fill="#d8c8a8" {...k} />
          </g>
        );
      })}
      {/* doors */}
      <rect x={800} y={440} width={320} height={460} fill="#5a3a22" {...k} strokeWidth={5} />
      <path d="M 960 440 L 960 900" stroke={INK} strokeWidth={5} />
      {[0, 1].map((i) => <rect key={i} x={826 + i * 160} y={470} width={108} height={180} rx={6} fill="#6f4a2d" stroke={INK} strokeWidth={3} />)}
      {[0, 1].map((i) => <rect key={i} x={826 + i * 160} y={680} width={108} height={190} rx={6} fill="#6f4a2d" stroke={INK} strokeWidth={3} />)}
      <circle cx={940} cy={680} r={9} fill="#c9a24a" {...k} strokeWidth={2} />
      <circle cx={980} cy={680} r={9} fill="#c9a24a" {...k} strokeWidth={2} />
      {/* chain and sign; an empty sign means the bank is open */}
      {sign ? (
        <>
          <path d="M 900 600 Q 960 640 1020 600" fill="none" stroke="#6d7480" strokeWidth={8} strokeDasharray="14 8" />
          <g transform={`translate(960 610) rotate(${sway})`}>
            <path d="M -60 0 L 0 -46 L 60 0" fill="none" stroke={INK} strokeWidth={3} />
            <rect x={-150} y={0} width={300} height={104} rx={10} fill="#fffaf0" {...k} strokeWidth={5} />
            <text x={0} y={70} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={sign.length > 8 ? 46 : 60} fill="#b8322a">{sign}</text>
          </g>
        </>
      ) : null}
      {/* steps and pavement */}
      <rect x={220} y={880} width={1480} height={34} fill="#d8c8a8" {...k} />
      <rect x={160} y={914} width={1600} height={40} fill="#cdbb98" {...k} />
      <rect x={0} y={954} width={1920} height={126} fill="#a8997a" />
      {Array.from({length: 11}, (_, i) => <path key={i} d={`M ${i * 200} 958 L ${i * 200 - 50} 1080`} stroke="#978868" strokeWidth={4} />)}
    </g>
  );
};

export const MONEY_SETS: Record<string, React.FC<SetProps>> = {
  bazaar: Bazaar,
  kirana: Kirana,
  datacentre: DataCentre,
  pub: Pub,
  bank_front: BankFront,
};
