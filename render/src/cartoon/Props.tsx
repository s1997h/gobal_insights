import React from 'react';
import {Character, INK, darken} from './Character';
import {CAST} from './Cast';
import {Icon} from './Icons';

/** Props for the episode renderer. Each is placed at x, y (its base) and scaled by s. */

export type PropSpec = {t: string; x: number; y: number; s?: number; [k: string]: unknown};
type P = {spec: PropSpec; t: number; p: number; fps: number};

const k = {stroke: INK, strokeWidth: 3, strokeLinejoin: 'round' as const};
const ease = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x));
const popIn = (p: number, at: number) => {
  const q = Math.max(0, Math.min(1, (p - at) * 8));
  return q === 0 ? 0 : 1 + Math.sin(q * Math.PI) * 0.18 * (1 - q) + (q - 1) * 0;
};
const FONT = 'Inter, Helvetica Neue, Arial, sans-serif';

const Bed: React.FC<P> = ({spec, t, p}) => {
  const sl = spec.sleeper as {who: string; expr: string; expr2?: string; at?: number} | undefined;
  const reach = spec.reach as number | undefined;
  const expr = sl && sl.expr2 && p >= (sl.at ?? 0.5) ? sl.expr2 : sl?.expr;
  const r = reach !== undefined ? ease((p - reach) * 3.5) : 0;
  return (
    <g>
      <rect x={-330} y={-330} width={34} height={330} rx={8} fill="#8b5a3c" {...k} />
      <rect x={-330} y={-360} width={190} height={70} rx={30} fill="#9b6a48" {...k} />
      <rect x={300} y={-200} width={30} height={200} rx={8} fill="#8b5a3c" {...k} />
      <rect x={-310} y={-150} width={640} height={110} rx={16} fill="#f4f1ea" {...k} />
      <rect x={-300} y={-60} width={620} height={60} fill="#8b5a3c" {...k} />
      <ellipse cx={-210} cy={-176} rx={100} ry={40} fill="#ffffff" {...k} />
      {sl && (
        <Character look={CAST[sl.who] ?? CAST.you} pose="stand" expression={expr as never} x={-200} y={-200} scale={1.0} t={t} headOnly />
      )}
      {sl && r > 0 && (
        <g>
          <path d={`M -150 -150 Q ${-250 - r * 60} ${-210 - r * 40} ${-260 - r * 160} ${-190 - r * 40}`} fill="none" stroke={INK} strokeWidth={19} strokeLinecap="round" />
          <path d={`M -150 -150 Q ${-250 - r * 60} ${-210 - r * 40} ${-260 - r * 160} ${-190 - r * 40}`} fill="none" stroke="#3aa59b" strokeWidth={13} strokeLinecap="round" />
          <circle cx={-260 - r * 160} cy={-190 - r * 40} r={10} fill={CAST.you.skin} stroke={INK} strokeWidth={2.6} />
        </g>
      )}
      <path d="M -160 -150 C -60 -200 200 -190 320 -160 L 320 -40 L -160 -40 Z" fill="#5b8def" {...k} />
      <path d="M -160 -150 C -60 -200 200 -190 320 -160" fill="none" stroke="#f4f1ea" strokeWidth={10} />
      <path d="M -40 -120 L 280 -110 M -20 -80 L 300 -76" stroke={darken('#5b8def', 0.85)} strokeWidth={4} />
    </g>
  );
};

const Nightstand: React.FC<P> = ({spec}) => (
  <g>
    <rect x={-110} y={-230} width={220} height={230} rx={10} fill="#b98656" {...k} />
    <rect x={-96} y={-200} width={192} height={80} rx={6} fill="#c99a6a" {...k} />
    <rect x={-96} y={-104} width={192} height={80} rx={6} fill="#c99a6a" {...k} />
    <circle cx={0} cy={-160} r={8} fill="#e3c27a" {...k} />
    <circle cx={0} cy={-64} r={8} fill="#e3c27a" {...k} />
    {spec.lamp ? (
      <g>
        <rect x={-50} y={-250} width={40} height={20} rx={5} fill="#6d6a66" {...k} />
        <rect x={-34} y={-330} width={8} height={80} fill="#6d6a66" />
        <path d="M -80 -330 L 20 -330 L 0 -400 L -60 -400 Z" fill="#ffd98a" {...k} />
      </g>
    ) : null}
    {spec.clock ? (
      <g transform="translate(40 -262)">
        <Icon name="alarm" size={60} />
      </g>
    ) : null}
  </g>
);

const Couch: React.FC<P> = () => (
  <g>
    <rect x={-330} y={-280} width={660} height={170} rx={40} fill="#d9774f" {...k} />
    <rect x={-380} y={-170} width={110} height={170} rx={30} fill="#c8693f" {...k} />
    <rect x={270} y={-170} width={110} height={170} rx={30} fill="#c8693f" {...k} />
    <rect x={-290} y={-130} width={580} height={80} rx={18} fill="#e58a62" {...k} />
    <rect x={-300} y={-60} width={600} height={50} rx={10} fill="#c8693f" {...k} />
    <rect x={-300} y={-14} width={24} height={14} fill={INK} />
    <rect x={276} y={-14} width={24} height={14} fill={INK} />
  </g>
);

const Table: React.FC<P> = ({spec}) => (
  <g>
    <rect x={-470} y={-150} width={940} height={36} rx={10} fill="#a7724c" {...k} />
    <rect x={-440} y={-116} width={880} height={22} fill={darken('#a7724c', 0.85)} {...k} />
    <rect x={-420} y={-96} width={26} height={96} fill="#8b5a3c" {...k} />
    <rect x={394} y={-96} width={26} height={96} fill="#8b5a3c" {...k} />
    {spec.dinner ? (
      <g>
        {[-300, 0, 300].map((x) => (
          <g key={x}>
            <ellipse cx={x} cy={-158} rx={70} ry={16} fill="#f7f7f2" {...k} />
            <ellipse cx={x} cy={-164} rx={40} ry={9} fill="#e3a05c" />
          </g>
        ))}
        <rect x={-150} y={-230} width={18} height={72} rx={4} fill="#fff6c9" {...k} />
        <path d="M -141 -232 q 8 -14 0 -24 q -8 10 0 24" fill="#ffb347" />
      </g>
    ) : (
      <g>
        {[-250, 240].map((x) => (
          <g key={x} transform={`translate(${x} -186)`}>
            <path d="M -18 -14 L 18 -14 L 14 30 Q 0 35 -14 30 Z" fill="#fbf6ea" {...k} />
            <rect x={-20} y={-20} width={40} height={8} rx={3} fill="#7b5236" {...k} />
          </g>
        ))}
      </g>
    )}
  </g>
);

const Desk: React.FC<P> = ({t}) => (
  <g>
    <rect x={-300} y={-160} width={600} height={34} rx={8} fill="#8fc7b8" {...k} />
    <rect x={-280} y={-126} width={30} height={126} fill="#6aa596" {...k} />
    <rect x={250} y={-126} width={30} height={126} fill="#6aa596" {...k} />
    <g transform="translate(40 -160)">
      <path d="M -130 0 L 130 0 L 150 14 L -150 14 Z" fill="#b9bec7" {...k} />
      <rect x={-120} y={-170} width={240} height={170} rx={10} fill="#5d6b84" {...k} />
      <rect x={-106} y={-156} width={212} height={142} rx={4} fill="#dff3fb" />
      {[0, 1, 2, 3].map((i) => (
        <rect key={i} x={-90} y={-140 + i * 30} width={60 + ((i * 37 + Math.floor(t * 2) * 13) % 100)} height={12} rx={4} fill="#9fb7d6" />
      ))}
    </g>
  </g>
);

const Bench: React.FC<P> = () => (
  <g>
    <rect x={-280} y={-200} width={560} height={26} rx={8} fill="#a7724c" {...k} />
    <rect x={-280} y={-250} width={560} height={26} rx={8} fill="#a7724c" {...k} />
    <rect x={-290} y={-110} width={580} height={28} rx={8} fill="#b98656" {...k} />
    <rect x={-250} y={-82} width={18} height={82} fill="#4a4f5a" {...k} />
    <rect x={232} y={-82} width={18} height={82} fill="#4a4f5a" {...k} />
  </g>
);

const Calendar: React.FC<P> = ({spec, p}) => {
  const [a, b] = (spec.flip as number[]) ?? [1, 30];
  const v = Math.round(a + (b - a) * ease(p * 1.3));
  return (
    <g>
      <rect x={-150} y={-170} width={300} height={320} rx={18} fill="#fffaf0" {...k} strokeWidth={5} />
      <rect x={-150} y={-170} width={300} height={90} rx={18} fill="#e9625a" {...k} strokeWidth={5} />
      <circle cx={-80} cy={-176} r={14} fill="#6d6a66" {...k} />
      <circle cx={80} cy={-176} r={14} fill="#6d6a66" {...k} />
      <text x={0} y={-108} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={44} fill="#ffffff">DAY</text>
      <text x={0} y={90} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={170} fill={INK}>{v}</text>
    </g>
  );
};

const LabelTag: React.FC<{text: string; y: number}> = ({text, y}) => (
  <g transform={`translate(0 ${y})`}>
    <rect x={-text.length * 13 - 20} y={-34} width={text.length * 26 + 40} height={56} rx={28} fill="#fffaf0" {...k} />
    <text x={0} y={6} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={34} fill={INK}>{text}</text>
  </g>
);

const FlipPhone: React.FC<P> = ({spec}) => (
  <g>
    <g transform="scale(3)">
      <rect x={-22} y={-60} width={44} height={60} rx={8} fill="#8a96a8" {...k} strokeWidth={1.6} />
      <rect x={-22} y={-4} width={44} height={60} rx={8} fill="#7a8698" {...k} strokeWidth={1.6} />
      <rect x={-14} y={-52} width={28} height={30} rx={3} fill="#bfe3c9" stroke={INK} strokeWidth={1.2} />
      {Array.from({length: 9}, (_, i) => (
        <rect key={i} x={-14 + (i % 3) * 10} y={8 + Math.floor(i / 3) * 12} width={8} height={8} rx={2} fill="#dfe4ec" />
      ))}
    </g>
    {spec.label ? <LabelTag text={spec.label as string} y={230} /> : null}
  </g>
);

const AlarmClock: React.FC<P> = ({t}) => (
  <g transform={`rotate(${Math.sin(t * 30) * 4})`}>
    <Icon name="alarm" size={180} />
    <LabelTag text="$10" y={150} />
  </g>
);

const Brain: React.FC<P> = ({spec, t, p}) => (
  <g>
    <path d="M -150 30 C -200 -10 -180 -110 -110 -120 C -90 -180 10 -190 30 -140 C 90 -190 190 -140 170 -60 C 220 -20 190 70 120 70 C 100 120 -20 130 -40 90 C -100 120 -170 90 -150 30 Z" fill="#f4a7b9" {...k} strokeWidth={5} />
    <path d="M -100 -60 C -60 -90 -20 -40 20 -80 M -110 10 C -60 -20 0 30 50 -10 C 80 -40 120 -10 140 -30 M -40 60 C 0 40 40 80 90 40" fill="none" stroke="#d07a90" strokeWidth={8} strokeLinecap="round" />
    <circle cx={-50} cy={-20} r={10} fill={INK} />
    <circle cx={30} cy={-20} r={10} fill={INK} />
    <path d="M -30 20 Q -10 34 10 20" fill="none" stroke={INK} strokeWidth={5} strokeLinecap="round" />
    {spec.notifs
      ? [0, 1, 2, 3].map((i) => {
          const a = (i / 4) * Math.PI * 2 + t * 0.6;
          const show = p > 0.15 + i * 0.12;
          return show ? (
            <g key={i} transform={`translate(${Math.cos(a) * 250} ${Math.sin(a) * 170 - 20}) scale(0.55)`}>
              <Icon name="bell" />
            </g>
          ) : null;
        })
      : null}
  </g>
);

const ChatStack: React.FC<P> = ({spec, p}) => {
  const n = Math.round(((spec.count as number) ?? 200) * ease(p * 1.4));
  return (
    <g>
      <rect x={-170} y={-300} width={340} height={600} rx={40} fill="#30343c" {...k} strokeWidth={5} />
      <rect x={-150} y={-270} width={300} height={540} rx={20} fill="#eaf5fb" />
      {Array.from({length: 7}, (_, i) => {
        const yy = -240 + i * 72;
        const left = i % 2 === 0;
        const vis = p > i * 0.08;
        return vis ? (
          <rect key={i} x={left ? -130 : -40} y={yy} width={170} height={52} rx={20} fill={left ? '#ffffff' : '#2ec4b6'} stroke={INK} strokeWidth={2} />
        ) : null;
      })}
      <g transform="translate(150 -300)">
        <circle r={62} fill="#e9625a" {...k} strokeWidth={4} />
        <text x={0} y={16} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={46} fill="#ffffff">{n}</text>
      </g>
    </g>
  );
};

const NotifFlood: React.FC<P> = ({spec, p, t}) => {
  const from = (spec.from as number) ?? 0.3;
  const q = Math.max(0, (p - from) / (1 - from));
  const n = Math.round(((spec.count as number) ?? 500) * ease(q * 1.2));
  return (
    <g>
      <rect x={-160} y={-290} width={320} height={580} rx={40} fill="#30343c" {...k} strokeWidth={5} />
      <rect x={-140} y={-262} width={280} height={524} rx={20} fill={q > 0 ? '#eaf5fb' : '#1d2026'} />
      {q > 0 &&
        Array.from({length: 14}, (_, i) => {
          const appear = i * 0.05;
          if (q < appear) return null;
          const jitter = Math.sin(t * 20 + i) * 2;
          return (
            <g key={i} transform={`translate(${((i * 71) % 180) - 90 + jitter} ${-230 + ((i * 97) % 460)}) rotate(${((i * 37) % 30) - 15})`}>
              <rect x={-120} y={-28} width={240} height={56} rx={14} fill="#ffffff" stroke={INK} strokeWidth={2.4} />
              <circle cx={-92} cy={0} r={15} fill={['#e9625a', '#2ec4b6', '#f2b84b', '#5b8def'][i % 4]} />
              <rect x={-66} y={-12} width={140} height={10} rx={4} fill="#9aa3b0" />
              <rect x={-66} y={6} width={90} height={9} rx={4} fill="#c9d0da" />
            </g>
          );
        })}
      {q > 0 && (
        <g transform="translate(150 -300)">
          <circle r={70} fill="#e9625a" {...k} strokeWidth={4} />
          <text x={0} y={17} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={48} fill="#ffffff">{n}</text>
        </g>
      )}
    </g>
  );
};

const BrickWall: React.FC<P> = () => (
  <g>
    {Array.from({length: 11}, (_, r) =>
      Array.from({length: 5}, (_, c) => (
        <rect key={`${r}-${c}`} x={-150 + c * 64 - (r % 2) * 32} y={-660 + r * 60} width={64} height={60} fill={r % 3 === 0 ? '#c0573f' : '#b44e38'} stroke="#7a3426" strokeWidth={4} />
      )),
    )}
    <rect x={-182} y={-660} width={360} height={660} fill="none" {...k} strokeWidth={5} />
  </g>
);

const BigPhone: React.FC<P> = ({p, t}) => (
  <g>
    <rect x={-210} y={-380} width={420} height={760} rx={50} fill="#30343c" {...k} strokeWidth={5} />
    <rect x={-186} y={-350} width={372} height={700} rx={26} fill="#9fd6f2" />
    {['maya', 'leo', 'zoe', 'sam', 'ana'].map((w, i) =>
      p > i * 0.1 ? (
        <Character key={w} look={CAST[w]} pose={i % 2 ? 'wave' : 'stand'} expression="happy" x={-130 + (i % 3) * 130} y={-60 + Math.floor(i / 3) * 330} scale={0.62} t={t} seed={i * 3} />
      ) : null,
    )}
  </g>
);

const PartyPic: React.FC<P> = ({p}) => (
  <g>
    <rect x={-230} y={-200} width={460} height={380} rx={16} fill="#fffaf0" {...k} strokeWidth={5} />
    <rect x={-200} y={-170} width={400} height={250} rx={8} fill="#f5d36b" />
    {[-120, 0, 120].map((x, i) => (
      <g key={x}>
        <path d={`M ${x - 26} -60 L ${x} -150 L ${x + 26} -60 Z`} fill={['#e9625a', '#2ec4b6', '#5b8def'][i]} {...k} />
        <circle cx={x} cy={-30} r={34} fill="#f2e8dc" {...k} />
      </g>
    ))}
    <text x={0} y={140} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={38} fill={INK}>Saturday party!</text>
    {p > 0.45 && <path d="M -230 -200 L 230 180 M 230 -200 L -230 180" stroke="#e9625a" strokeWidth={18} strokeLinecap="round" opacity={0.9} />}
    {p > 0.45 && <LabelTag text="you missed it" y={250} />}
  </g>
);

const LakeX: React.FC<P> = ({p}) => (
  <g>
    <ellipse cx={0} cy={60} rx={330} ry={90} fill="#5aa9d6" {...k} strokeWidth={4} />
    <ellipse cx={-60} cy={44} rx={120} ry={22} fill="#8cc9ea" />
    <g transform={`translate(${-40 + p * 60} ${-120 + p * 120}) rotate(${p * 200})`}>
      <rect x={-30} y={-54} width={60} height={108} rx={10} fill="#30343c" {...k} />
    </g>
    {p > 0.35 && <path d="M -260 -160 L 260 220 M 260 -160 L -260 220" stroke="#e9625a" strokeWidth={22} strokeLinecap="round" />}
  </g>
);

const ShopFront: React.FC<P> = () => (
  <g>
    <rect x={-260} y={-520} width={520} height={520} fill="#f2c56b" {...k} />
    <path d="M -290 -520 L 290 -520 L 270 -440 L -270 -440 Z" fill="#e9625a" {...k} />
    {Array.from({length: 8}, (_, i) => <path key={i} d={`M ${-270 + i * 70} -440 L ${-255 + i * 70} -520`} stroke="#ffffff" strokeWidth={10} />)}
    <rect x={-210} y={-400} width={260} height={220} fill="#cfeefb" {...k} />
    <rect x={90} y={-400} width={130} height={400} fill="#8b5a3c" {...k} />
    <rect x={-140} y={-160} width={200} height={60} rx={10} fill="#ffffff" {...k} />
    <text x={-40} y={-118} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={34} fill={INK}>CASH OK</text>
  </g>
);

const WallClock: React.FC<P> = ({spec, t}) => (
  <g>
    <circle r={90} fill="#ffffff" {...k} strokeWidth={6} />
    {Array.from({length: 12}, (_, i) => <path key={i} d="M 0 -76 L 0 -64" transform={`rotate(${i * 30})`} stroke={INK} strokeWidth={4} />)}
    <path d="M 0 0 L 0 -46" transform={`rotate(${210 + t * 2})`} stroke={INK} strokeWidth={8} strokeLinecap="round" />
    <path d="M 0 0 L 0 -66" transform={`rotate(${t * 24})`} stroke={INK} strokeWidth={5} strokeLinecap="round" />
    <circle r={8} fill={INK} />
    {spec.label ? <LabelTag text={spec.label as string} y={150} /> : null}
  </g>
);

const Coffee: React.FC<P> = ({t}) => (
  <g transform="scale(2.2)">
    <path d="M -16 -18 L 16 -18 L 13 20 Q 0 25 -13 20 Z" fill="#fbf6ea" {...k} strokeWidth={1.6} />
    <rect x={-18} y={-24} width={36} height={8} rx={3} fill="#7b5236" {...k} strokeWidth={1.6} />
    {[-6, 4].map((x, i) => (
      <path key={i} d={`M ${x} -30 q ${4 * Math.sin(t * 3 + i)} -8 0 -16 q ${-4 * Math.sin(t * 3 + i)} -8 0 -16`} fill="none" stroke="#ffffff" strokeWidth={2.4} opacity={0.8} />
    ))}
  </g>
);

export const PROPS: Record<string, React.FC<P>> = {
  bed: Bed,
  nightstand: Nightstand,
  couch: Couch,
  table: Table,
  desk: Desk,
  bench: Bench,
  calendar: Calendar,
  flip_phone: FlipPhone,
  alarm_clock: AlarmClock,
  brain: Brain,
  chat_stack: ChatStack,
  notif_flood: NotifFlood,
  wall: BrickWall,
  big_phone: BigPhone,
  party_pic: PartyPic,
  lake_x: LakeX,
  shop_front: ShopFront,
  wall_clock: WallClock,
  coffee: Coffee,
};

export const PropView: React.FC<P> = (props) => {
  const C = PROPS[props.spec.t];
  if (!C) return null;
  const FURN: Record<string, number> = {bed: 1.25, couch: 1.15, table: 1.1, desk: 1.15, bench: 1.15, nightstand: 1.1};
  const s = ((props.spec.s as number) ?? 1) * (FURN[props.spec.t] ?? 1);
  const pop = props.spec.pop !== undefined ? popIn(props.p, props.spec.pop as number) : 1;
  if (pop === 0) return null;
  return (
    <g transform={`translate(${props.spec.x} ${props.spec.y}) scale(${s * pop})`}>
      <C {...props} />
    </g>
  );
};
