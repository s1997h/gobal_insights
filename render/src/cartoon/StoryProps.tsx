import React from 'react';
import {INK} from './Character';
import type {PropSpec} from './Props';

/**
 * Props for company-history stories (first used for the Kodak episode): the 1975 digital-camera
 * prototype, a television that paints a picture in pixel by pixel, the "money machine" behind a
 * consumables business, an internal memo, a compact digital camera, a photo-sharing app and a jar of
 * skin cream. Brand-free: names come from the spec as plain text.
 *
 * proto_cam and tv_pixels stand on their base (y = 0 is the floor or table top); the others are drawn
 * around their centre, for the plain studio background.
 */

type P = {spec: PropSpec; t: number; p: number; fps: number};
const k = {stroke: INK, strokeWidth: 5, strokeLinejoin: 'round' as const, strokeLinecap: 'round' as const};
const FONT = 'Inter, Helvetica Neue, Arial, sans-serif';
const RED = '#e9443a';
const GOLD = '#f2b84b';
const TEAL = '#2ec4b6';
const CREAM = '#fffaf0';
const clamp = (v: number) => Math.max(0, Math.min(1, v));
const pop = (q: number) => (q <= 0 ? 0 : q >= 1 ? 1 : 1 + Math.sin(q * Math.PI) * 0.22 * (1 - q));
const fit = (text: string, size: number, room: number) => Math.min(size, room / Math.max(1, text.length * 0.74));
const num = (v: unknown, d: number) => (typeof v === 'number' ? v : d);

// ------------------------------------------------------------------------------------- 1975 camera
/** The toaster-sized prototype: a metal box, a movie-camera lens, a cassette deck. `save` starts the
 * 23-second save bar (shot progress 0..1); `secs` is the number it counts to. */
const ProtoCam: React.FC<P> = ({spec, p, t}) => {
  const save = spec.save as number | undefined;
  const secs = num(spec.secs, 23);
  const q = save === undefined ? 0 : clamp((p - save) / Math.max(0.05, 0.92 - save));
  const spin = save !== undefined && p > save && q < 1 ? t * 360 : 0;
  return (
    <g>
      {/* body */}
      <rect x={-200} y={-250} width={400} height={250} rx={16} fill="#9aa7b4" {...k} />
      <rect x={-200} y={-250} width={400} height={46} rx={14} fill="#7d8b99" {...k} />
      <path d="M -80 -250 L -80 -292 L 80 -292 L 80 -250" fill="none" stroke={INK} strokeWidth={12} strokeLinecap="round" />
      {/* lens */}
      <rect x={-262} y={-170} width={70} height={110} rx={10} fill="#4b5563" {...k} />
      <ellipse cx={-262} cy={-115} rx={22} ry={52} fill="#1f2937" {...k} />
      <ellipse cx={-262} cy={-115} rx={9} ry={24} fill="#6b8fb8" opacity={0.8} />
      {/* circuit window */}
      <rect x={-170} y={-190} width={150} height={150} rx={8} fill="#2f5d3a" {...k} strokeWidth={4} />
      {[0, 1, 2].map((i) => (
        <rect key={i} x={-155 + i * 46} y={-170} width={30} height={50} rx={3} fill="#1b1f24" />
      ))}
      <path d="M -160 -95 L -40 -95 M -160 -75 L -60 -75 M -100 -60 L -30 -60" stroke={GOLD} strokeWidth={4} />
      {/* cassette deck */}
      <rect x={10} y={-190} width={170} height={115} rx={8} fill="#2a2f36" {...k} strokeWidth={4} />
      <rect x={28} y={-176} width={134} height={70} rx={6} fill="#c9b79c" stroke={INK} strokeWidth={3} />
      {[64, 126].map((cx) => (
        <g key={cx} transform={`translate(${cx} -141) rotate(${spin})`}>
          <circle r={20} fill={CREAM} stroke={INK} strokeWidth={3} />
          <path d="M 0 -20 L 0 20 M -20 0 L 20 0" stroke={INK} strokeWidth={3} />
        </g>
      ))}
      <circle cx={160} cy={-60} r={10} fill={save !== undefined && p > save && q < 1 && Math.sin(t * 12) > 0 ? RED : '#5b1d1a'} stroke={INK} strokeWidth={3} />
      <text x={-150} y={-14} fontFamily={FONT} fontWeight={800} fontSize={24} fill={INK}>{String(spec.label ?? 'PROTOTYPE')}</text>
      {/* save bar */}
      {save !== undefined && p > save && (
        <g transform={`translate(0 -420) scale(${pop(clamp((p - save) * 6))})`}>
          <rect x={-250} y={-58} width={500} height={116} rx={18} fill={CREAM} {...k} />
          <text x={-220} y={-14} fontFamily={FONT} fontWeight={900} fontSize={34} fill={INK}>{q < 1 ? 'SAVING PHOTO…' : 'SAVED: 1 PHOTO'}</text>
          <text x={220} y={-14} textAnchor="end" fontFamily={FONT} fontWeight={900} fontSize={34} fill={q < 1 ? RED : TEAL}>{`${Math.min(secs, Math.floor(q * secs))} s`}</text>
          <rect x={-220} y={10} width={440} height={26} rx={13} fill="#e3ddd0" stroke={INK} strokeWidth={3} />
          <rect x={-220} y={10} width={440 * q} height={26} rx={13} fill={q < 1 ? GOLD : TEAL} stroke={INK} strokeWidth={3} />
        </g>
      )}
    </g>
  );
};

// --------------------------------------------------------------------------------- pixel television
const FACE = (() => {
  // a 20 x 15 grey-level picture of a face, drawn once: 0 dark .. 1 light
  const W = 20;
  const H = 15;
  const px: number[] = [];
  const skin: boolean[] = [];
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const dx = (x - 9.5) / 6.2;
      const dy = (y - 7.5) / 6.5;
      const inFace = dx * dx + dy * dy < 1;
      const hair = inFace && y < 4;
      const eye = (y === 6 || y === 7) && (x === 7 || x === 12);
      const mouth = y === 10 && x >= 8 && x <= 11;
      let v = inFace ? 0.82 : 0.28 + ((x * 7 + y * 13) % 5) * 0.03;
      if (hair) v = 0.18;
      if (eye || mouth) v = 0.12;
      if (inFace && x > 13) v -= 0.18; // shadow side
      px.push(v);
      skin.push(inFace && !hair);
    }
  }
  return {W, H, px, skin};
})();

/** An old television on legs showing a 100 x 100-pixel photo, painted in row by row between `from` and `to`. */
const TvPixels: React.FC<P> = ({spec, p, t}) => {
  const noisy = !!spec.static;
  const from = num(spec.from, 0.12);
  const to = num(spec.to, 0.8);
  const rows = Math.floor(clamp((p - from) / Math.max(0.05, to - from)) * FACE.H);
  const cw = 290 / FACE.W;
  const ch = 216 / FACE.H;
  return (
    <g>
      <path d="M -120 0 L -90 -60 M 120 0 L 90 -60" stroke={INK} strokeWidth={10} strokeLinecap="round" />
      <rect x={-230} y={-370} width={460} height={320} rx={30} fill="#8a6a4a" {...k} />
      <rect x={-200} y={-345} width={330} height={260} rx={24} fill="#1d2127" {...k} />
      <g transform="translate(-180 -323)">
        {FACE.px.map((v0, i) => {
          const r = Math.floor(i / FACE.W);
          if (r >= rows) return null;
          // `static`: where the face should be there is only noise (the first, broken picture)
          const fuzz = noisy && FACE.skin[i];
          const v = fuzz ? ((Math.sin(i * 12.9898 + Math.floor(t * 14) * 78.233) * 43758.5453) % 1 + 1) % 1 : v0;
          const g = Math.round(40 + v * 200);
          return <rect key={i} x={(i % FACE.W) * cw} y={r * ch} width={cw + 0.6} height={ch + 0.6} fill={`rgb(${g},${g},${g})`} />;
        })}
        {rows < FACE.H && p > from && <rect x={0} y={rows * ch} width={290} height={4} fill="#9fe" opacity={0.8} />}
      </g>
      <circle cx={180} cy={-290} r={18} fill="#c9b79c" stroke={INK} strokeWidth={4} />
      <circle cx={180} cy={-230} r={18} fill="#c9b79c" stroke={INK} strokeWidth={4} />
      {spec.label ? (
        <text x={0} y={60} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={40} fill={INK}>{String(spec.label)}</text>
      ) : null}
    </g>
  );
};

// ----------------------------------------------------------------------------------- money machine
const NodeIcon: React.FC<{i: number}> = ({i}) => {
  if (i === 0) // camera
    return (
      <g>
        <rect x={-60} y={-38} width={120} height={80} rx={12} fill="#5b6470" {...k} />
        <circle cx={0} cy={2} r={26} fill="#1f2937" {...k} />
        <rect x={20} y={-52} width={30} height={16} rx={4} fill="#5b6470" {...k} strokeWidth={4} />
      </g>
    );
  if (i === 1) // film roll
    return (
      <g>
        <rect x={-40} y={-50} width={60} height={100} rx={10} fill={GOLD} {...k} />
        <path d="M 20 -30 L 70 -30 L 70 30 L 20 30" fill="#3b2f2a" {...k} strokeWidth={4} />
        {[-20, 0, 20].map((y) => <rect key={y} x={30} y={y - 5} width={10} height={10} fill={CREAM} />)}
      </g>
    );
  if (i === 2) // chemicals
    return (
      <g>
        <path d="M -20 -55 L 20 -55 L 20 -25 L 45 40 Q 45 55 30 55 L -30 55 Q -45 55 -45 40 L -20 -25 Z" fill="#cfe9ff" {...k} />
        <path d="M -38 20 L 38 20 L 45 40 Q 45 55 30 55 L -30 55 Q -45 55 -45 40 Z" fill={TEAL} stroke={INK} strokeWidth={4} />
      </g>
    );
  return ( // print
    <g transform="rotate(-6)">
      <rect x={-55} y={-55} width={110} height={110} fill={CREAM} {...k} />
      <rect x={-42} y={-42} width={84} height={66} fill="#8fd3f4" stroke={INK} strokeWidth={3} />
      <path d="M -42 24 L -10 -6 L 10 12 L 24 0 L 42 24 Z" fill="#4f9a5a" stroke={INK} strokeWidth={3} />
      <circle cx={24} cy={-24} r={9} fill={GOLD} />
    </g>
  );
};

/** Camera -> film -> chemicals -> prints -> money: the business that paid on every click. Nodes appear
 * one by one; `broken` (progress) greys out everything after the camera and crosses out the film. */
const MoneyMachine: React.FC<P> = ({spec, p, t}) => {
  const labels = (spec.labels as string[]) ?? ['CAMERA', 'FILM', 'CHEMICALS', 'PRINTS'];
  const tags = (spec.tags as string[]) ?? ['CHEAP', '$', '$', '$'];
  const broken = spec.broken as number | undefined;
  const isBroken = broken !== undefined && p > broken;
  const xs = [-660, -330, 0, 330];
  return (
    <g>
      {xs.map((x, i) => {
        const ats = spec.ats as number[] | undefined;
        const q = i === 0 ? 1 : clamp((p - (ats ? ats[i - 1] : 0.04 + i * 0.12)) * 5); // the first node is there on the cut
        const dead = isBroken && i > 0;
        return (
          <g key={i} opacity={dead ? 0.35 : 1}>
            {i > 0 && q > 0 && <path d={`M ${x - 230} 0 L ${x - 120} 0`} stroke={dead ? '#999' : GOLD} strokeWidth={14} strokeLinecap="round" />}
            {i > 0 && q > 0 && <path d={`M ${x - 140} -22 L ${x - 112} 0 L ${x - 140} 22`} fill="none" stroke={dead ? '#999' : GOLD} strokeWidth={14} strokeLinecap="round" strokeLinejoin="round" />}
            {q > 0 && (
              <g transform={`translate(${x} 0) scale(${pop(q)})`}>
                <circle r={110} fill={CREAM} {...k} strokeWidth={6} />
                {spec.plain ? (
                  <text x={0} y={30} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={96} fill={INK}>{i + 1}</text>
                ) : (
                  <g transform="translate(0 -14)">
                    <NodeIcon i={i} />
                  </g>
                )}
                <text x={0} y={160} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(labels[i] ?? '', 44, 270)} fill={CREAM} stroke={INK} strokeWidth={10} paintOrder="stroke">{labels[i]}</text>
                <g transform="translate(78 -86)">
                  <circle r={34} fill={i === 0 ? '#e3ddd0' : GOLD} stroke={INK} strokeWidth={4} />
                  <text x={0} y={i === 0 ? 7 : 12} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={i === 0 ? 18 : 34} fill={INK}>{tags[i]}</text>
                </g>
              </g>
            )}
          </g>
        );
      })}
      {/* the pile of money at the end */}
      {(() => {
        const ats = spec.ats as number[] | undefined;
        const q = clamp((p - (ats ? ats[3] : 0.04 + 4 * 0.12)) * 5);
        if (q <= 0) return null;
        const dead = isBroken;
        return (
          <g transform={`translate(640 0) scale(${pop(q)})`} opacity={dead ? 0.35 : 1}>
            <path d="M -330 0 L -220 0" stroke={dead ? '#999' : GOLD} strokeWidth={14} strokeLinecap="round" />
            {[0, 1, 2, 3, 4].map((j) => (
              <ellipse key={j} cx={-30 + (j % 2) * 50} cy={60 - j * 28} rx={60} ry={18} fill={GOLD} stroke={INK} strokeWidth={4} />
            ))}
            {!dead && [0, 1, 2].map((j) => {
              const y = ((t * 120 + j * 70) % 210) - 60;
              return <text key={j} x={-70 + j * 60} y={-y - 40} fontFamily={FONT} fontWeight={900} fontSize={44} fill="#2f8f4e" opacity={1 - (y + 60) / 210}>$</text>;
            })}
            <text x={0} y={160} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={44} fill={GOLD} stroke={INK} strokeWidth={10} paintOrder="stroke">{String(spec.end ?? 'KODAK')}</text>
          </g>
        );
      })()}
      {isBroken && (
        <g transform={`translate(-330 0) scale(${pop(clamp((p - (broken as number)) * 6))}) rotate(${Math.sin(t * 30) * 2})`}>
          <path d="M -120 -120 L 120 120 M 120 -120 L -120 120" stroke={RED} strokeWidth={26} strokeLinecap="round" />
        </g>
      )}
    </g>
  );
};

// ------------------------------------------------------------------------------------------- memo
/** An internal report: a title, a line of small print, and up to three lines that appear one by one
 * (`lines`, e.g. "BAD NEWS|digital can replace film"), then a stamp (`stamp`) slams on at `at`. */
const Memo: React.FC<P> = ({spec, p, t}) => {
  const lines = (spec.lines as string[]) ?? [];
  const at = num(spec.at, 0.72);
  const sq = clamp((p - at) * 7);
  return (
    <g transform="rotate(-2)">
      <rect x={-330} y={-400} width={660} height={800} rx={10} fill="#000" opacity={0.18} transform="translate(14 16)" />
      <rect x={-330} y={-400} width={660} height={800} rx={10} fill={CREAM} {...k} />
      <text x={-280} y={-320} fontFamily={FONT} fontWeight={900} fontSize={fit(String(spec.head ?? ''), 52, 560)} fill={INK}>{String(spec.head ?? '')}</text>
      <text x={-280} y={-272} fontFamily={FONT} fontWeight={600} fontSize={28} fill="#6b6f76">{String(spec.sub ?? '')}</text>
      <path d="M -280 -245 L 280 -245" stroke={INK} strokeWidth={4} />
      {[0, 1, 2, 3, 4, 5, 6].map((i) => (
        <rect key={i} x={-280} y={-215 + i * 26} width={i % 3 === 2 ? 330 : 540} height={10} rx={5} fill="#d9d3c6" />
      ))}
      {lines.map((ln, i) => {
        const ats = spec.ats as number[] | undefined;
        const q = clamp((p - (ats ? ats[i] : 0.12 + i * 0.2)) * 5);
        if (q <= 0) return null;
        const [a, b] = ln.split('|');
        const bad = /bad/i.test(a);
        return (
          <g key={i} transform={`translate(-280 ${20 + i * 130})`} opacity={q}>
            <rect x={-14} y={-46} width={588} height={110} rx={12} fill={bad ? '#fde2df' : '#dff5ef'} stroke={INK} strokeWidth={3} />
            <text x={6} y={-6} fontFamily={FONT} fontWeight={900} fontSize={34} fill={bad ? RED : '#1f8a70'}>{a}</text>
            <text x={6} y={40} fontFamily={FONT} fontWeight={700} fontSize={fit(b ?? '', 34, 550)} fill={INK}>{b}</text>
          </g>
        );
      })}
      {spec.stamp && sq > 0 ? (
        <g transform={`translate(150 300) rotate(-12) scale(${1 + (1 - sq) * 1.4})`} opacity={sq}>
          <rect x={-190} y={-62} width={380} height={124} rx={12} fill="none" stroke={RED} strokeWidth={10} />
          <text x={0} y={22} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(String(spec.stamp), 70, 340)} fill={RED} transform={`rotate(${Math.sin(t * 3) * 0})`}>{String(spec.stamp)}</text>
        </g>
      ) : null}
    </g>
  );
};

// -------------------------------------------------------------------------------------- digicam
/** A 2000s compact digital camera; `tag` (e.g. "-$60") hangs from it from `at` on. */
const Digicam: React.FC<P> = ({spec, p, t}) => {
  const at = num(spec.at, 0.45);
  const q = clamp((p - at) * 5);
  return (
    <g>
      <rect x={-230} y={-150} width={460} height={300} rx={40} fill="#d4d9df" {...k} strokeWidth={6} />
      <rect x={-230} y={-150} width={460} height={60} rx={30} fill="#b9c0c8" {...k} strokeWidth={6} />
      <rect x={110} y={-185} width={70} height={36} rx={10} fill="#9aa3ad" {...k} />
      <circle cx={30} cy={30} r={100} fill="#8c949e" {...k} strokeWidth={6} />
      <circle cx={30} cy={30} r={66} fill="#1f2937" {...k} />
      <circle cx={6} cy={8} r={18} fill="#6b8fb8" opacity={0.8} />
      <rect x={-200} y={-120} width={80} height={44} rx={8} fill={CREAM} stroke={INK} strokeWidth={4} />
      <text x={-160} y={-88} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={22} fill={INK}>{String(spec.label ?? 'DIGITAL')}</text>
      {spec.tag && q > 0 ? (
        <g transform={`translate(240 60) rotate(${12 + Math.sin(t * 3) * 4}) scale(${pop(q)})`}>
          <path d="M -20 -20 L 0 -60" stroke={INK} strokeWidth={4} />
          <path d="M -70 -20 L 110 -20 L 140 40 L 110 100 L -70 100 Z" fill={RED} {...k} />
          <circle cx={-40} cy={40} r={10} fill={CREAM} stroke={INK} strokeWidth={3} />
          <text x={45} y={58} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(String(spec.tag), 56, 160)} fill={CREAM}>{String(spec.tag)}</text>
        </g>
      ) : null}
    </g>
  );
};

// ------------------------------------------------------------------------------------ photo app
/** A phone running a photo-sharing app: a grid of photos with hearts floating up. `badge` sits under it. */
const PhotoApp: React.FC<P> = ({spec, p, t}) => {
  const tiles = ['#8fd3f4', '#f7b7a3', '#c3e88d', '#ffd166', '#cdb4db', '#90e0ef', '#f4a261', '#a8dadc', '#e5989b'];
  return (
    <g>
      <rect x={-170} y={-330} width={340} height={660} rx={46} fill="#1f2328" {...k} strokeWidth={6} />
      <rect x={-150} y={-300} width={300} height={600} rx={30} fill={CREAM} />
      <text x={0} y={-252} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={34} fill={INK}>{String(spec.label ?? 'PHOTOS')}</text>
      {tiles.map((c, i) => {
        const q = clamp((p - 0.05 - i * 0.05) * 6);
        const x = -138 + (i % 3) * 94;
        const y = -224 + Math.floor(i / 3) * 112;
        return (
          <g key={i} opacity={q}>
            <rect x={x} y={y} width={88} height={104} rx={8} fill={c} stroke={INK} strokeWidth={3} />
            <path d={`M ${x} ${y + 104} L ${x + 30} ${y + 64} L ${x + 50} ${y + 84} L ${x + 66} ${y + 70} L ${x + 88} ${y + 104} Z`} fill="#4f9a5a" opacity={0.75} />
          </g>
        );
      })}
      {[0, 1, 2, 3, 4].map((j) => {
        const y = ((t * 140 + j * 120) % 520) - 100;
        return (
          <path key={j} transform={`translate(${130 + (j % 2) * 40} ${-y + 120}) scale(${0.9 + (j % 3) * 0.2})`} opacity={clamp(1 - (y + 100) / 520) * clamp(p * 6)}
            d="M 0 10 C -30 -12 -24 -36 0 -22 C 24 -36 30 -12 0 10 Z" fill={RED} stroke={INK} strokeWidth={3} />
        );
      })}
      {spec.badge ? (
        <g transform="translate(0 400)">
          <rect x={-170} y={-40} width={340} height={80} rx={40} fill={GOLD} {...k} />
          <text x={0} y={14} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(String(spec.badge), 40, 300)} fill={INK}>{String(spec.badge)}</text>
        </g>
      ) : null}
    </g>
  );
};

// ------------------------------------------------------------------------------------------- cream
/** A jar of skin cream with its name on the label. */
const Cream: React.FC<P> = ({spec, t}) => {
  const label = String(spec.label ?? 'SKIN CREAM').toUpperCase();
  return (
    <g transform={`translate(0 ${Math.sin(t * 2) * 6})`}>
      {Array.from({length: 10}, (_, i) => (
        <path key={i} d="M 0 -300 L 0 -270" transform={`rotate(${i * 36 + t * 12})`} stroke={GOLD} strokeWidth={8} strokeLinecap="round" />
      ))}
      <rect x={-200} y={-60} width={400} height={230} rx={40} fill="#fff4f2" {...k} strokeWidth={6} />
      <rect x={-215} y={-150} width={430} height={100} rx={26} fill="#d8434c" {...k} strokeWidth={6} />
      <rect x={-150} y={10} width={300} height={90} rx={14} fill={CREAM} stroke={INK} strokeWidth={4} />
      <text x={0} y={70} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(label, 46, 270)} fill="#a8323a">{label}</text>
    </g>
  );
};


// ------------------------------------------------------------------------------------------ napkin
/** The money machine sketched on a paper napkin, the way an executive explains it after a meeting. */
const Napkin: React.FC<P> = (props) => {
  const W = 1260;
  const H = 700;
  const dots = [];
  for (let x = -W / 2 + 30; x < W / 2 - 10; x += 34) dots.push([x, -H / 2], [x, H / 2]);
  for (let y = -H / 2 + 30; y < H / 2 - 10; y += 34) dots.push([-W / 2, y], [W / 2, y]);
  return (
    <g transform="rotate(-2.5)">
      <rect x={-W / 2} y={-H / 2} width={W} height={H} rx={8} fill="#000" opacity={0.22} transform="translate(18 22)" />
      <rect x={-W / 2} y={-H / 2} width={W} height={H} rx={8} fill="#fbf9f3" />
      {dots.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={15} fill="#fbf9f3" />
      ))}
      <rect x={-W / 2 + 40} y={-H / 2 + 40} width={W - 80} height={H - 80} rx={6} fill="none" stroke="#e7e1d4" strokeWidth={5} strokeDasharray="3 13" strokeLinecap="round" />
      <path d={`M 0 ${-H / 2} L 0 ${H / 2} M ${-W / 2} 0 L ${W / 2} 0`} stroke="#ece6da" strokeWidth={6} />
      <g transform="translate(-50 -40) scale(0.7)">
        <MoneyMachine {...props} />
      </g>
      {spec(props).sign ? (
        <text x={W / 2 - 70} y={H / 2 - 50} textAnchor="end" fontFamily="'Comic Sans MS', 'Segoe Print', cursive" fontSize={44} fill="#2b3a67" transform="rotate(-4)">{String(spec(props).sign)}</text>
      ) : null}
    </g>
  );
};
const spec = (props: P) => props.spec;

// ------------------------------------------------------------------------------------------ drawer
/** Mini versions of the things that end up in the drawer. */
const DrawerItem: React.FC<{k: string; t: number}> = ({k: kind, t}) => {
  if (kind === 'cam')
    return (
      <g transform="translate(-10 0) scale(0.6)">
        <ProtoCam spec={{t: 'proto_cam', x: 0, y: 0}} p={0} t={0} fps={30} />
      </g>
    );
  if (kind === 'memo')
    return (
      <g transform="rotate(8)">
        <rect x={-95} y={-125} width={190} height={130} rx={6} fill={CREAM} {...k} strokeWidth={4} />
        <text x={0} y={-90} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={22} fill={INK}>DIGITAL vs FILM</text>
        {[0, 1, 2].map((i) => (
          <rect key={i} x={-70} y={-70 + i * 20} width={i === 2 ? 80 : 140} height={8} rx={4} fill="#d9d3c6" />
        ))}
      </g>
    );
  if (kind === 'bulb') {
    const glow = 0.55 + 0.25 * Math.sin(t * 4);
    return (
      <g transform="translate(0 -70)">
        <circle r={120} fill={GOLD} opacity={glow * 0.45} />
        <circle r={60} fill="#fff3b0" {...k} />
        <rect x={-26} y={50} width={52} height={36} rx={6} fill="#9aa3b0" {...k} />
      </g>
    );
  }
  return null;
};

/**
 * A wooden desk drawer seen from the front, standing on y = 0. It slides open over `open` [from, to],
 * items in `items` ({k: 'cam' | 'memo' | 'bulb', at?}) are inside (or drop in at `at`), and it slams
 * shut at `shut`. The label card on the front says `label` (default "LATER").
 */
const Drawer: React.FC<P> = ({spec: sp, p, t}) => {
  const open = (sp.open as number[] | undefined) ?? [0.05, 0.25];
  const shut = sp.shut as number | undefined;
  let o = clamp((p - open[0]) / Math.max(0.02, open[1] - open[0]));
  o = 1 - Math.pow(1 - o, 3);
  if (shut !== undefined) o = Math.min(o, 1 - Math.pow(clamp((p - shut) * 9), 2));
  const items = (sp.items as {k: string; at?: number}[] | undefined) ?? [];
  const dy = o * 200;
  const front = -470 + dy;
  const bang = shut !== undefined && p > shut ? Math.max(0, 1 - (p - shut) * 14) : 0;
  return (
    <g transform={`translate(${Math.sin(t * 70) * 8 * bang} 0)`}>
      <rect x={-470} y={-560} width={940} height={560} rx={12} fill="#7a4b2c" {...k} strokeWidth={6} />
      <rect x={-500} y={-600} width={1000} height={56} rx={10} fill="#9a6338" {...k} strokeWidth={6} />
      {/* lower drawer, shut */}
      <rect x={-400} y={-250} width={800} height={210} rx={10} fill="#93603a" {...k} strokeWidth={6} />
      <rect x={-70} y={-160} width={140} height={28} rx={14} fill="#d8b56a" {...k} strokeWidth={4} />
      {/* slot of the top drawer */}
      <rect x={-400} y={-500} width={800} height={210} rx={8} fill="#2a1a10" {...k} strokeWidth={6} />
      {o > 0.01 && (
        <g>
          {/* inside of the open drawer: floor and side walls */}
          <path d={`M -400 -500 L 400 -500 L 432 ${front} L -432 ${front} Z`} fill="#4a2e1a" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
          <path d={`M -400 -500 L -432 ${front} L -432 ${front + 30} L -400 -470 Z M 400 -500 L 432 ${front} L 432 ${front + 30} L 400 -470 Z`} fill="#6b4226" stroke={INK} strokeWidth={4} strokeLinejoin="round" />
          {items.map((it, i) => {
            const q = it.at === undefined ? 1 : clamp((p - it.at) * 7);
            if (q <= 0) return null;
            const x = items.length === 1 ? 0 : -170 + (340 * i) / (items.length - 1);
            const y = -500 + dy * 0.78 - (1 - q) * 420;
            return (
              <g key={i} transform={`translate(${x} ${y})`} opacity={Math.min(1, q * 3)}>
                <DrawerItem k={it.k} t={t} />
              </g>
            );
          })}
        </g>
      )}
      {/* drawer front */}
      <g transform={`translate(0 ${front + 105}) scale(${1 + o * 0.08})`}>
        <rect x={-410} y={-108} width={820} height={216} rx={10} fill="#a8703f" {...k} strokeWidth={6} />
        <rect x={-380} y={-84} width={760} height={168} rx={8} fill="none" stroke="#7a4b2c" strokeWidth={5} />
        <rect x={-80} y={-6} width={160} height={30} rx={15} fill="#d8b56a" {...k} strokeWidth={4} />
        <rect x={-95} y={-74} width={190} height={56} rx={6} fill={CREAM} stroke={INK} strokeWidth={4} />
        <text x={0} y={-34} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(String(sp.label ?? 'LATER'), 34, 170)} fill={INK}>{String(sp.label ?? 'LATER')}</text>
      </g>
    </g>
  );
};

// ------------------------------------------------------------------------------------------ the news
/** The studio behind the anchor: a dark blue set and a graphic box with `box` in it. Full frame, centre-anchored. */
const NewsBg: React.FC<P> = ({spec: sp, t}) => (
  <g>
    <defs>
      <linearGradient id="newsBg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#0f2a5a" />
        <stop offset="1" stopColor="#061633" />
      </linearGradient>
    </defs>
    <rect x={-1100} y={-640} width={2200} height={1280} fill="url(#newsBg)" />
    {[0, 1, 2, 3, 4, 5].map((i) => (
      <rect key={i} x={-1100 + i * 380 + ((t * 20) % 380)} y={-640} width={60} height={1280} fill="#2a5aa8" opacity={0.12} transform="skewX(-18)" />
    ))}
    {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
      <rect key={i} x={-1000 + i * 210} y={60 - ((i * 37) % 5) * 60} width={150} height={600} fill="#0a1f45" opacity={0.85} />
    ))}
    <g transform="translate(470 -150)">
      <rect x={-300} y={-190} width={600} height={380} rx={18} fill="#f2b100" stroke="#ffffff" strokeWidth={8} />
      <rect x={-300} y={-190} width={600} height={380} rx={18} fill="none" stroke={INK} strokeWidth={4} />
      <text x={0} y={30} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(String(sp.box ?? 'KODAK'), 150, 520)} fill="#c8102e">{String(sp.box ?? 'KODAK')}</text>
      {sp.stamp ? (
        <g transform="translate(20 120) rotate(-8)">
          <rect x={-230} y={-48} width={460} height={96} rx={10} fill="#ffffff" stroke="#c8102e" strokeWidth={8} />
          <text x={0} y={22} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={fit(String(sp.stamp), 64, 420)} fill="#c8102e">{String(sp.stamp)}</text>
        </g>
      ) : null}
    </g>
  </g>
);

/** In front of the anchor: the desk, the BREAKING NEWS strip with `head`, a ticker with `ticker`, a LIVE bug and an old TV's rounded bezel. */
const NewsFg: React.FC<P> = ({spec: sp, t, p}) => {
  const tick = String(sp.ticker ?? '');
  const off = (t * 160) % (tick.length * 22 + 400);
  const q = clamp(p * 10);
  return (
    <g>
      <path d="M -1100 250 L 1100 250 L 1100 640 L -1100 640 Z" fill="#14305f" />
      <path d="M -760 205 L 760 205 L 820 300 L -820 300 Z" fill="#dfe6f2" stroke={INK} strokeWidth={5} strokeLinejoin="round" />
      <rect x={-820} y={300} width={1640} height={240} fill="#1b3d78" stroke={INK} strokeWidth={5} />
      <g transform={`translate(${-1100 * (1 - q)} -150)`}>
        <rect x={-880} y={250} width={420} height={70} fill="#c8102e" />
        <text x={-860} y={300} fontFamily={FONT} fontWeight={900} fontSize={40} fill="#ffffff">BREAKING NEWS</text>
        <rect x={-960} y={320} width={1920} height={110} fill="#ffffff" />
        <text x={-860} y={395} fontFamily={FONT} fontWeight={900} fontSize={fit(String(sp.head ?? ''), 62, 1680)} fill="#0b1b3a">{String(sp.head ?? '')}</text>
        <rect x={-960} y={430} width={1920} height={56} fill="#0b1b3a" />
        <text x={-900 - off + 1900} y={468} fontFamily={FONT} fontWeight={700} fontSize={30} fill="#ffd54a">{tick}</text>
      </g>
      <g transform="translate(-820 -440)">
        <rect x={0} y={0} width={110} height={50} rx={6} fill="#c8102e" />
        <text x={55} y={36} textAnchor="middle" fontFamily={FONT} fontWeight={900} fontSize={30} fill="#ffffff" opacity={0.6 + 0.4 * Math.sin(t * 6)}>LIVE</text>
      </g>
      {sp.tv !== false && (
        <g>
          {[...Array(54)].map((_, i) => (
            <rect key={i} x={-1000} y={-560 + i * 21} width={2000} height={4} fill="#000" opacity={0.07} />
          ))}
          <path fillRule="evenodd" d="M -1100 -640 L 1100 -640 L 1100 640 L -1100 640 Z M -905 -470 Q -910 -515 -860 -515 L 860 -515 Q 910 -515 905 -470 L 915 470 Q 915 515 865 515 L -865 515 Q -915 515 -915 470 Z" fill="#2b2420" />
          <path d="M -905 -470 Q -910 -515 -860 -515 L 860 -515 Q 910 -515 905 -470 L 915 470 Q 915 515 865 515 L -865 515 Q -915 515 -915 470 Z" fill="none" stroke="#111" strokeWidth={14} />
        </g>
      )}
    </g>
  );
};


// --------------------------------------------------------------------------------------- worktable
/** A workshop table standing on y = 0 with its top at y = -210, for props to sit on in the foreground. */
const Worktable: React.FC<P> = ({spec: sp}) => (
  <g>
    <rect x={-360} y={-180} width={26} height={180} fill="#6b4226" {...k} />
    <rect x={334} y={-180} width={26} height={180} fill="#6b4226" {...k} />
    <rect x={-330} y={-60} width={660} height={18} fill="#7a4b2c" {...k} strokeWidth={4} />
    <rect x={-400} y={-214} width={800} height={36} rx={8} fill="#a8703f" {...k} />
    <rect x={-380} y={-180} width={760} height={22} fill="#8a5a36" {...k} strokeWidth={4} />
    {sp.mess !== false && (
      <g>
        <path d="M -330 -214 C -300 -250 -260 -200 -230 -236 C -200 -268 -170 -220 -150 -240" fill="none" stroke="#c0392b" strokeWidth={6} strokeLinecap="round" />
        <rect x={210} y={-232} width={90} height={18} rx={4} fill="#3b82c4" {...k} strokeWidth={3} />
        <rect x={300} y={-228} width={40} height={10} rx={3} fill="#9aa3b0" stroke={INK} strokeWidth={3} />
      </g>
    )}
  </g>
);

export const STORY_PROPS: Record<string, React.FC<P>> = {
  worktable: Worktable,
  napkin: Napkin,
  drawer: Drawer,
  news_bg: NewsBg,
  news_fg: NewsFg,
  proto_cam: ProtoCam,
  tv_pixels: TvPixels,
  money_machine: MoneyMachine,
  memo: Memo,
  digicam: Digicam,
  photo_app: PhotoApp,
  cream: Cream,
};
