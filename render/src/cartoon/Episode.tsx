import React from 'react';
import {AbsoluteFill, CalculateMetadataFunction, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {Character, type Expression, type Item, type Pose} from './Character';
import {CAST} from './Cast';
import {SETS} from './Places';
import {PropView, type PropSpec} from './Props';
import {FxView, type FxSpec} from './Fx';
import {DayBadge, OverlayView, PlaceTag, TimeBadge, parseClock, type OvSpec} from './Overlays';

/**
 * A whole cartoon episode from data: shots.json (what is on screen) and timing.json (when).
 * Each shot is one set, a few actors, props, effects, an optional overlay and a camera move.
 */

export type ActorSpec = {
  who: string;
  pose: Pose;
  expr: Expression;
  x: number;
  y: number;
  s?: number;
  face?: number;
  hold?: Item;
  glow?: boolean;
  walk?: [number, number];
  pose2?: Pose;
  expr2?: Expression;
  at?: number;
  nude?: boolean;
};

/** who speaks when within a shot: actor index and start/end seconds from the shot's start */
export type Speak = {a: number; s: number; e: number};
/** one caption word with absolute start/end seconds */
export type Word = {w: string; s: number; e: number};

export type Shot = {
  id: string;
  n: string;
  set: string;
  setopt?: Record<string, unknown>;
  day?: number | null;
  cam?: number[];
  actors?: ActorSpec[];
  props?: PropSpec[];
  fx?: FxSpec[];
  ov?: OvSpec;
  min?: number;
  /** wall clock for hour-by-hour stories, e.g. "9:30 AM"; also sets the light */
  clock?: string | null;
  tod?: 'dawn' | 'day' | 'dusk' | 'night' | 'sepia';
  /** place and date of the scene, e.g. "Rochester, 1975" */
  where?: string | null;
  /** how the shot arrives: a small punch-in (default), a wipe for a new chapter, or a plain cut */
  tr?: 'punch' | 'wipe' | 'cut' | 'fade';
  /** camera shake between two progress values */
  shake?: [number, number];
  /** lines spoken on screen: drives the speaking character's mouth */
  speak?: Speak[];
  /** draw characters in the big-head chibi style */
  chibi?: boolean;
  /** a cut-in partway through the shot: from progress `cut` on, the camera is `cam2` (same voice, new angle) */
  cam2?: number[];
  cut?: number;
};

export type EpisodeProps = {
  shots: Shot[];
  timing: {total_sec: number; scenes: {id: string; start_ms: number; end_ms: number}[]};
  fonts?: boolean;
  /** word-by-word captions along the bottom */
  words?: Word[];
};

let fontsLoaded = false;
const ensureFonts = () => {
  if (fontsLoaded) return;
  fontsLoaded = true;
  for (const [file, weight] of [
    ['fonts/Inter-Regular.otf', '400'],
    ['fonts/Inter-SemiBold.otf', '600'],
    ['fonts/Inter-Bold.otf', '700'],
    ['fonts/Inter-ExtraBold.otf', '800'],
    ['fonts/Inter-ExtraBold.otf', '900'],
  ]) {
    loadFont({family: 'Inter', url: staticFile(file), weight}).catch((e) => console.warn('font failed', file, e));
  }
};

export const calcEpisode: CalculateMetadataFunction<EpisodeProps> = ({props}) => ({
  durationInFrames: Math.max(30, Math.ceil(props.timing.total_sec * 30)),
});

const ease = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x * x * (3 - 2 * x));
const scaleFor = (set: string) => (set.startsWith('img:') ? 1.4 : set === 'studio' ? 1.85 : 1.55);
const todOf = (shot: Shot): NonNullable<Shot['tod']> => {
  if (shot.tod) return shot.tod;
  if (!shot.clock) return 'day';
  const h = parseClock(shot.clock);
  return h < 5 || h >= 19.5 ? 'night' : h < 7.5 ? 'dawn' : h >= 17 ? 'dusk' : 'day';
};
const TINT: Record<string, [string, number]> = {dawn: ['#ffcfa0', 0.16], day: ['#ffffff', 0], dusk: ['#ff9f6a', 0.2], night: ['#6f80c8', 0.34], sepia: ['#d9b178', 0.34]};
const INDOOR_LIT = new Set(['studio', 'datacentre', 'drawer', 'stage']);

/** mouth openness for a speaking character: a syllable-like flutter that eases in and out of the line */
const talkAt = (t: number, sp: Speak[] | undefined, i: number) => {
  if (!sp) return 0;
  for (const x of sp) {
    if (x.a !== i || t < x.s || t > x.e) continue;
    const edge = Math.min(1, (t - x.s) / 0.08, (x.e - t) / 0.08);
    const f = Math.abs(Math.sin(t * 15.5)) * 0.7 + Math.abs(Math.sin(t * 6.1 + 1.3)) * 0.3;
    return Math.max(0, edge) * (0.15 + 0.85 * f);
  }
  return 0;
};

const Defs: React.FC = () => (
  <defs>
    <radialGradient id="phoneGlow" cx="50%" cy="70%" r="60%">
      <stop offset="0" stopColor="#8fd3ff" stopOpacity={0.55} />
      <stop offset="1" stopColor="#8fd3ff" stopOpacity={0} />
    </radialGradient>
    <radialGradient id="ep-vig" cx="50%" cy="48%" r="75%">
      <stop offset="0.6" stopColor="#000" stopOpacity={0} />
      <stop offset="1" stopColor="#000" stopOpacity={0.32} />
    </radialGradient>
    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="3.2" markerHeight="3.2" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#f2b84b" stroke="#2a2a2e" strokeWidth={1} />
    </marker>
  </defs>
);

const Actor: React.FC<{a: ActorSpec; t: number; p: number; i: number; base: number; chibi?: boolean; talk?: number}> = ({a, t, p, i, base, chibi, talk}) => {
  const switched = a.at !== undefined && p >= a.at;
  let pose = (switched && a.pose2) || a.pose;
  const expr = (switched && a.expr2) || a.expr;
  let x = a.x;
  let moving = false;
  let facing = a.face ?? 0;
  if (a.walk) {
    const end = a.pose2 && a.at !== undefined ? a.at : 1;
    const q = ease(Math.min(1, p / Math.max(0.05, end)));
    x = a.walk[0] + (a.walk[1] - a.walk[0]) * q;
    moving = q > 0 && q < 0.995 && !switched;
    if (a.face === undefined) facing = moving ? Math.sign(a.walk[1] - a.walk[0]) : 0;
    if (!moving && pose === 'walk') pose = 'stand';
  }
  const sit = pose.startsWith('sit');
  return (
    <g>
      {!sit && <ellipse cx={x} cy={(a.y ?? 1000) + 4} rx={46 * (a.s ?? 1) * base} ry={9 * (a.s ?? 1) * base} fill="#000" opacity={0.2} />}
    <Character
      look={CAST[a.who] ?? CAST.you}
      pose={pose}
      expression={expr}
      x={x}
      y={a.y ?? 1000}
      scale={(a.s ?? 1) * base}
      t={t}
      seed={i * 4 + 1}
      facing={facing}
      moving={moving}
      hold={a.hold ?? null}
      glow={a.glow}
      bare={a.nude}
      chibi={chibi}
      talk={talk}
    />
    </g>
  );
};

/** warm floating dust in painted rooms, like light catching particles */
const Dust: React.FC<{t: number}> = ({t}) => (
  <g style={{mixBlendMode: 'screen'}}>
    {Array.from({length: 22}, (_, i) => {
      const sx = (i * 397) % 1920;
      const sy = (i * 211) % 900;
      const x = (sx + t * (8 + (i % 5) * 3) + 40 * Math.sin(t * 0.4 + i)) % 1960;
      const y = sy + 30 * Math.sin(t * 0.3 + i * 1.7) - ((t * (4 + (i % 3))) % 200);
      const r = 1.6 + (i % 4) * 0.9;
      return <circle key={i} cx={x} cy={y} r={r} fill="#ffe2a8" opacity={0.18 + 0.22 * Math.abs(Math.sin(t * 0.8 + i))} />;
    })}
  </g>
);

/** word-by-word captions: a short group of words with the spoken one highlighted */
const Captions: React.FC<{words: Word[]}> = ({words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  let k = -1;
  for (let i = 0; i < words.length; i++) {
    if (words[i].s <= t + 0.02) k = i;
    else break;
  }
  if (k < 0) return null;
  if (t > words[k].e + 0.6) return null;
  // group of up to 4 words, broken after punctuation
  let a = k;
  while (a > 0 && k - a < 3 && !/[.?!,:;]$/.test(words[a - 1].w) && words[a].s - words[a - 1].e < 0.5) a--;
  let b = k;
  while (b < words.length - 1 && b - a < 3 && !/[.?!,:;]$/.test(words[b].w) && words[b + 1].s - words[b].e < 0.5) b++;
  const grp = words.slice(a, b + 1);
  const size = 64;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 70, pointerEvents: 'none'}}>
      <div style={{display: 'flex', gap: 30, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 1500}}>
        {grp.map((w, j) => {
          const on = a + j === k;
          return (
            <span
              key={j}
              style={{
                fontFamily: 'Inter',
                fontWeight: 900,
                fontSize: size,
                color: on ? '#ffd54a' : '#ffffff',
                WebkitTextStroke: '12px #141414',
                paintOrder: 'stroke fill',
                textShadow: '0 6px 0 rgba(0,0,0,0.35)',
                display: 'inline-block',
                transform: on ? 'scale(1.06)' : 'none',
                letterSpacing: -0.5,
                textTransform: 'uppercase',
              }}
            >
              {w.w.replace(/[,;:]$/, '')}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const actorPos = (a: ActorSpec, p: number) => {
  if (!a.walk) return a.x;
  const end = a.pose2 && a.at !== undefined ? a.at : 1;
  return a.walk[0] + (a.walk[1] - a.walk[0]) * ease(Math.min(1, p / Math.max(0.05, end)));
};

export const ShotView: React.FC<{shot: Shot; dur: number; prevDay: number | null; badge?: boolean; prevClock?: string | null; first?: boolean}> = ({shot, dur, prevDay, badge = true, prevClock = null, first = false}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const p = Math.min(1, frame / Math.max(1, dur - 1));
  const img = shot.set.startsWith('img:') ? shot.set.slice(4) : null;
  const Set = SETS[shot.set] ?? SETS.studio;
  const second = !!shot.cam2 && shot.cut !== undefined && p >= shot.cut;
  const cut = shot.cut ?? 1;
  const cam = second ? (shot.cam2 as number[]) : shot.cam ?? [1, 1];
  const cp = second ? (p - cut) / Math.max(0.01, 1 - cut) : shot.cam2 ? p / Math.max(0.01, cut) : p;
  const tr = shot.tr ?? (first ? 'cut' : 'punch');
  const since = second ? frame - Math.round(cut * (dur - 1)) : frame;
  const kick = (tr === 'cut' || tr === 'fade') && !second ? 0 : Math.pow(1 - Math.min(1, since / 8), 2);
  const z = (cam[0] + (cam[1] - cam[0]) * ease(Math.min(1, Math.max(0, cp)))) * (1 + 0.045 * kick);
  const tod = todOf(shot);
  const [tintC, tintA] = INDOOR_LIT.has(shot.set) || (img && !shot.tod) ? TINT.day : TINT[tod];
  const shaking = shot.shake && p >= shot.shake[0] && p <= shot.shake[1];
  const sx = shaking ? Math.sin(frame * 2.3) * 9 : 0;
  const sy = shaking ? Math.cos(frame * 3.1) * 7 : 0;
  const wipe = tr === 'wipe' ? Math.min(1, frame / 11) : 1;
  const fx = cam[2] ?? 960;
  const fy = cam[3] ?? 600;
  const opt = {tod, ...(shot.setopt ?? {})};
  const props = shot.props ?? [];
  const behind = props.filter((pr) => !pr.front);
  const front = props.filter((pr) => pr.front);
  const actors = [...(shot.actors ?? [])];
  const lead = actors[0];
  const follow = lead ? {x: actorPos(lead, p), y: (lead.y ?? 1000) - 560} : undefined;
  return (
    <AbsoluteFill>
      <svg viewBox="0 0 1920 1080" width="100%" height="100%">
        <Defs />
        <g transform={`translate(${fx + sx} ${fy + sy}) scale(${z}) translate(${-fx} ${-fy})`}>
          {img ? <image href={staticFile(`bg/${img}.jpg`)} x={-64} y={-36} width={2048} height={1152} preserveAspectRatio="xMidYMid slice" /> : <Set opt={opt} t={t} p={p} layer="bg" />}
          {behind.map((pr, i) => (
            <PropView key={`b${i}`} spec={pr} t={t} p={p} fps={fps} />
          ))}
          <g style={img ? {filter: 'sepia(0.14) saturate(1.08) brightness(0.98)'} : undefined}>
            {actors.map((a, i) => (
              <Actor key={i} a={a} t={t} p={p} i={i} base={scaleFor(shot.set)} chibi={shot.chibi} talk={talkAt(t, shot.speak, i)} />
            ))}
          </g>
          {front.map((pr, i) => (
            <PropView key={`f${i}`} spec={pr} t={t} p={p} fps={fps} />
          ))}
          {!img && <Set opt={opt} t={t} p={p} layer="fg" />}
          {tintA > 0 && <rect x={-200} y={-200} width={2320} height={1480} fill={tintC} opacity={tintA} style={{mixBlendMode: 'multiply'}} />}
          {(shot.fx ?? []).map((f, i) => (
            <FxView key={i} spec={f} t={t} p={p} dur={dur / fps} follow={f.follow ? follow : undefined} />
          ))}
        </g>
        {shot.ov && <OverlayView spec={shot.ov} t={t} p={p} dur={dur / fps} />}
        {badge && shot.day !== undefined && shot.day !== null && <DayBadge day={shot.day} prev={prevDay} t={t} />}
        {badge && shot.clock ? <TimeBadge clock={shot.clock} prev={prevClock} t={t} /> : null}
        {badge && shot.where ? <PlaceTag text={shot.where} t={t} low={!!shot.clock} /> : null}
        {img && <Dust t={t} />}
        <rect width={1920} height={1080} fill="url(#ep-vig)" />
        {tr === 'fade' && frame < 14 && <rect width={1920} height={1080} fill="#0b0b10" opacity={1 - frame / 14} />}
        {wipe < 1 && (
          <g transform={`translate(${wipe * 2700} 0)`}>
            <path d="M -700 0 L 1920 0 L 2200 1080 L -700 1080 Z" fill="#0b1b33" />
            <path d="M 1920 0 L 2060 0 L 2340 1080 L 2200 1080 Z" fill="#f2b84b" />
            <path d="M -840 0 L -700 0 L -420 1080 L -560 1080 Z" fill="#f2b84b" transform="translate(-0 0)" />
          </g>
        )}
      </svg>
    </AbsoluteFill>
  );
};

export const Episode: React.FC<EpisodeProps> = ({shots, timing, words}) => {
  const {fps, durationInFrames} = useVideoConfig();
  ensureFonts();
  let prevDay: number | null = null;
  let prevClock: string | null = null;
  return (
    <AbsoluteFill style={{backgroundColor: '#0b1b33', fontFamily: 'Inter'}}>
      {shots.map((shot, i) => {
        const span = timing.scenes[i];
        if (!span) return null;
        const from = Math.round((span.start_ms / 1000) * fps);
        const end = i === shots.length - 1 ? durationInFrames : Math.round((span.end_ms / 1000) * fps);
        const dur = Math.max(1, end - from);
        const pd = prevDay;
        if (shot.day !== undefined && shot.day !== null) prevDay = shot.day;
        const pc = prevClock;
        if (shot.clock) prevClock = shot.clock;
        return (
          <Sequence key={shot.id} from={from} durationInFrames={dur} layout="none">
            <ShotView shot={shot} dur={dur} prevDay={pd} prevClock={pc} first={i === 0} />
          </Sequence>
        );
      })}
      {words && words.length > 0 && <Captions words={words} />}
    </AbsoluteFill>
  );
};

export const sampleEpisode: EpisodeProps = {
  shots: [
    {id: 'a', n: '', set: 'studio', actors: [{who: 'you', pose: 'phone', expr: 'shocked', x: 560, y: 1000, hold: 'phone', glow: true}], ov: {t: 'title', title: '30 DAYS', sub: 'no phone', pos: 'right'}},
    {id: 'b', n: '', set: 'street', day: 4, actors: [{who: 'you', pose: 'walk', expr: 'happy', x: 300, y: 1000, walk: [300, 1200]}]},
  ],
  timing: {total_sec: 6, scenes: [{id: 'a', start_ms: 0, end_ms: 3000}, {id: 'b', start_ms: 3000, end_ms: 6000}]},
};
