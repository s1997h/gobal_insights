import React from 'react';
import {AbsoluteFill, CalculateMetadataFunction, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/fonts';
import {ShotView, type Shot} from './Episode';

/**
 * A vertical Short (1080 x 1920) cut from an episode: a hook title on top, the 16:9 scene in the
 * middle, big word-by-word captions under it, and the bottom 20% left clear for the app's buttons.
 */

export type CapToken = {text: string; start_ms: number; end_ms: number; num?: boolean};

export type ShortProps = {
  shots: (Shot & {vx?: number})[];
  timing: {total_sec: number; scenes: {id: string; start_ms: number; end_ms: number}[]};
  words: {word: string; start_ms: number; end_ms: number}[];
  caps?: CapToken[]; // words with numbers already turned into numerals (shorts/caps.py)
  title: string[]; // 1-3 lines
  highlight?: string[]; // words drawn in gold
  brand?: string;
};

let loaded = false;
const fonts = () => {
  if (loaded) return;
  loaded = true;
  for (const [f, w] of [
    ['fonts/Inter-Bold.otf', '700'],
    ['fonts/Inter-ExtraBold.otf', '800'],
    ['fonts/Inter-ExtraBold.otf', '900'],
  ]) {
    loadFont({family: 'Inter', url: staticFile(f), weight: w}).catch(() => undefined);
  }
};

export const calcShort: CalculateMetadataFunction<ShortProps> = ({props}) => ({
  durationInFrames: Math.max(30, Math.ceil(props.timing.total_sec * 30)),
});

const INK = '#2a2a2e';
const GOLD = '#f2b84b';
const CREAM = '#fffaf0';
// Text stays inside the Reels safe zone Meta publishes: clear of the top 14% (270 px), the bottom 35%
// (y > 1248) and the right-hand button column. The same box is safe for YouTube Shorts.
const SAFE_BOTTOM = 1244;
const TITLE_TOP = 288; // also inside the 4:5 feed crop (285-1635) and the 3:4 grid crop (240-1680)
const CAP_TOP = 1134; // captions get their own band: never over the scene, never under the app's caption
const CAP_LEFT = 120;
const CAP_RIGHT = 120; // keeps text left of the like / comment / share column

/** Stacked layout: title, then the scene as large as the space allows (at least full 16:9 width). */
const layoutFor = (lines: number) => {
  const titleSize = lines >= 3 ? 70 : 78;
  const titleH = Math.round(lines * titleSize * 1.02);
  const sceneTop = TITLE_TOP + titleH + 14;
  const scale = Math.max(1080 / 1920, (CAP_TOP - 10 - sceneTop) / 1080);
  return {titleSize, sceneTop, scale, sceneH: Math.round(1080 * scale)};
};

/** Left offset that centres scene-x `vx` in the 1080-wide window, kept inside the 1920 scene. */
const leftFor = (scale: number, vx = 960) => {
  const half = 540 / scale;
  const c = Math.min(1920 - half, Math.max(half, vx));
  return Math.round(540 - c * scale);
};

type ShortShot = Shot & {vx?: number};

type Chunk = {words: CapToken[]; start: number; end: number};

const chunkWords = (words: CapToken[]): Chunk[] => {
  const out: Chunk[] = [];
  let cur: CapToken[] = [];
  for (const w of words) {
    cur.push(w);
    const text = cur.map((x) => x.text).join(' ');
    const stop = /[.?!,;:]$/.test(w.text);
    if (stop || cur.length >= 3 || text.length >= 12) {
      out.push({words: cur, start: cur[0].start_ms, end: cur[cur.length - 1].end_ms});
      cur = [];
    }
  }
  if (cur.length) out.push({words: cur, start: cur[0].start_ms, end: cur[cur.length - 1].end_ms});
  return out;
};

const clean = (t: string) => t.replace(/[.,;:"]+$/g, '').replace(/^"/, '');

const Captions: React.FC<{words: CapToken[]}> = ({words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const ms = (frame / fps) * 1000;
  const chunks = React.useMemo(() => chunkWords(words), [words]);
  let idx = -1;
  for (let i = 0; i < chunks.length; i++) {
    const next = chunks[i + 1];
    if (ms >= chunks[i].start - 60 && (!next || ms < next.start - 60) && ms <= chunks[i].end + 700) idx = i;
  }
  if (idx < 0) return null;
  const c = chunks[idx];
  const age = (ms - c.start) / 1000;
  const pop = age < 0.1 ? 0.8 + (age / 0.1) * 0.28 : age < 0.18 ? 1.08 - ((age - 0.1) / 0.08) * 0.08 : 1;
  // Inter Black caps run ~0.74 em per character, plus the stroke and the gap between words
  const em = c.words.reduce((n, w) => n + clean(w.text).length * 0.74 * (w.num ? 1.2 : 1) + 0.2, 0) + (c.words.length - 1) * 0.5;
  const size = Math.min(94, Math.floor((1080 - CAP_LEFT - CAP_RIGHT - 30) / (em * 1.08)));
  return (
    <div
      style={{
        position: 'absolute',
        top: CAP_TOP,
        height: SAFE_BOTTOM - CAP_TOP,
        left: CAP_LEFT,
        right: CAP_RIGHT,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: `0 ${Math.round(size * 0.5)}px`,
        whiteSpace: 'nowrap',
        transform: `scale(${pop})`,
        transformOrigin: '50% 50%',
      }}
    >
      {c.words.map((w, i) => {
        const on = ms >= w.start_ms - 40 && ms < (c.words[i + 1]?.start_ms ?? c.end + 700);
        const gold = on || w.num;
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              fontFamily: 'Inter',
              fontWeight: 900,
              fontSize: Math.round(size * (w.num ? 1.2 : 1)),
              lineHeight: 1,
              color: gold ? GOLD : '#ffffff',
              WebkitTextStroke: `${Math.round(size * 0.17)}px ${INK}`,
              paintOrder: 'stroke fill',
              textTransform: 'uppercase',
              letterSpacing: -1,
              transform: on ? 'scale(1.08)' : 'none',
              filter: 'drop-shadow(0 6px 0 rgba(0,0,0,0.35))',
            }}
          >
            {clean(w.text)}
          </span>
        );
      })}
    </div>
  );
};

/** One shot inside the vertical frame, with a short punch-in when it starts (a cut every few seconds keeps eyes on it). */
const ShotFrame: React.FC<{shot: ShortShot; dur: number; prevDay: number | null; punch: boolean; scale: number}> = ({shot, dur, prevDay, punch, scale}) => {
  const f = useCurrentFrame();
  const k = Math.min(1, f / 9);
  const p = punch ? 1 + 0.07 * (1 - k) * (1 - k) : 1;
  return (
    <div style={{position: 'absolute', inset: 0, transform: `scale(${p})`, transformOrigin: '50% 55%'}}>
      <div style={{position: 'absolute', top: 0, left: leftFor(scale, shot.vx), width: 1920, height: 1080, transform: `scale(${scale})`, transformOrigin: 'top left'}}>
        <ShotView shot={shot} dur={dur} prevDay={prevDay} badge={false} />
      </div>
    </div>
  );
};

export const EpisodeShort: React.FC<ShortProps> = ({shots, timing, words, caps, title, highlight = [], brand = 'THE IF LAB'}) => {
  fonts();
  const {fps, durationInFrames} = useVideoConfig();
  const frame = useCurrentFrame();
  const hi = new Set(highlight.map((h) => h.toLowerCase()));
  const ms = (frame / fps) * 1000;
  const cur = timing.scenes.findIndex((sc) => ms >= sc.start_ms && ms < sc.end_ms);
  const day = shots[cur < 0 ? shots.length - 1 : cur]?.day;
  const clock = shots[cur < 0 ? shots.length - 1 : cur]?.clock;
  const tokens: CapToken[] = caps ?? words.map((w) => ({text: w.word, start_ms: w.start_ms, end_ms: w.end_ms}));
  const tp = frame < 6 ? 0.9 + (frame / 6) * 0.1 : 1; // the hook title is readable from frame 0 (it is also the cover)
  const {titleSize, sceneTop, scale, sceneH} = layoutFor(title.length);
  let prevDay: number | null = null;
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 40%, #1b3a66 0%, #0b1b33 70%)', fontFamily: 'Inter'}}>
      <AbsoluteFill style={{backgroundImage: 'radial-gradient(rgba(255,255,255,0.07) 2.4px, transparent 2.6px)', backgroundSize: '56px 56px'}} />
      {/* hook title */}
      <div style={{position: 'absolute', top: TITLE_TOP, left: 70, right: 70, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, transform: `scale(${tp})`, transformOrigin: '50% 0%'}}>
        {title.map((line, i) => (
          <div key={i} style={{textAlign: 'center', fontWeight: 900, fontSize: titleSize, lineHeight: 1.02, letterSpacing: -2}}>
            {line.split(' ').map((w, j) => (
              <span key={j} style={{color: hi.has(w.toLowerCase().replace(/[^a-z0-9%]/g, '')) ? GOLD : CREAM, WebkitTextStroke: `16px ${INK}`, paintOrder: 'stroke fill'}}>
                {w}{' '}
              </span>
            ))}
          </div>
        ))}
      </div>
      {/* the scene */}
      <div style={{position: 'absolute', top: sceneTop - 6, left: -6, width: 1092, height: sceneH + 12, background: INK}} />
      <div style={{position: 'absolute', top: sceneTop, left: 0, width: 1080, height: sceneH, overflow: 'hidden'}}>
        {shots.map((shot: ShortShot, i) => {
          const span = timing.scenes[i];
          if (!span) return null;
          const from = Math.round((span.start_ms / 1000) * fps);
          const end = i === shots.length - 1 ? durationInFrames : Math.round((span.end_ms / 1000) * fps);
          const pd = prevDay;
          if (shot.day !== undefined && shot.day !== null) prevDay = shot.day;
          return (
            <Sequence key={shot.id + i} from={from} durationInFrames={Math.max(1, end - from)} layout="none">
              <ShotFrame shot={shot} dur={Math.max(1, end - from)} prevDay={pd} punch={i > 0} scale={scale} />
            </Sequence>
          );
        })}
        <div style={{position: 'absolute', top: 18, left: 72, display: 'flex', gap: 12}}>
          <div style={{background: CREAM, border: `4px solid ${INK}`, borderRadius: 30, padding: '4px 18px', fontWeight: 900, fontSize: 24, letterSpacing: 3, color: INK}}>{brand}</div>
          {day !== undefined && day !== null && (
            <div style={{background: GOLD, border: `4px solid ${INK}`, borderRadius: 30, padding: '4px 18px', fontWeight: 900, fontSize: 24, letterSpacing: 2, color: INK}}>DAY {day}</div>
          )}
          {clock ? (
            <div style={{background: GOLD, border: `4px solid ${INK}`, borderRadius: 30, padding: '4px 18px', fontWeight: 900, fontSize: 24, letterSpacing: 1, color: INK}}>{clock}</div>
          ) : null}
        </div>
      </div>
      <Captions words={tokens} />
    </AbsoluteFill>
  );
};

export const sampleShort: ShortProps = {
  shots: [{id: 'a', n: '', set: 'studio', actors: [{who: 'you', pose: 'phone', expr: 'shocked', x: 960, y: 1000, hold: 'phone', glow: true}]}],
  timing: {total_sec: 3, scenes: [{id: 'a', start_ms: 0, end_ms: 3000}]},
  words: [
    {word: 'Your', start_ms: 100, end_ms: 400},
    {word: 'phone', start_ms: 400, end_ms: 800},
    {word: 'buzzed.', start_ms: 800, end_ms: 1300},
  ],
  title: ['Why does your phone', 'buzz when it', "isn't there?"],
  highlight: ['buzz'],
};
