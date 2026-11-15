import React from 'react';
import {Character, INK} from './Character';
import {CAST} from './Cast';
import {Icon, type IconName} from './Icons';

/**
 * Graphic overlays drawn over the set (stats, charts, checklists) and the day badge. All animate
 * in from the shot's progress p (0..1) and local seconds t.
 */

export type OvSpec = {t: string; pos?: 'left' | 'right' | 'center'; until?: number; [k: string]: unknown};
type P = {spec: OvSpec; t: number; p: number; dur: number};

const FONT = 'Inter, Helvetica Neue, Arial, sans-serif';
const CREAM = '#fffaf0';
const GOLD = '#f2b84b';
const TEAL = '#2ec4b6';
const RED = '#e9625a';
const NAVY = '#0b1b33';
const k = {stroke: INK, strokeWidth: 4, strokeLinejoin: 'round' as const};
const clamp = (v: number) => Math.max(0, Math.min(1, v));
const ease = (x: number) => {
  const c = clamp(x);
  return 1 - Math.pow(1 - c, 3);
};
const pop = (q: number) => (q <= 0 ? 0 : q >= 1 ? 1 : 1 + Math.sin(q * Math.PI) * 0.22 * (1 - q));
const cx = (pos?: string) => (pos === 'left' ? 520 : pos === 'right' ? 1340 : 960);

const Card: React.FC<{w: number; h: number; children: React.ReactNode; fill?: string}> = ({w, h, children, fill = CREAM}) => (
  <g>
    <rect x={-w / 2 + 12} y={-h / 2 + 14} width={w} height={h} rx={34} fill="#000" opacity={0.25} />
    <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={34} fill={fill} {...k} strokeWidth={5} />
    {children}
  </g>
);

const Src: React.FC<{text?: string; y: number; light?: boolean}> = ({text, y, light}) =>
  text ? (
    <text x={0} y={y} textAnchor="middle" fontFamily={FONT} fontWeight={600} fontSize={24} fill={light ? '#c9d3e3' : '#6d6a66'}>
      {text}
    </text>
  ) : null;

// Wrap a label into lines of about n characters.
const wrap = (s: string, n: number) => {
  const words = s.split(' ');
  const lines: string[] = [];
  let cur = '';
  for (const w of words) {
    if ((cur + ' ' + w).trim().length > n && cur) {
      lines.push(cur);
      cur = w;
    } else cur = (cur + ' ' + w).trim();
  }
  if (cur) lines.push(cur);
  return lines;
};

const Title: React.FC<P> = ({spec, t}) => {
  const small = !!spec.small;
  const q = clamp(t * 3);
  return (
    <g transform={`scale(${pop(q)}) rotate(-3)`}>
      <text x={0} y={small ? 0 : 20} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={small ? 150 : 230} fill={GOLD} stroke={INK} strokeWidth={14} paintOrder="stroke" letterSpacing={-4}>
        {spec.title as string}
      </text>
      {spec.sub ? (
        <g transform={`translate(0 ${small ? 90 : 140})`}>
          <rect x={-((spec.sub as string).length * 22) - 40} y={-52} width={(spec.sub as string).length * 44 + 80} height={84} rx={18} fill={RED} {...k} strokeWidth={5} />
          <text x={0} y={10} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={58} fill="#ffffff">
            {(spec.sub as string).toUpperCase()}
          </text>
        </g>
      ) : null}
    </g>
  );
};

const Stat: React.FC<P> = ({spec, t}) => {
  const big = spec.big as string;
  const num = parseFloat(big.replace(/[^0-9.]/g, ''));
  const suffix = big.replace(/[0-9.,]/g, '');
  const shown = spec.count && !Number.isNaN(num) ? `${Math.round(num * ease(t / 1.2))}${suffix}` : big;
  const lines = wrap(spec.label as string, 26);
  const sub = spec.sub as string | undefined;
  const h = 330 + lines.length * 52 + (sub ? 50 : 0) + (spec.src ? 40 : 0);
  return (
    <g transform={`scale(${pop(clamp(t * 3.5))})`}>
      <Card w={720} h={h}>
        <text x={0} y={-h / 2 + 230} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={210} fill={RED} stroke={INK} strokeWidth={8} paintOrder="stroke" letterSpacing={-6}>
          {shown}
        </text>
        {lines.map((l, i) => (
          <text key={i} x={0} y={-h / 2 + 310 + i * 52} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={44} fill={INK}>
            {l}
          </text>
        ))}
        {sub ? (
          <text x={0} y={-h / 2 + 310 + lines.length * 52 + 10} textAnchor="middle" fontFamily={FONT} fontWeight={600} fontSize={34} fill="#4d5560">
            {sub}
          </text>
        ) : null}
        <Src text={spec.src as string} y={h / 2 - 28} />
      </Card>
    </g>
  );
};

const People: React.FC<P> = ({spec, t}) => {
  const n = (spec.n as number) ?? 4;
  const kk = (spec.k as number) ?? 1;
  const looks = ['you', 'maya', 'leo', 'zoe', 'sam', 'ana'];
  return (
    <g transform={`scale(${pop(clamp(t * 3))})`}>
      <Card w={1180} h={640}>
        {Array.from({length: n}, (_, i) => {
          const on = i < kk;
          const fade = on ? 1 : 1 - 0.75 * clamp((t - 0.5 - i * 0.25) * 3);
          return (
            <g key={i} opacity={fade}>
              <Character look={CAST[looks[i % looks.length]]} pose={on ? 'cheer' : 'stand'} expression={on ? 'joy' : fade < 0.6 ? 'sad' : 'neutral'} x={-390 + i * 260} y={170} scale={1.0} t={t} seed={i * 5} />
            </g>
          );
        })}
        <text x={0} y={238} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={54} fill={INK}>
          <tspan fill={RED}>{`${kk} in ${n}`}</tspan> {spec.label as string}
        </text>
        <Src text={spec.src as string} y={290} />
      </Card>
    </g>
  );
};

const Rules: React.FC<P> = ({spec, p}) => {
  const items = spec.items as string[];
  return (
    <g>
      {items.map((it, i) => {
        const q = clamp((p - 0.05 - i * 0.15) * 6);
        if (q <= 0) return null;
        return (
          <g key={i} transform={`translate(0 ${(i - 1) * 170}) scale(${pop(q)}) rotate(${(i - 1) * -2})`}>
            <rect x={-330} y={-66} width={660} height={132} rx={30} fill={CREAM} {...k} strokeWidth={5} />
            <g transform="translate(-250 0) scale(0.95)">
              <Icon name="cross" />
            </g>
            <text x={-180} y={22} fontFamily={FONT} fontWeight={900} fontSize={64} fill={INK}>
              {it}
            </text>
          </g>
        );
      })}
    </g>
  );
};

const Loop: React.FC<P> = ({spec, p, t}) => {
  const steps = spec.steps as string[];
  const cross = (spec.cross as number) ?? -1;
  const icons: IconName[] = ['bell', 'phone', 'star'];
  return (
    <g>
      {steps.map((s, i) => {
        const q = clamp((p - 0.08 - i * 0.2) * 6);
        const x = (i - 1) * 520;
        return (
          <g key={i}>
            {i > 0 && q > 0 && (
              <path d={`M ${x - 360} 0 L ${x - 180} 0`} stroke={GOLD} strokeWidth={16} strokeLinecap="round" markerEnd="url(#arrow)" />
            )}
            {q > 0 && (
              <g transform={`translate(${x} 0) scale(${pop(q)})`}>
                <circle r={150} fill={CREAM} {...k} strokeWidth={6} />
                <g transform="translate(0 -30) scale(1.1)">
                  <Icon name={icons[i % 3]} />
                </g>
                <text x={0} y={95} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={50} fill={INK}>{s}</text>
                {i === cross && p > 0.78 && (
                  <g transform={`rotate(${Math.sin(t * 30) * 2})`}>
                    <path d="M -130 -130 L 130 130 M 130 -130 L -130 130" stroke={RED} strokeWidth={26} strokeLinecap="round" />
                  </g>
                )}
              </g>
            )}
          </g>
        );
      })}
    </g>
  );
};

const Line: React.FC<P> = ({spec, t}) => {
  const xs = spec.x as string[];
  const series = spec.series as {name: string; v: number[]; c: string; static?: boolean}[];
  const W = 1100;
  const H = 440;
  const px = (i: number) => -W / 2 + 120 + (i / (xs.length - 1)) * (W - 240);
  const py = (v: number) => H / 2 - 60 - v * (H - 120);
  return (
    <g transform={`scale(${pop(clamp(t * 3))})`}>
      <Card w={W + 120} h={H + 230}>
        <text x={0} y={-H / 2 - 30} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={50} fill={INK}>{spec.title as string}</text>
        <path d={`M ${-W / 2 + 80} ${-H / 2 + 20} L ${-W / 2 + 80} ${H / 2 - 40} L ${W / 2 - 60} ${H / 2 - 40}`} fill="none" stroke={INK} strokeWidth={5} />
        {xs.map((l, i) => (
          <text key={l} x={px(i)} y={H / 2 + 10} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={34} fill="#4d5560">{l}</text>
        ))}
        {series.map((s, si) => {
          const prog = s.static ? 1 : ease((t - 0.3) / 1.8);
          const pts = s.v.map((v, i) => [px(i), py(v)]);
          const total = pts.length - 1;
          const upto = prog * total;
          const shown: number[][] = [];
          for (let i = 0; i <= total; i++) {
            if (i <= upto) shown.push(pts[i]);
            else {
              const f = upto - (i - 1);
              if (f > 0) shown.push([pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f]);
              break;
            }
          }
          const color = s.c === 'teal' ? TEAL : s.c === 'red' ? RED : GOLD;
          const last = shown[shown.length - 1];
          return (
            <g key={si}>
              <path d={shown.map((pt, i) => `${i ? 'L' : 'M'} ${pt[0]} ${pt[1]}`).join(' ')} fill="none" stroke={INK} strokeWidth={18} strokeLinecap="round" strokeLinejoin="round" />
              <path d={shown.map((pt, i) => `${i ? 'L' : 'M'} ${pt[0]} ${pt[1]}`).join(' ')} fill="none" stroke={color} strokeWidth={11} strokeLinecap="round" strokeLinejoin="round" />
              {last && (
                <g transform={`translate(${last[0]} ${last[1]})`}>
                  <circle r={14} fill={color} {...k} />
                  {prog >= 1 && (
                    <text x={-24} y={s.v[s.v.length - 1] > 0.5 ? -26 : 54} textAnchor="end" fontFamily={FONT} fontWeight={800} fontSize={36} fill={INK}>{s.name}</text>
                  )}
                </g>
              )}
            </g>
          );
        })}
        <Src text={spec.src as string} y={H / 2 + 80} />
      </Card>
    </g>
  );
};

const Duo: React.FC<P> = ({spec, t}) => {
  const a = spec.a as {big: string; label: string};
  const b = spec.b as {big: string; label: string};
  return (
    <g transform={`scale(${pop(clamp(t * 3))})`}>
      <Card w={1300} h={620}>
        <text x={0} y={-220} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={44} fill={INK}>{spec.head as string}</text>
        {[a, b].map((c, i) => {
          const q = clamp((t - 0.6 - i * 1.6) * 3);
          return q > 0 ? (
            <g key={i} transform={`translate(${(i - 0.5) * 600} 30) scale(${pop(q)})`}>
              <text x={0} y={30} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={170} fill={i === 0 ? RED : TEAL} stroke={INK} strokeWidth={8} paintOrder="stroke" letterSpacing={-4}>{c.big}</text>
              {wrap(c.label, 18).map((l, j) => (
                <text key={j} x={0} y={110 + j * 50} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={42} fill={INK}>{l}</text>
              ))}
            </g>
          ) : null;
        })}
        <Src text={spec.src as string} y={280} />
      </Card>
    </g>
  );
};

const Icons: React.FC<P> = ({spec, p}) => {
  const items = spec.items as IconName[];
  const labels = spec.labels as string[] | undefined;
  const n = items.length;
  const gap = spec.pos === 'center' ? 380 : 230;
  const perRow = spec.pos === 'center' ? n : 3;
  return (
    <g>
      {items.map((ic, i) => {
        const q = clamp((p - 0.06 - i * (0.75 / n)) * 6);
        if (q <= 0) return null;
        const row = Math.floor(i / perRow);
        const col = i % perRow;
        const inRow = Math.min(perRow, n - row * perRow);
        const x = (col - (inRow - 1) / 2) * gap;
        const y = (row - (Math.ceil(n / perRow) - 1) / 2) * 260;
        return (
          <g key={i} transform={`translate(${x} ${y}) scale(${pop(q)})`}>
            <circle r={110} fill={CREAM} {...k} strokeWidth={5} />
            <g transform="scale(1.3)">
              <Icon name={ic} />
            </g>
            {labels ? (
              <text x={0} y={175} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={44} fill="#ffffff" stroke={INK} strokeWidth={8} paintOrder="stroke">{labels[i]}</text>
            ) : null}
          </g>
        );
      })}
    </g>
  );
};

const MathOv: React.FC<P> = ({spec, p}) => {
  const parts = [spec.a, spec.b, spec.c] as string[];
  return (
    <g>
      {parts.map((s, i) => {
        const q = clamp((p - 0.3 * i) * 6 - (i === 0 ? -1 : 0));
        if (q <= 0) return null;
        const last = i === 2;
        return (
          <g key={i} transform={`translate(0 ${(i - 1) * 190}) scale(${pop(q)})`}>
            {last && <rect x={-430} y={-110} width={860} height={150} rx={30} fill={GOLD} {...k} strokeWidth={5} />}
            <text x={0} y={last ? 4 : 0} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={last ? 140 : 110} fill={last ? INK : '#ffffff'} stroke={last ? 'none' : INK} strokeWidth={8} paintOrder="stroke">
              {last ? `= ${s}` : s}
            </text>
          </g>
        );
      })}
      <Src text={spec.src as string} y={430} light />
    </g>
  );
};

const Days: React.FC<P> = ({spec, t}) => {
  const n = (spec.n as number) ?? 6;
  return (
    <g>
      {Array.from({length: 7}, (_, i) => {
        const on = i < n;
        const q = clamp((t - i * 0.18) * 4);
        if (q <= 0) return null;
        return (
          <g key={i} transform={`translate(${(i - 3) * 230} -40) scale(${pop(q)})`}>
            <rect x={-95} y={-120} width={190} height={220} rx={20} fill={on ? CREAM : '#3a4a66'} {...k} strokeWidth={5} />
            <rect x={-95} y={-120} width={190} height={56} rx={20} fill={on ? RED : '#55627b'} {...k} strokeWidth={5} />
            {on ? (
              <g transform="translate(0 20) scale(0.9)">
                <Icon name="phone" />
              </g>
            ) : null}
          </g>
        );
      })}
      <text x={0} y={220} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={96} fill={GOLD} stroke={INK} strokeWidth={10} paintOrder="stroke">{spec.label as string}</text>
    </g>
  );
};

const Bars: React.FC<P> = ({spec, t}) => {
  const bars = spec.bars as {l: string; v: number; txt: string; static?: boolean; hot?: boolean}[];
  const max = (spec.max as number) ?? Math.max(...bars.map((b) => b.v));
  const W = 1200;
  const H = 420;
  const bw = 220;
  return (
    <g transform={`scale(${pop(clamp(t * 3))})`}>
      <Card w={W + 80} h={H + 270}>
        <text x={0} y={-H / 2 - 40} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={50} fill={INK}>{spec.title as string}</text>
        <path d={`M ${-W / 2 + 40} ${H / 2} L ${W / 2 - 40} ${H / 2}`} stroke={INK} strokeWidth={5} />
        {bars.map((b, i) => {
          const x = (i - 1) * 340;
          const g = b.static ? 1 : ease((t - 0.3 - (i > 0 ? (i - 1) * 1.6 + 0.4 : 0)) / 0.9);
          const h = (b.v / max) * (H - 40) * g;
          const c = b.hot ? RED : i === 0 ? TEAL : GOLD;
          return (
            <g key={i}>
              {g > 0 && <rect x={x - bw / 2} y={H / 2 - h} width={bw} height={h} rx={14} fill={c} {...k} strokeWidth={5} />}
              <text x={x} y={H / 2 + 50} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={38} fill="#4d5560">{b.l}</text>
              {g > 0.95 && (
                <text x={x} y={H / 2 - h - 22} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={52} fill={INK}>{b.txt}</text>
              )}
            </g>
          );
        })}
        <Src text={spec.src as string} y={H / 2 + 110} />
      </Card>
    </g>
  );
};

const Chop: React.FC<P> = ({spec, p, t}) => {
  // the waking day as a bar: phone hours in one block, the rest chopped into pieces
  const phone = (spec.phone as number) ?? 4;
  const awake = (spec.awake as number) ?? 16;
  const W = 1500;
  const phoneW = (phone / awake) * W;
  const cut = clamp((p - 0.45) * 3);
  const slices = 9;
  return (
    <g transform={`scale(${pop(clamp(t * 3))})`}>
      <text x={0} y={-170} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={60} fill="#ffffff" stroke={INK} strokeWidth={8} paintOrder="stroke">{`Your ${awake} waking hours`}</text>
      <rect x={-W / 2} y={-80} width={phoneW} height={160} rx={20} fill={RED} {...k} strokeWidth={5} />
      <text x={-W / 2 + phoneW / 2} y={20} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={52} fill="#ffffff">{`${phone} h phone`}</text>
      {Array.from({length: slices}, (_, i) => {
        const w = (W - phoneW) / slices;
        const x = -W / 2 + phoneW + i * w + cut * (i * 8 - 10);
        const y = -80 + cut * Math.sin(i * 2.1) * 24;
        return <rect key={i} x={x} y={y} width={w - cut * 8} height={160} rx={cut * 12} fill={TEAL} {...k} strokeWidth={5} transform={`rotate(${cut * Math.sin(i * 1.7) * 6} ${x + w / 2} ${y + 80})`} />;
      })}
      <text x={-W / 2 + phoneW + (W - phoneW) / 2} y={140 + 70} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={52} fill="#ffffff" stroke={INK} strokeWidth={8} paintOrder="stroke">
        {`${awake - phone} h, chopped up`}
      </text>
    </g>
  );
};

const Crowd: React.FC<P> = ({spec, t}) => {
  const cols = 27;
  const rows = 9;
  const shown = Math.min(cols * rows, Math.round(cols * rows * ease(t / 2.2)));
  return (
    <g transform={`scale(${pop(clamp(t * 3))})`}>
      <Card w={1400} h={760}>
        {Array.from({length: shown}, (_, i) => {
          const c = i % cols;
          const r = Math.floor(i / cols);
          const color = [TEAL, GOLD, RED, '#5b8def', '#6a4f8f'][(i * 7) % 5];
          return (
            <g key={i} transform={`translate(${-620 + c * 47.5} ${-300 + r * 52})`}>
              <circle cx={0} cy={-8} r={9} fill="#f2e8dc" stroke={INK} strokeWidth={2} />
              <path d="M -13 18 Q -13 2 0 2 Q 13 2 13 18 Z" fill={color} stroke={INK} strokeWidth={2} />
            </g>
          );
        })}
        <text x={0} y={250} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={80} fill={RED} stroke={INK} strokeWidth={6} paintOrder="stroke">{spec.label as string}</text>
        <text x={0} y={310} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={40} fill={INK}>{spec.sub as string}</text>
        <Src text={spec.src as string} y={355} />
      </Card>
    </g>
  );
};

const Rise: React.FC<P> = ({spec, t}) => {
  const items = spec.items as string[];
  const n = items.length;
  return (
    <g transform={`scale(${pop(clamp(t * 3))})`}>
      <Card w={1300} h={640}>
        {spec.after ? (
          <text x={0} y={-250} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={46} fill={INK}>After the internet came back</text>
        ) : null}
        {items.map((it, i) => {
          const x = (i - (n - 1) / 2) * 380;
          const g = ease((t - 0.3 - i * 0.9) / 0.8);
          const h = (spec.after ? 190 : 250) * g;
          return (
            <g key={i}>
              <rect x={x - 90} y={150 - 90} width={180} height={90} rx={12} fill="#c9d0da" {...k} />
              {g > 0 && <rect x={x - 90} y={60 - h} width={180} height={h} rx={12} fill={[TEAL, GOLD, RED][i % 3]} {...k} />}
              {g > 0.9 && (
                <path d={`M ${x - 30} ${60 - h - 30} L ${x} ${60 - h - 70} L ${x + 30} ${60 - h - 30}`} fill="none" stroke={INK} strokeWidth={10} strokeLinecap="round" strokeLinejoin="round" />
              )}
              <text x={x} y={210} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={42} fill={INK}>{it}</text>
            </g>
          );
        })}
        <Src text={spec.src as string} y={290} />
      </Card>
    </g>
  );
};

const Checklist: React.FC<P> = ({spec, p}) => {
  const items = spec.items as string[];
  const n = items.length;
  const w = spec.pos === 'right' ? 1000 : 1300;
  return (
    <g>
      <Card w={w} h={n * 130 + 90}>
        {items.map((it, i) => {
          const at = 0.12 + i * (0.8 / n);
          const q = clamp((p - at) * 8);
          const y = -((n - 1) * 130) / 2 + i * 130;
          return (
            <g key={i} transform={`translate(${-w / 2 + 90} ${y})`} opacity={q > 0 ? 1 : 0.35}>
              <rect x={-44} y={-44} width={88} height={88} rx={16} fill="#ffffff" {...k} />
              {q > 0 && (
                <path d="M -24 0 L -6 20 L 28 -24" fill="none" stroke={TEAL} strokeWidth={14} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={100} strokeDashoffset={100 * (1 - q)} />
              )}
              <text x={80} y={16} fontFamily={FONT} fontWeight={800} fontSize={spec.pos === 'right' ? 42 : 52} fill={INK}>{it}</text>
            </g>
          );
        })}
      </Card>
    </g>
  );
};

const Chips: React.FC<P> = ({spec, p, t}) => {
  const items = spec.items as string[];
  return (
    <g>
      <text x={0} y={-270} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={64} fill="#ffffff" stroke={INK} strokeWidth={8} paintOrder="stroke">You'd quit on...</text>
      {items.map((it, i) => {
        const q = clamp((p - 0.3 - i * 0.12) * 6);
        if (q <= 0) return null;
        const wob = Math.sin(t * 3 + i) * 2;
        return (
          <g key={i} transform={`translate(0 ${(i - 1) * 170}) scale(${pop(q)}) rotate(${wob})`}>
            <rect x={-260} y={-64} width={520} height={128} rx={64} fill={[TEAL, GOLD, RED][i % 3]} {...k} strokeWidth={6} />
            <text x={0} y={22} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={70} fill={INK}>{it}</text>
          </g>
        );
      })}
    </g>
  );
};

const End: React.FC<P> = ({t}) => (
  <g transform={`translate(0 -330) scale(${pop(clamp(t * 2))})`}>
    <text x={0} y={0} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={92} fill={GOLD} stroke={INK} strokeWidth={10} paintOrder="stroke">What IF You...</text>
  </g>
);

export const OVERLAYS: Record<string, React.FC<P>> = {
  title: Title,
  stat: Stat,
  people: People,
  rules: Rules,
  loop: Loop,
  line: Line,
  duo: Duo,
  icons: Icons,
  math: MathOv,
  days: Days,
  bars: Bars,
  chop: Chop,
  crowd: Crowd,
  rise: Rise,
  checklist: Checklist,
  chips: Chips,
  end: End,
};

export const OverlayView: React.FC<P> = (props) => {
  const C = OVERLAYS[props.spec.t];
  if (!C) return null;
  const until = props.spec.until ?? 1.01;
  if (props.p > until) return null;
  const out = props.spec.until !== undefined ? clamp((until - props.p) * 12) : 1;
  return (
    <g transform={`translate(${cx(props.spec.pos)} 540)`} opacity={out}>
      <C {...props} />
    </g>
  );
};

/** DAY n / 30 in the top-left corner, with a progress bar. Pops when the day changes. */
export const DayBadge: React.FC<{day: number; prev: number | null; t: number}> = ({day, prev, t}) => {
  const changed = prev !== day;
  const q = changed ? clamp(t * 3) : 1;
  const frac = Math.min(1, day / 30);
  return (
    <g transform={`translate(70 60) scale(${changed ? pop(q) : 1})`}>
      <rect x={6} y={8} width={330} height={128} rx={26} fill="#000" opacity={0.25} />
      <rect x={0} y={0} width={330} height={128} rx={26} fill={CREAM} {...k} strokeWidth={5} />
      <text x={28} y={72} fontFamily={FONT} fontWeight={900} fontSize={64} fill={INK} letterSpacing={-1}>
        DAY <tspan fill={RED}>{day}</tspan>
      </text>
      <text x={302} y={72} textAnchor="end" fontFamily={FONT} fontWeight={700} fontSize={30} fill="#6d6a66">/ 30</text>
      <rect x={28} y={90} width={274} height={18} rx={9} fill="#e3ddd0" stroke={INK} strokeWidth={3} />
      {frac > 0 && <rect x={28} y={90} width={274 * frac} height={18} rx={9} fill={TEAL} stroke={INK} strokeWidth={3} />}
    </g>
  );
};

export {NAVY};
