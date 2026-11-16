import React from 'react';
import {Character, INK, darken, type Expression, type Pose} from './Character';
import {CAST} from './Cast';

/** Props for money stories: phones that fail to pay, ATMs, stalls, notes, ledgers, queues. */

type Spec = {t: string; x: number; y: number; s?: number; [k: string]: unknown};
type P = {spec: Spec; t: number; p: number; fps: number};

const k = {stroke: INK, strokeWidth: 3, strokeLinejoin: 'round' as const};
const FONT = 'Inter, Helvetica Neue, Arial, sans-serif';
const RED = '#e9443a';
const GREEN = '#2fae6b';
const CREAM = '#fffaf0';
const clamp = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const pop = (q: number) => (q <= 0 ? 0 : q >= 1 ? 1 : 1 + Math.sin(q * Math.PI) * 0.22 * (1 - q) - (1 - q) * (1 - q));

/** A deterministic fake QR pattern (not a real code). */
const QR: React.FC<{size: number; dead?: boolean}> = ({size, dead}) => {
  const n = 13;
  const c = size / n;
  const cells: React.ReactNode[] = [];
  for (let y = 0; y < n; y++)
    for (let x = 0; x < n; x++) {
      const corner = (x < 4 && y < 4) || (x > n - 5 && y < 4) || (x < 4 && y > n - 5);
      const on = corner ? x % 4 === 0 || y % 4 === 0 || x === n - 1 || y === n - 1 || x === n - 4 || y === n - 4 || (x % (n - 4) === 1 && false) : (x * 7 + y * 13 + x * y) % 3 === 0;
      if (on) cells.push(<rect key={`${x}-${y}`} x={x * c} y={y * c} width={c + 0.5} height={c + 0.5} fill={dead ? '#8a8f98' : INK} />);
    }
  return <g transform={`translate(${-size / 2} ${-size / 2})`}>{cells}</g>;
};

// ---------------------------------------------------------------------------------- pay phone
const PayPhone: React.FC<P> = ({spec, t, p}) => {
  const at = (spec.at as number) ?? 0.35;
  const retry = spec.retry as number | undefined;
  const at2 = (spec.at2 as number) ?? 2;
  const ok = !!spec.ok;
  const amount = (spec.amount as string) ?? '₹20';
  const to = (spec.to as string) ?? 'Chai stall';
  const spinning = p < at || (retry !== undefined && p >= retry && p < at2);
  const since = p >= at2 ? p - at2 : p >= at && !spinning ? p - at : 0;
  const q = clamp(since * 14);
  const shake = !ok && !spinning && since < 0.06 ? Math.sin(since * 400) * 14 : 0;
  const attempt = retry !== undefined && p >= retry ? 2 : 1;
  return (
    <g transform={`translate(${shake} 0) rotate(${(spec.tilt as number) ?? -4})`}>
      <rect x={-196} y={-384} width={392} height={768} rx={56} fill="#000" opacity={0.25} transform="translate(14 16)" />
      <rect x={-196} y={-384} width={392} height={768} rx={56} fill="#2b2f38" {...k} strokeWidth={6} />
      <rect x={-172} y={-356} width={344} height={712} rx={36} fill={spinning ? '#f6f8fc' : ok ? '#e9f9ef' : '#fdecea'} />
      <rect x={-50} y={-346} width={100} height={18} rx={9} fill="#2b2f38" />
      {!spec.bare && <text x={0} y={-270} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={30} fill="#6d7480">Paying {to}</text>}
      {!spec.bare && <text x={0} y={-170} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={110} fill={INK} letterSpacing={-3}>{amount}</text>}
      {spinning ? (
        <g>
          <circle cx={0} cy={20} r={74} fill="none" stroke="#dfe4ee" strokeWidth={18} />
          <path d="M 0 -54 A 74 74 0 0 1 74 20" fill="none" stroke="#5b8def" strokeWidth={18} strokeLinecap="round" transform={`rotate(${t * 420} 0 20)`} />
          <text x={0} y={170} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={34} fill="#6d7480">Processing{'.'.repeat(1 + (Math.floor(t * 3) % 3))}</text>
          {attempt === 2 && <text x={0} y={224} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={28} fill="#9aa3b0">Attempt 2</text>}
        </g>
      ) : (
        <g>
          <g transform={`translate(0 20) scale(${pop(q)})`}>
            <circle r={92} fill={ok ? GREEN : RED} {...k} strokeWidth={6} />
            {ok ? (
              <path d="M -42 4 L -12 36 L 46 -30" fill="none" stroke="#fff" strokeWidth={22} strokeLinecap="round" strokeLinejoin="round" />
            ) : (
              <path d="M -36 -36 L 36 36 M 36 -36 L -36 36" stroke="#fff" strokeWidth={22} strokeLinecap="round" />
            )}
          </g>
          {!spec.bare && <text x={0} y={186} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={48} fill={ok ? '#1f7d4b' : '#b8322a'}>{ok ? 'PAID' : 'PAYMENT'}</text>}
          {!ok && !spec.bare && <text x={0} y={240} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={48} fill="#b8322a">FAILED</text>}
          {!ok && !spec.bare && (
            <g transform="translate(0 300)">
              <rect x={-110} y={-30} width={220} height={60} rx={30} fill="#fff" stroke="#b8322a" strokeWidth={4} />
              <text x={0} y={11} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={30} fill="#b8322a">Try again</text>
            </g>
          )}
        </g>
      )}
    </g>
  );
};

// ----------------------------------------------------------------------------------- QR stand
const QrStand: React.FC<P> = ({spec, p}) => {
  const at = (spec.at as number) ?? 2;
  const dead = p >= at;
  const q = clamp((p - at) * 12);
  return (
    <g>
      <path d="M -70 0 L 70 0 L 56 -22 L -56 -22 Z" fill="#6d7480" {...k} />
      <rect x={-84} y={-250} width={168} height={230} rx={12} fill={CREAM} {...k} strokeWidth={4} />
      <rect x={-84} y={-250} width={168} height={46} rx={12} fill="#5b8def" {...k} strokeWidth={4} />
      <text x={0} y={-218} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={24} fill="#fff">SCAN &amp; PAY</text>
      <g transform="translate(0 -116)"><QR size={132} dead={dead} /></g>
      {dead && <path d="M -70 -186 L 70 -46 M 70 -186 L -70 -46" stroke={RED} strokeWidth={18} strokeLinecap="round" opacity={q} />}
    </g>
  );
};

// ---------------------------------------------------------------------------------- chai stall
const ChaiStall: React.FC<P> = ({spec, t}) => (
  <g>
    {/* umbrella */}
    <rect x={-6} y={-560} width={12} height={330} fill="#8b5a3c" {...k} />
    <path d="M -300 -500 Q 0 -700 300 -500 Z" fill="#e9625a" {...k} strokeWidth={4} />
    {[-200, -100, 0, 100, 200].map((x, i) => i % 2 === 0 && <path key={i} d={`M ${x - 50} -500 Q ${x * 0.5 - 20} -640 0 -650 Q ${x * 0.5 + 20} -640 ${x + 50} -500 Z`} fill="#fffaf0" opacity={0.9} />)}
    {/* cart */}
    <rect x={-250} y={-240} width={500} height={44} rx={8} fill="#c98f52" {...k} />
    <rect x={-236} y={-196} width={472} height={150} fill="#3f9d6b" {...k} />
    <rect x={-150} y={-176} width={300} height={74} rx={10} fill={CREAM} {...k} />
    <text x={0} y={-124} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={46} fill={INK}>{(spec.sign as string) ?? 'CHAI ₹20'}</text>
    {[-170, 170].map((x, i) => (
      <g key={i} transform={`translate(${x} -30)`}>
        <circle r={46} fill="#30343c" {...k} strokeWidth={5} />
        <circle r={12} fill="#9aa3b0" {...k} />
        {[0, 1, 2, 3].map((a) => <path key={a} d="M 0 -40 L 0 40" transform={`rotate(${a * 45})`} stroke="#9aa3b0" strokeWidth={3} />)}
      </g>
    ))}
    {/* kettle and glasses */}
    <g transform="translate(-140 -240)">
      <path d="M -52 0 L -58 -70 Q 0 -100 58 -70 L 52 0 Z" fill="#cfd6df" {...k} />
      <path d="M 54 -56 Q 96 -60 100 -92" fill="none" stroke="#cfd6df" strokeWidth={14} strokeLinecap="round" />
      <path d="M 54 -56 Q 96 -60 100 -92" fill="none" stroke={INK} strokeWidth={3} />
      <path d="M -40 -84 Q 0 -140 40 -84" fill="none" stroke={INK} strokeWidth={8} />
      {[0, 1].map((i) => <path key={i} d={`M ${98 + i * 10} -104 q ${6 * Math.sin(t * 3 + i)} -16 0 -32 q ${-6 * Math.sin(t * 3 + i)} -16 0 -32`} fill="none" stroke="#fff" strokeWidth={5} opacity={0.8} />)}
    </g>
    {[0, 1, 2, 3].map((i) => (
      <g key={i} transform={`translate(${10 + i * 56} -240)`}>
        <path d="M -18 0 L -22 -50 L 22 -50 L 18 0 Z" fill="#e9f6fb" opacity={0.9} {...k} strokeWidth={2.4} />
        <path d="M -19 -6 L -21 -34 L 21 -34 L 19 -6 Z" fill="#b5713a" />
      </g>
    ))}
  </g>
);

// ---------------------------------------------------------------------------------- ATM booth
const AtmBooth: React.FC<P> = ({spec, t, p}) => {
  const at = (spec.at as number) ?? 0;
  const down = p >= at;
  const msg = ((spec.screen as string) ?? 'OUT OF SERVICE').split('|');
  const blink = Math.sin(t * 6) > -0.3;
  return (
    <g>
      <rect x={-250} y={-640} width={500} height={640} fill="#dfe6f5" {...k} strokeWidth={5} />
      <rect x={-270} y={-700} width={540} height={96} rx={10} fill="#2f4a7a" {...k} strokeWidth={5} />
      <text x={0} y={-630} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={72} fill="#fff" letterSpacing={10}>ATM</text>
      <rect x={-210} y={-570} width={420} height={570} fill="#b9c7dd" {...k} />
      {/* machine */}
      <rect x={-150} y={-520} width={300} height={470} rx={14} fill="#eef2f8" {...k} strokeWidth={4} />
      <rect x={-118} y={-486} width={236} height={170} rx={8} fill={down ? '#3a1414' : '#1c3a5e'} {...k} />
      {down ? (
        blink && msg.map((m, i) => (
          <text key={i} x={0} y={-410 + i * 44 - (msg.length - 1) * 22 + 12} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={34} fill="#ff6b5e">{m}</text>
        ))
      ) : (
        <text x={0} y={-390} textAnchor="middle" fontFamily={FONT} fontWeight={800} fontSize={34} fill="#bfe6ff">WELCOME</text>
      )}
      {Array.from({length: 12}, (_, i) => <rect key={i} x={-70 + (i % 4) * 38} y={-288 + Math.floor(i / 4) * 34} width={28} height={24} rx={4} fill="#9aa3b0" stroke={INK} strokeWidth={2} />)}
      <rect x={-110} y={-170} width={220} height={22} rx={4} fill="#30343c" {...k} strokeWidth={2.4} />
      <rect x={-110} y={-120} width={130} height={14} rx={4} fill="#30343c" />
      <circle cx={100} cy={-252} r={10} fill={down ? RED : GREEN} />
    </g>
  );
};

// -------------------------------------------------------------------------------- petrol pump
const PetrolPump: React.FC<P> = ({spec}) => (
  <g>
    <rect x={-560} y={-720} width={1120} height={70} rx={10} fill="#e9625a" {...k} strokeWidth={5} />
    <rect x={-560} y={-664} width={1120} height={22} fill="#fffaf0" {...k} />
    {[-470, 470].map((x, i) => <rect key={i} x={x - 20} y={-642} width={40} height={642} fill="#cfd6df" {...k} />)}
    {[-150, 150].map((x, i) => (
      <g key={i} transform={`translate(${x} 0)`}>
        <rect x={-76} y={-360} width={152} height={340} rx={12} fill="#f2b84b" {...k} strokeWidth={4} />
        <rect x={-90} y={-20} width={180} height={20} fill="#6d7480" {...k} />
        <rect x={-56} y={-330} width={112} height={90} rx={6} fill="#1c3a5e" {...k} />
        <text x={0} y={-272} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={34} fill="#bfe6ff">₹ ---</text>
        <rect x={-56} y={-220} width={112} height={26} rx={4} fill="#fffaf0" stroke={INK} strokeWidth={2} />
        <path d={`M 76 -250 Q 150 -230 130 -120 Q 116 -60 96 -110`} fill="none" stroke={INK} strokeWidth={10} strokeLinecap="round" />
        <rect x={84} y={-150} width={22} height={50} rx={6} fill="#30343c" {...k} strokeWidth={2} />
      </g>
    ))}
    {spec.board ? (
      <g transform="translate(0 -470) rotate(-3)">
        <rect x={-190} y={-60} width={380} height={120} rx={12} fill={CREAM} {...k} strokeWidth={5} />
        <text x={0} y={20} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={58} fill="#b8322a">{spec.board as string}</text>
      </g>
    ) : null}
  </g>
);

// ------------------------------------------------------------------------------ auto-rickshaw
const Auto: React.FC<P> = ({spec, t}) => {
  const bob = Math.sin(t * 9) * 2.5;
  return (
    <g transform={`translate(0 ${bob}) scale(${(spec.flip as boolean) ? -1 : 1} 1)`}>
      <path d="M -250 -70 L -250 -210 Q -240 -330 -120 -340 L 110 -340 Q 190 -330 230 -220 L 262 -120 L 262 -70 Z" fill="#f2c230" {...k} strokeWidth={5} />
      <path d="M -250 -210 Q -240 -330 -120 -340 L 110 -340 Q 190 -330 230 -220 L -250 -220 Z" fill="#2a2a2e" {...k} strokeWidth={5} />
      <path d="M 120 -214 L 222 -214 L 250 -130 L 120 -130 Z" fill="#cfeefb" {...k} />
      <rect x={-210} y={-214} width={300} height={144} fill="#3f9d6b" {...k} />
      <rect x={-60} y={-214} width={10} height={144} fill={INK} />
      <rect x={-190} y={-196} width={110} height={70} rx={8} fill="#2a2a2e" opacity={0.55} />
      <circle cx={262} cy={-150} r={14} fill="#fff3b8" {...k} />
      {[-170, 200].map((x, i) => (
        <g key={i} transform={`translate(${x} -46)`}>
          <circle r={46} fill="#30343c" {...k} strokeWidth={5} />
          <circle r={16} fill="#9aa3b0" {...k} />
        </g>
      ))}
      {spec.sign ? (
        <g transform={`translate(-60 -410) scale(${(spec.flip as boolean) ? -1 : 1} 1)`}>
          <rect x={-130} y={-40} width={260} height={76} rx={10} fill={CREAM} {...k} strokeWidth={4} />
          <text x={0} y={14} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={40} fill="#b8322a">{spec.sign as string}</text>
        </g>
      ) : null}
    </g>
  );
};

// ----------------------------------------------------------------------------------- veg cart
const VegCart: React.FC<P> = () => (
  <g>
    <rect x={-230} y={-200} width={460} height={36} rx={6} fill="#8b5a3c" {...k} />
    <path d="M -230 -200 L -250 -250 L 250 -250 L 230 -200 Z" fill="#a8713c" {...k} />
    {Array.from({length: 22}, (_, i) => {
      const x = -210 + (i % 11) * 42;
      const y = -256 - Math.floor(i / 11) * 30 - ((i * 7) % 12);
      return <circle key={i} cx={x} cy={y} r={22} fill={['#e9443a', '#3f9d6b', '#f2b84b', '#8a63b8', '#f08a3a'][i % 5]} {...k} strokeWidth={2.4} />;
    })}
    <rect x={-200} y={-164} width={10} height={130} fill="#8b5a3c" {...k} strokeWidth={2} />
    <rect x={190} y={-164} width={10} height={130} fill="#8b5a3c" {...k} strokeWidth={2} />
    {[-150, 150].map((x, i) => (
      <g key={i} transform={`translate(${x} -50)`}>
        <circle r={50} fill="none" stroke="#30343c" strokeWidth={10} />
        {[0, 1, 2, 3].map((a) => <path key={a} d="M 0 -46 L 0 46" transform={`rotate(${a * 45})`} stroke="#6d7480" strokeWidth={4} />)}
        <circle r={10} fill="#30343c" />
      </g>
    ))}
  </g>
);

// ------------------------------------------------------------------------------------ shutter
const Shutter: React.FC<P> = ({spec, p}) => {
  const from = (spec.close as number) ?? -1; // progress when the shutter starts coming down
  const q = from < 0 ? 1 : clamp((p - from) * 3);
  const h = 380 * q;
  return (
    <g>
      <rect x={-330} y={-640} width={660} height={640} fill="#dfe6f5" {...k} strokeWidth={5} />
      <rect x={-350} y={-700} width={700} height={110} rx={10} fill="#2ec4b6" {...k} strokeWidth={5} />
      <text x={0} y={-622} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={64} fill="#fff" letterSpacing={4}>{(spec.name as string) ?? 'SUPERMART'}</text>
      <rect x={-280} y={-540} width={560} height={540} fill="#30343c" {...k} />
      {/* inside: tills */}
      {[0, 1, 2].map((i) => (
        <g key={i} transform={`translate(${-180 + i * 180} -80)`}>
          <rect x={-60} y={-90} width={120} height={90} fill="#6d7480" {...k} />
          <rect x={-40} y={-170} width={80} height={64} rx={6} fill="#3a1414" {...k} />
          <path d="M -18 -152 L 18 -124 M 18 -152 L -18 -124" stroke="#ff6b5e" strokeWidth={8} strokeLinecap="round" />
        </g>
      ))}
      <rect x={-280} y={-540} width={560} height={h + 160 * q} fill="#aab2bd" {...k} />
      {Array.from({length: Math.floor((h + 160 * q) / 30)}, (_, r) => <path key={r} d={`M -280 ${-520 + r * 30} L 280 ${-520 + r * 30}`} stroke="#7d8590" strokeWidth={4} />)}
      {q > 0.95 && spec.note ? (
        <g transform="translate(0 -300) rotate(-4)">
          <rect x={-170} y={-70} width={340} height={140} rx={8} fill={CREAM} {...k} strokeWidth={4} />
          {(spec.note as string).split('|').map((m, i, a) => (
            <text key={i} x={0} y={i * 50 - (a.length - 1) * 25 + 16} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={44} fill="#b8322a">{m}</text>
          ))}
        </g>
      ) : null}
    </g>
  );
};

// --------------------------------------------------------------------------------------- note
const Note: React.FC<P> = ({spec, t}) => {
  const glow = !!spec.glow;
  const bob = Math.sin(t * 2) * 10;
  return (
    <g transform={`translate(0 ${bob}) rotate(${(spec.tilt as number) ?? -6})`}>
      {glow &&
        Array.from({length: 14}, (_, i) => {
          const a = (i / 14) * Math.PI * 2 + t * 0.4;
          return <path key={i} d={`M ${Math.cos(a) * 260} ${Math.sin(a) * 170} L ${Math.cos(a) * 420} ${Math.sin(a) * 300}`} stroke="#ffe27a" strokeWidth={14} strokeLinecap="round" opacity={0.75} />;
        })}
      <rect x={-230} y={-110} width={460} height={220} rx={14} fill="#000" opacity={0.2} transform="translate(10 12)" />
      <rect x={-230} y={-110} width={460} height={220} rx={14} fill={(spec.color as string) ?? '#b9d8a8'} {...k} strokeWidth={5} />
      <rect x={-208} y={-88} width={416} height={176} rx={8} fill="none" stroke={INK} strokeWidth={2.4} strokeDasharray="6 8" />
      <circle cx={-110} cy={0} r={58} fill="#fffaf0" {...k} />
      <text x={-110} y={24} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={70} fill={INK}>₹</text>
      <text x={90} y={34} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={100} fill={INK} letterSpacing={-3}>{(spec.val as string) ?? '100'}</text>
    </g>
  );
};

// ------------------------------------------------------------------------------------- wallet
const Wallet: React.FC<P> = ({spec, p}) => {
  const q = clamp(p * 5);
  return (
    <g>
      {[0, 1].map((i) => (
        <g key={i} transform={`translate(${-60 + i * 70} ${-150 - q * 90 + i * 16}) rotate(${-10 + i * 12})`}>
          <rect x={-130} y={-70} width={260} height={140} rx={10} fill={i ? '#b9d8a8' : '#e8c7a0'} {...k} />
          <circle cx={-50} cy={0} r={34} fill="#fffaf0" {...k} strokeWidth={2.4} />
          <text x={-50} y={16} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={44} fill={INK}>₹</text>
          <text x={54} y={22} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={60} fill={INK}>{i ? '100' : '20'}</text>
        </g>
      ))}
      <path d="M -260 -170 L 260 -170 L 280 150 Q 0 190 -280 150 Z" fill="#7a4b28" {...k} strokeWidth={5} />
      <path d="M -270 -40 Q 0 -10 270 -40 L 280 150 Q 0 190 -280 150 Z" fill="#8f5a32" {...k} strokeWidth={5} />
      <path d="M -250 -20 Q 0 8 250 -20" fill="none" stroke="#5e3a1f" strokeWidth={4} strokeDasharray="14 10" />
      <circle cx={170} cy={70} r={30} fill="#f2b84b" {...k} />
      <text x={170} y={84} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={36} fill={INK}>10</text>
      {spec.label ? (
        <g transform={`translate(0 270) scale(${pop(clamp((p - 0.3) * 6))})`}>
          <rect x={-190} y={-58} width={380} height={110} rx={55} fill={CREAM} {...k} strokeWidth={5} />
          <text x={0} y={18} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={68} fill="#b8322a">{spec.label as string}</text>
        </g>
      ) : null}
    </g>
  );
};

// -------------------------------------------------------------------------------------- khata
const Khata: React.FC<P> = ({spec, p, t}) => {
  const lines = (spec.lines as [string, string][]) ?? [];
  const from = (spec.from as number) ?? 0.1;
  const to = (spec.to as number) ?? 0.8;
  const strike = (spec.strike as number) ?? -1;
  const at = (spec.at as number) ?? 0.6;
  const glow = !!spec.glow;
  const mystery = !!spec.mystery;
  return (
    <g transform={`rotate(${(spec.tilt as number) ?? -3})`}>
      {glow &&
        Array.from({length: 16}, (_, i) => {
          const a = (i / 16) * Math.PI * 2 + t * 0.3;
          return <path key={i} d={`M ${Math.cos(a) * 420} ${Math.sin(a) * 360} L ${Math.cos(a) * 620} ${Math.sin(a) * 520}`} stroke="#ffe27a" strokeWidth={16} strokeLinecap="round" opacity={0.6} />;
        })}
      <rect x={-380} y={-300} width={760} height={600} rx={18} fill="#000" opacity={0.22} transform="translate(14 16)" />
      <rect x={-380} y={-300} width={760} height={600} rx={18} fill="#b8322a" {...k} strokeWidth={6} />
      <rect x={-354} y={-276} width={708} height={552} rx={8} fill={mystery ? '#3a1414' : '#fbf3dc'} {...k} />
      <path d="M 0 -276 L 0 276" stroke={mystery ? '#5a1f1f' : '#d9c9a0'} strokeWidth={8} />
      {mystery ? (
        <text x={0} y={70} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={260} fill="#f2b84b">?</text>
      ) : (
        <g>
          {Array.from({length: 9}, (_, i) => <path key={i} d={`M -330 ${-196 + i * 52} L 330 ${-196 + i * 52}`} stroke="#bcd3e6" strokeWidth={3} />)}
          <path d="M -90 -260 L -90 260" stroke="#e9a6a0" strokeWidth={3} />
          <text x={-330} y={-222} fontFamily={FONT} fontWeight={800} fontSize={30} fill="#8a7a55">NAME</text>
          <text x={330} y={-222} textAnchor="end" fontFamily={FONT} fontWeight={800} fontSize={30} fill="#8a7a55">OWES</text>
          {lines.map((ln, i) => {
            const start = from + ((to - from) * i) / Math.max(1, lines.length);
            const q = clamp((p - start) * 10);
            if (q <= 0) return null;
            const y = -160 + i * 52;
            const name = ln[0].slice(0, Math.ceil(ln[0].length * q));
            const done = i === strike && p >= at;
            return (
              <g key={i}>
                <text x={-330} y={y} fontFamily={FONT} fontWeight={700} fontStyle="italic" fontSize={40} fill="#27408b">{name}</text>
                {q >= 1 && <text x={330} y={y} textAnchor="end" fontFamily={FONT} fontWeight={800} fontStyle="italic" fontSize={40} fill="#27408b">{ln[1]}</text>}
                {done && <path d={`M -340 ${y - 14} L ${-340 + 680 * clamp((p - at) * 8)} ${y - 14}`} stroke={GREEN} strokeWidth={8} strokeLinecap="round" />}
              </g>
            );
          })}
        </g>
      )}
      {/* pen */}
      {!mystery && (
        <g transform={`translate(${-20 + Math.sin(t * 9) * 8} ${Math.min(250, -150 + lines.length * 52 + 60) + Math.cos(t * 7) * 6}) rotate(35)`}>
          <rect x={-10} y={-120} width={20} height={130} rx={6} fill="#27408b" {...k} strokeWidth={2.4} />
          <path d="M -10 10 L 0 34 L 10 10 Z" fill="#f2e7d0" {...k} strokeWidth={2.4} />
        </g>
      )}
    </g>
  );
};

// ------------------------------------------------------------------------------------- cheque
const Cheque: React.FC<P> = ({spec, p, t}) => {
  const fly = spec.fly as [number, number] | undefined;
  const q = fly ? clamp((p - ((spec.from as number) ?? 0.1)) / 0.5) : 0;
  const e = q * q * (3 - 2 * q);
  const dx = fly ? fly[0] * e : 0;
  const dy = fly ? fly[1] * e - Math.sin(e * Math.PI) * 160 : Math.sin(t * 2) * 6;
  return (
    <g transform={`translate(${dx} ${dy}) rotate(${-5 + (fly ? Math.sin(e * Math.PI) * 14 : 0)})`}>
      <rect x={-170} y={-76} width={340} height={152} rx={8} fill="#000" opacity={0.2} transform="translate(8 10)" />
      <rect x={-170} y={-76} width={340} height={152} rx={8} fill="#eaf4e4" {...k} />
      <rect x={-170} y={-76} width={340} height={30} rx={8} fill="#9fc79a" {...k} strokeWidth={2.4} />
      <text x={-154} y={-54} fontFamily={FONT} fontWeight={900} fontSize={20} fill={INK}>CHEQUE</text>
      <path d="M -150 -14 L 60 -14 M -150 16 L 20 16" stroke="#6d7480" strokeWidth={4} />
      <rect x={76} y={-28} width={78} height={34} rx={4} fill="#fff" stroke={INK} strokeWidth={2.4} />
      <text x={115} y={-3} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={24} fill={INK}>{(spec.val as string) ?? '£20'}</text>
      <path d="M 30 50 q 14 -26 28 0 q 12 18 26 -8 q 10 -14 22 6 l 30 -4" fill="none" stroke="#27408b" strokeWidth={4} strokeLinecap="round" />
    </g>
  );
};

// ----------------------------------------------------------------------------------------- TV
const Tv: React.FC<P> = ({spec, t}) => {
  const lines = (spec.lines as string[]) ?? [];
  const tick = (t * 160) % 900;
  return (
    <g>
      <rect x={-470} y={-560} width={940} height={560} rx={22} fill="#1d2027" {...k} strokeWidth={6} />
      <rect x={-440} y={-532} width={880} height={480} rx={8} fill="#16335c" />
      <clipPath id="tv-clip"><rect x={-440} y={-532} width={880} height={480} rx={8} /></clipPath>
      <g clipPath="url(#tv-clip)">
        <rect x={-440} y={-532} width={880} height={86} fill="#c8281e" />
        <text x={-410} y={-472} fontFamily={FONT} fontWeight={900} fontSize={56} fill="#fff" letterSpacing={2}>BREAKING NEWS</text>
        <circle cx={380} cy={-489} r={14} fill="#fff" opacity={0.5 + 0.5 * Math.sin(t * 6)} />
        {lines.map((ln, i) => (
          <text key={i} x={0} y={-340 + i * 84} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={i === 0 ? 68 : 54} fill={i === 0 ? '#ffe27a' : '#fff'}>{ln}</text>
        ))}
        <rect x={-440} y={-116} width={880} height={64} fill="#f2b84b" />
        <text x={440 - tick} y={-72} fontFamily={FONT} fontWeight={800} fontSize={36} fill={INK}>{(spec.ticker as string) ?? ''}</text>
        <text x={1340 - tick} y={-72} fontFamily={FONT} fontWeight={800} fontSize={36} fill={INK}>{(spec.ticker as string) ?? ''}</text>
      </g>
      <rect x={-60} y={0} width={120} height={40} fill="#1d2027" {...k} />
      <rect x={-200} y={40} width={400} height={20} rx={8} fill="#1d2027" {...k} />
    </g>
  );
};

// -------------------------------------------------------------------------------------- queue
const ORDER = ['maya', 'leo', 'zoe', 'sam', 'ana', 'you'];
const Queue: React.FC<P> = ({spec, t, p}) => {
  const n = (spec.n as number) ?? 5;
  const gap = (spec.gap as number) ?? 150;
  const who = (spec.who as string[]) ?? ORDER;
  const at = (spec.at as number) ?? 2;
  const pose = (p >= at && (spec.pose2 as Pose)) || ((spec.pose as Pose) ?? 'stand');
  const expr = (p >= at && (spec.expr2 as Expression)) || ((spec.expr as Expression) ?? 'neutral');
  const dir = (spec.dir as number) ?? 1;
  const shrink = (spec.shrink as number) ?? 0; // people further back get smaller (depth)
  return (
    <g>
      {Array.from({length: n}, (_, i) => n - 1 - i).map((i) => {
        const stagger = p >= at ? clamp((p - at - i * 0.03) * 20) : 0;
        const ps = p >= at && stagger < 1 ? ((spec.pose as Pose) ?? 'stand') : pose;
        const ex = p >= at && stagger < 1 ? ((spec.expr as Expression) ?? 'neutral') : expr;
        const sc = 1.55 * (1 - shrink * i);
        return (
          <g key={i}>
            <ellipse cx={i * gap * dir * (1 - shrink * i * 0.5)} cy={2} rx={62 * (1 - shrink * i)} ry={12} fill="#000" opacity={0.18} />
            <Character look={CAST[who[i % who.length]] ?? CAST.you} pose={ps} expression={ex} x={i * gap * dir * (1 - shrink * i * 0.5)} y={-i * shrink * 60} scale={sc} t={t + i * 0.37} seed={i * 7 + 3}
              facing={-dir} hold={ps === 'phone' ? 'phone' : null} glow={ps === 'phone' && !!spec.glow} />
          </g>
        );
      })}
    </g>
  );
};

// ------------------------------------------------------------------------------------ balance
const Balance: React.FC<P> = ({spec, p}) => {
  const at = (spec.at as number) ?? 2;
  const locked = p >= at;
  const q = clamp((p - at) * 8);
  return (
    <g>
      <rect x={-330} y={-170} width={660} height={340} rx={30} fill="#000" opacity={0.22} transform="translate(12 14)" />
      <rect x={-330} y={-170} width={660} height={340} rx={30} fill={CREAM} {...k} strokeWidth={6} />
      <rect x={-330} y={-170} width={660} height={84} rx={30} fill="#2f4a7a" {...k} strokeWidth={6} />
      <text x={-290} y={-112} fontFamily={FONT} fontWeight={800} fontSize={40} fill="#fff">Account balance</text>
      <text x={0} y={60} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={130} fill={locked ? '#9aa3b0' : INK} letterSpacing={-4}>{(spec.amount as string) ?? '₹42,318'}</text>
      <text x={0} y={128} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={34} fill={locked ? '#b8322a' : '#1f7d4b'}>{locked ? 'Cannot be moved today' : 'Available'}</text>
      {locked && (
        <g transform={`translate(250 -150) scale(${pop(q) * 1.5})`}>
          <path d="M -34 -20 L -34 -52 C -34 -96 34 -96 34 -52 L 34 -20" fill="none" stroke="#8b929c" strokeWidth={16} />
          <path d="M -34 -20 L -34 -52 C -34 -96 34 -96 34 -52 L 34 -20" fill="none" stroke={INK} strokeWidth={3} />
          <rect x={-58} y={-24} width={116} height={96} rx={16} fill="#f2b84b" {...k} strokeWidth={6} />
          <circle cx={0} cy={16} r={11} fill={INK} />
          <rect x={-5} y={18} width={10} height={26} fill={INK} />
        </g>
      )}
    </g>
  );
};

// --------------------------------------------------------------------------------- sign board
const SignBoard: React.FC<P> = ({spec, t}) => {
  const lines = ((spec.text as string) ?? 'CASH ONLY').split('|');
  const w = Math.max(...lines.map((l) => l.length)) * 34 + 80;
  const h = lines.length * 64 + 50;
  return (
    <g transform={`rotate(${Math.sin(t * 1.4) * 1.5})`}>
      {!spec.hang && <rect x={-8} y={-h / 2} width={16} height={h / 2 + 250} fill="#8b5a3c" {...k} />}
      <g transform={`translate(0 ${-h / 2 - 40})`}>
        <rect x={-w / 2} y={-h / 2} width={w} height={h} rx={10} fill={(spec.fill as string) ?? CREAM} {...k} strokeWidth={5} />
        {lines.map((l, i) => (
          <text key={i} x={0} y={i * 64 - (lines.length - 1) * 32 + 20} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={56} fill={(spec.color as string) ?? '#b8322a'}>{l}</text>
        ))}
      </g>
    </g>
  );
};

// ---------------------------------------------------------------------------------- groceries
const Goods: React.FC<P> = ({spec}) => {
  const kind = (spec.kind as string) ?? 'milk';
  if (kind === 'eggs')
    return (
      <g>
        <path d="M -90 0 L -100 -40 L 100 -40 L 90 0 Z" fill="#c9b48a" {...k} />
        {[0, 1, 2, 3].map((i) => <ellipse key={i} cx={-66 + i * 44} cy={-52} rx={18} ry={24} fill="#fbf3dc" {...k} strokeWidth={2.4} />)}
      </g>
    );
  return (
    <g>
      <path d="M -50 0 L -56 -110 Q 0 -130 56 -110 L 50 0 Z" fill="#f6fbff" {...k} />
      <path d="M -56 -110 Q 0 -130 56 -110 L 52 -84 Q 0 -100 -52 -84 Z" fill="#5b8def" {...k} strokeWidth={2.4} />
      <text x={0} y={-36} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={30} fill="#5b8def">MILK</text>
      <g transform="translate(96 0)">
        <path d="M -44 0 L -44 -50 Q -44 -84 0 -84 Q 44 -84 44 -50 L 44 0 Z" fill="#d9a05a" {...k} />
        <path d="M -24 -70 L -16 -52 M 0 -76 L 8 -56 M 22 -70 L 28 -52" stroke="#a8713c" strokeWidth={4} />
      </g>
    </g>
  );
};

// ---------------------------------------------------------------------------------- city pins
const CityPins: React.FC<P> = ({spec, p}) => {
  const items = (spec.items as [string, string][]) ?? [];
  return (
    <g>
      {items.map((it, i) => {
        const q = clamp((p - 0.08 - i * 0.16) * 9);
        if (q <= 0) return null;
        const x = (i - (items.length - 1) / 2) * 400;
        return (
          <g key={i} transform={`translate(${x} ${i % 2 ? 40 : -40}) scale(${pop(q)})`}>
            <path d="M 0 150 C -110 30 -120 -40 -120 -70 A 120 120 0 1 1 120 -70 C 120 -40 110 30 0 150 Z" fill={['#e9625a', '#2ec4b6', '#f2b84b', '#5b8def'][i % 4]} {...k} strokeWidth={6} />
            <circle cx={0} cy={-70} r={78} fill={CREAM} {...k} strokeWidth={4} />
            <text x={0} y={-52} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={50} fill={INK}>{it[1]}</text>
            <rect x={-150} y={176} width={300} height={66} rx={33} fill={CREAM} {...k} strokeWidth={4} />
            <text x={0} y={222} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={38} fill={INK}>{it[0]}</text>
          </g>
        );
      })}
    </g>
  );
};

export const MONEY_PROPS: Record<string, React.FC<P>> = {
  pay_phone: PayPhone,
  qr_stand: QrStand,
  chai_stall: ChaiStall,
  atm_booth: AtmBooth,
  petrol_pump: PetrolPump,
  auto: Auto,
  veg_cart: VegCart,
  shutter: Shutter,
  note: Note,
  wallet: Wallet,
  khata: Khata,
  cheque: Cheque,
  tv: Tv,
  queue: Queue,
  balance: Balance,
  sign_board: SignBoard,
  goods: Goods,
  city_pins: CityPins,
};

export {darken as _darken};
