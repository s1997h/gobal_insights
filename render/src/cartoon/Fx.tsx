import React from 'react';
import {INK} from './Character';
import {Icon, type IconName} from './Icons';

/** Little animated effects: buzz lines, Zzz, thought and speech bubbles, sparkles, confetti. */

export type FxSpec = {t: string; x?: number; y?: number; [k: string]: unknown};
type P = {spec: FxSpec; t: number; p: number; dur: number; follow?: {x: number; y: number}};

const FONT = 'Inter, Helvetica Neue, Arial, sans-serif';
const k = {stroke: INK, strokeWidth: 3, strokeLinejoin: 'round' as const, strokeLinecap: 'round' as const};
const clamp = (v: number) => Math.max(0, Math.min(1, v));
const pop = (q: number) => (q <= 0 ? 0 : q >= 1 ? 1 : 1 + Math.sin(q * Math.PI) * 0.25 * (1 - q));

const Buzz: React.FC<P> = ({t}) => {
  const j = Math.sin(t * 80) * 4;
  return (
    <g transform={`translate(${j} 0)`} fill="none" stroke="#e9625a" strokeWidth={6} strokeLinecap="round">
      {[0, 1, 2].map((i) => (
        <g key={i} opacity={0.5 + 0.5 * Math.sin(t * 20 + i)}>
          <path d={`M ${-60 - i * 22} ${-30 - i * 6} Q ${-76 - i * 22} 0 ${-60 - i * 22} ${30 + i * 6}`} />
          <path d={`M ${60 + i * 22} ${-30 - i * 6} Q ${76 + i * 22} 0 ${60 + i * 22} ${30 + i * 6}`} />
        </g>
      ))}
    </g>
  );
};

const Ring: React.FC<P> = ({t}) => (
  <g transform={`rotate(${Math.sin(t * 40) * 8})`}>
    <Icon name="bell" size={110} />
    <g fill="none" stroke="#f2b84b" strokeWidth={7} strokeLinecap="round">
      <path d="M -80 -40 Q -96 0 -80 40" opacity={0.5 + 0.5 * Math.sin(t * 25)} />
      <path d="M 80 -40 Q 96 0 80 40" opacity={0.5 + 0.5 * Math.sin(t * 25)} />
    </g>
  </g>
);

const Zzz: React.FC<P> = ({t}) => (
  <g>
    {[0, 1, 2].map((i) => {
      const ph = (t * 0.6 + i / 3) % 1;
      return (
        <text key={i} x={ph * 120 + i * 10} y={-ph * 200} fontFamily={FONT} fontWeight={800} fontSize={40 + i * 18} fill="#ffffff" stroke={INK} strokeWidth={3} opacity={1 - ph} paintOrder="stroke">
          Z
        </text>
      );
    })}
  </g>
);

export const Bubble: React.FC<{w: number; h: number; tail?: 'down' | 'left' | 'none'; thought?: boolean}> = ({w, h, tail = 'down', thought}) => (
  <g>
    {thought ? (
      <g fill="#ffffff" {...k}>
        <ellipse cx={0} cy={0} rx={w / 2} ry={h / 2} />
        <circle cx={-w * 0.25} cy={h / 2 + 26} r={16} />
        <circle cx={-w * 0.33} cy={h / 2 + 62} r={9} />
      </g>
    ) : (
      <g>
        <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={h / 2.4} fill="#ffffff" {...k} />
        {tail === 'down' && <path d={`M -24 ${h / 2 - 2} L -6 ${h / 2 + 40} L 18 ${h / 2 - 2}`} fill="#ffffff" {...k} />}
        {tail === 'down' && <path d={`M -22 ${h / 2 - 3} L 16 ${h / 2 - 3}`} stroke="#ffffff" strokeWidth={6} />}
      </g>
    )}
  </g>
);

const Thought: React.FC<P> = ({spec, t, follow}) => {
  const icons = (spec.icons as IconName[]) ?? ['question'];
  const w = 120 + icons.length * 110;
  const x = follow ? follow.x + 140 : 0;
  const y = follow ? follow.y : 0;
  return (
    <g transform={`translate(${x} ${y + Math.sin(t * 2) * 6})`}>
      <Bubble w={w} h={170} thought />
      {icons.map((ic, i) => {
        const q = clamp(t * 2.5 - i * 0.6);
        return q > 0 ? (
          <g key={i} transform={`translate(${(i - (icons.length - 1) / 2) * 110} 0) scale(${0.85 * pop(q)})`}>
            <Icon name={ic} />
          </g>
        ) : null;
      })}
    </g>
  );
};

const Speech: React.FC<P> = ({spec}) => {
  const text = spec.text as string;
  const w = Math.max(260, text.length * 21 + 60);
  return (
    <g>
      <Bubble w={w} h={96} />
      <text x={0} y={13} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={36} fill={INK}>
        {text}
      </text>
    </g>
  );
};

const Question: React.FC<P> = ({t}) => (
  <g transform={`rotate(${Math.sin(t * 4) * 8})`}>
    <Icon name="question" size={130} />
  </g>
);

const Sparkle: React.FC<P> = ({t}) => (
  <g>
    {[0, 1, 2, 3, 4, 5].map((i) => {
      const a = (i / 6) * Math.PI * 2;
      const r = 150 + 30 * Math.sin(t * 5 + i);
      const s = 0.6 + 0.4 * Math.sin(t * 8 + i * 2);
      return (
        <path key={i} transform={`translate(${Math.cos(a) * r} ${Math.sin(a) * r}) scale(${s})`} d="M 0 -26 L 7 -7 L 26 0 L 7 7 L 0 26 L -7 7 L -26 0 L -7 -7 Z" fill="#ffe27a" {...k} strokeWidth={2.4} />
      );
    })}
  </g>
);

const Bulb: React.FC<P> = ({t}) => (
  <g transform={`scale(${1 + 0.05 * Math.sin(t * 6)})`}>
    <circle r={110} fill="#ffe27a" opacity={0.3} />
    <Icon name="bulb" size={150} />
  </g>
);

const Hearts: React.FC<P> = ({t}) => (
  <g>
    {[0, 1, 2].map((i) => {
      const ph = (t * 0.5 + i / 3) % 1;
      return (
        <g key={i} transform={`translate(${(i - 1) * 140 + Math.sin(t * 2 + i) * 20} ${-ph * 160}) scale(${0.5 + 0.2 * i})`} opacity={1 - ph}>
          <Icon name="heart" />
        </g>
      );
    })}
  </g>
);

const COLORS = ['#e9625a', '#2ec4b6', '#f2b84b', '#5b8def', '#ffffff'];
const Confetti: React.FC<P> = ({t}) => (
  <g>
    {Array.from({length: 60}, (_, i) => {
      const x = (i * 137) % 1920;
      const y = ((t * (260 + (i % 7) * 40) + i * 53) % 1300) - 150;
      return <rect key={i} x={x + Math.sin(t * 3 + i) * 30} y={y} width={18} height={10} fill={COLORS[i % 5]} transform={`rotate(${t * 200 + i * 30} ${x} ${y})`} />;
    })}
  </g>
);

const Birds: React.FC<P> = ({t}) => (
  <g fill="none" stroke={INK} strokeWidth={5} strokeLinecap="round">
    {[0, 1, 2].map((i) => {
      const x = ((t * 90 + i * 260) % 2200) - 100;
      const y = 200 + i * 50 + Math.sin(t * 2 + i) * 20;
      const f = Math.sin(t * 10 + i) * 10;
      return <path key={i} d={`M ${x - 26} ${y - f} Q ${x - 12} ${y - 14} ${x} ${y} Q ${x + 12} ${y - 14} ${x + 26} ${y - f}`} />;
    })}
  </g>
);

const Tumbleweed: React.FC<P> = ({t, spec}) => {
  const x = ((t * 260) % 2400) - 200;
  const y = (spec.y as number) ?? 980;
  return (
    <g transform={`translate(${x} ${y - 60 - Math.abs(Math.sin(t * 5)) * 40}) rotate(${t * 300})`} fill="none" stroke="#a88457" strokeWidth={5}>
      <circle r={56} />
      <path d="M -50 -20 C -10 40 30 -40 52 10 M -30 -46 C 0 0 -10 30 20 54 M 40 -38 C 0 -10 -30 20 -40 40" />
    </g>
  );
};

const ClockFloat: React.FC<P> = ({spec, t}) => {
  const fast = spec.fast ? 8 : 1;
  return (
    <g>
      <circle r={110} fill="#ffffff" {...k} strokeWidth={6} />
      {Array.from({length: 12}, (_, i) => <path key={i} d="M 0 -94 L 0 -80" transform={`rotate(${i * 30})`} stroke={INK} strokeWidth={5} />)}
      <path d="M 0 0 L 0 -56" transform={`rotate(${t * 30 * fast})`} stroke={INK} strokeWidth={9} strokeLinecap="round" />
      <path d="M 0 0 L 0 -84" transform={`rotate(${t * 360 * fast * 0.25})`} stroke="#e9625a" strokeWidth={6} strokeLinecap="round" />
      <circle r={9} fill={INK} />
      {spec.label ? (
        <g transform="translate(0 170)">
          <rect x={-120} y={-40} width={240} height={68} rx={34} fill="#fffaf0" {...k} />
          <text x={0} y={8} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={40} fill={INK}>{spec.label as string}</text>
        </g>
      ) : null}
    </g>
  );
};

const NotifPop: React.FC<P> = ({spec, p}) => {
  const at = (spec.at as number) ?? 0.2;
  const q = clamp((p - at) * 6);
  if (q <= 0) return null;
  return (
    <g transform={`scale(${pop(q)})`}>
      <rect x={-190} y={-50} width={380} height={100} rx={22} fill="#ffffff" {...k} />
      <circle cx={-140} cy={0} r={28} fill="#e9625a" {...k} />
      <rect x={-96} y={-22} width={230} height={14} rx={6} fill="#9aa3b0" />
      <rect x={-96} y={6} width={150} height={12} rx={6} fill="#c9d0da" />
    </g>
  );
};

const GhostPhone: React.FC<P> = ({t}) => (
  <g opacity={0.65 + 0.2 * Math.sin(t * 3)} transform={`translate(0 ${Math.sin(t * 2) * 8})`}>
    <rect x={-60} y={-110} width={120} height={220} rx={18} fill="#9fd6f2" fillOpacity={0.25} stroke="#ffffff" strokeWidth={5} strokeDasharray="14 10" />
    <text x={0} y={22} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={80} fill="#ffffff">?</text>
  </g>
);

const Crickets: React.FC<P> = ({t}) => (
  <g>
    {[0, 1].map((i) => {
      const ph = (t * 0.7 + i * 0.5) % 1;
      return (
        <text key={i} x={i * 160} y={i * 90 - ph * 30} fontFamily={FONT} fontStyle="italic" fontWeight={700} fontSize={44} fill="#6d6a66" opacity={Math.sin(ph * Math.PI)}>
          *chirp*
        </text>
      );
    })}
  </g>
);

const Checks: React.FC<P> = ({spec, p}) => {
  const items = (spec.items as string[]) ?? [];
  return (
    <g>
      {items.map((it, i) => {
        const q = clamp((p - 0.12 - i * 0.25) * 6);
        if (q <= 0) return null;
        return (
          <g key={i} transform={`translate(0 ${i * 120}) scale(${pop(q)})`}>
            <rect x={-60} y={-46} width={520} height={92} rx={46} fill="#fffaf0" {...k} />
            <g transform="translate(-14 0) scale(0.75)">
              <Icon name="check" />
            </g>
            <text x={40} y={14} fontFamily={FONT} fontWeight={800} fontSize={38} fill={INK}>{it}</text>
          </g>
        );
      })}
    </g>
  );
};

const Sunbeam: React.FC<P> = ({t}) => (
  <g opacity={0.22 + 0.05 * Math.sin(t * 2)}>
    <path d="M 760 170 L 1180 170 L 1500 1080 L 300 1080 Z" fill="#fff3b0" />
  </g>
);

/** A camera flash: the frame goes white for a moment at `from`. Absolute. */
const Flash: React.FC<P> = ({spec, p, dur}) => {
  const local = (p - ((spec.from as number) ?? 0)) * dur;
  const a = local < 0 ? 0 : Math.max(0, 1 - local / 0.35);
  return <rect x={-300} y={-300} width={2520} height={1680} fill="#ffffff" opacity={a * 0.92} />;
};

const NoCamera: React.FC<P> = ({p}) => (
  <g>
    <Icon name="camera" size={170} />
    {p > 0.3 && <path d="M -110 -90 L 110 90" stroke="#e9625a" strokeWidth={20} strokeLinecap="round" />}
  </g>
);

const FailTag: React.FC<P> = ({spec, t}) => (
  <g transform={`rotate(${(spec.tilt as number) ?? -6}) translate(0 ${Math.sin(t * 5) * 4})`}>
    <rect x={-120} y={-40} width={240} height={80} rx={16} fill="#e9443a" {...k} strokeWidth={5} />
    <text x={0} y={16} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={46} fill="#fff">{(spec.text as string) ?? 'FAILED'}</text>
  </g>
);

const Spark: React.FC<P> = ({t}) => (
  <g>
    {Array.from({length: 9}, (_, i) => {
      const a = (i / 9) * Math.PI * 2 + i;
      const r = 30 + ((t * 260 + i * 37) % 120);
      return <path key={i} d={`M ${Math.cos(a) * r} ${Math.sin(a) * r} l ${Math.cos(a) * 26} ${Math.sin(a) * 26}`} stroke={i % 2 ? '#ffe27a' : '#ff8a5a'} strokeWidth={8} strokeLinecap="round" opacity={1 - (r - 30) / 120} />;
    })}
    <path d="M -10 -44 L 14 -8 L -6 -4 L 12 44 L -22 2 L 0 -4 Z" fill="#ffe27a" {...k} transform={`scale(${1 + 0.2 * Math.sin(t * 30)})`} />
  </g>
);

const Coins: React.FC<P> = ({t}) => (
  <g>
    {Array.from({length: 7}, (_, i) => {
      const a = -Math.PI / 2 + (i - 3) * 0.32;
      const d = Math.min(1, t * 1.4);
      const x = Math.cos(a) * 260 * d;
      const y = Math.sin(a) * 260 * d + 300 * d * d;
      return (
        <g key={i} transform={`translate(${x} ${y})`} opacity={1 - d * 0.3}>
          <ellipse rx={26} ry={26 * Math.abs(Math.cos(t * 9 + i))} fill="#f2b84b" {...k} />
        </g>
      );
    })}
  </g>
);

export const FX: Record<string, React.FC<P>> = {
  fail: FailTag,
  spark: Spark,
  coins: Coins,
  buzz: Buzz,
  ring: Ring,
  zzz: Zzz,
  thought: Thought,
  speech: Speech,
  question: Question,
  sparkle: Sparkle,
  bulb: Bulb,
  hearts: Hearts,
  confetti: Confetti,
  birds: Birds,
  tumbleweed: Tumbleweed,
  clock_float: ClockFloat,
  notif_pop: NotifPop,
  ghost_phone: GhostPhone,
  crickets: Crickets,
  checks: Checks,
  sunbeam: Sunbeam,
  no_camera: NoCamera,
  flash: Flash,
};

export const FxView: React.FC<P> = (props) => {
  const C = FX[props.spec.t];
  if (!C) return null;
  const {spec, p, dur} = props;
  const from = (spec.from as number) ?? 0;
  const until = (spec.until as number) ?? 1.01;
  if (p < from || p > until) return null;
  const local = (p - from) * dur;
  const q = clamp(local * 5);
  const absolute = ['confetti', 'birds', 'tumbleweed', 'sunbeam', 'flash'].includes(spec.t) || spec.follow;
  const x = absolute ? 0 : ((spec.x as number) ?? 960);
  const y = absolute ? 0 : ((spec.y as number) ?? 540);
  return (
    <g transform={`translate(${x} ${y}) scale(${absolute ? 1 : pop(q)})`}>
      <C {...props} t={local} />
    </g>
  );
};
