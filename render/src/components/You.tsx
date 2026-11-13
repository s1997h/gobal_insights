import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Mood} from '../types';

const SKIN = '#F2C7A1';
const SKIN_SHADE = '#D9A67E';
const HAIR = '#1B2540';
const INK = '#0B1B33';
const HOODIE = '#2EC4B6';
const HOODIE_DARK = '#1F9A8E';
const MOUTH = '#7A2E3A';

const BROWS: Record<Mood, [string, string]> = {
  neutral: ['M134 205 Q160 196 186 204', 'M214 204 Q240 196 266 205'],
  shocked: ['M134 186 Q160 172 186 184', 'M214 184 Q240 172 266 186'],
  happy: ['M134 198 Q160 186 186 196', 'M214 196 Q240 186 266 198'],
  worried: ['M134 212 L186 190', 'M214 190 L266 212'],
};

/** The YOU character: a flat-vector narrator stand-in with four expressions. Replace with your own art freely. */
export const You: React.FC<{mood: Mood; height: number}> = ({mood, height}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pop = spring({frame, fps, config: {damping: 11, stiffness: 120}});
  const breathe = Math.sin(frame / 14) * 5;
  const blinkPhase = frame % 100;
  const blink = (mood === 'neutral' || mood === 'worried') && blinkPhase < 4 ? 0.12 : 1;
  const width = (height * 400) / 520;
  const eyeRx = mood === 'shocked' ? 26 : 22;
  const eyeRy = mood === 'shocked' ? 33 : 26;
  const pupil = mood === 'shocked' ? 6 : mood === 'worried' ? 8 : 9;

  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 400 520"
      style={{transform: `translateY(${breathe}px) scale(${0.82 + 0.18 * pop})`, transformOrigin: '50% 100%', overflow: 'visible'}}
    >
      {/* body */}
      <path d="M50 520 C50 405 110 362 200 362 C290 362 350 405 350 520 Z" fill={HOODIE} />
      <path d="M135 372 Q200 412 265 372 L265 394 Q200 434 135 394 Z" fill={HOODIE_DARK} />
      <rect x="176" y="326" width="48" height="54" rx="14" fill={SKIN_SHADE} />
      <text x="200" y="488" textAnchor="middle" fontFamily="inherit" fontWeight={800} fontSize="40" fill="#F4F6FA" opacity="0.9">
        YOU
      </text>
      {/* head */}
      <circle cx="100" cy="246" r="19" fill={SKIN_SHADE} />
      <circle cx="300" cy="246" r="19" fill={SKIN_SHADE} />
      <ellipse cx="200" cy="236" rx="100" ry="108" fill={SKIN} />
      <path d="M98 220 C92 120 150 92 200 92 C256 92 308 122 302 220 C288 172 250 150 200 150 C150 150 112 172 98 220 Z" fill={HAIR} />
      <path d="M150 112 C170 70 215 66 246 96 C222 92 190 96 150 112 Z" fill={HAIR} />
      {mood === 'happy' && (
        <>
          <circle cx="132" cy="282" r="16" fill="#F08A7E" opacity="0.45" />
          <circle cx="268" cy="282" r="16" fill="#F08A7E" opacity="0.45" />
        </>
      )}
      {/* eyes */}
      {mood === 'happy' ? (
        <>
          <path d="M138 246 Q160 220 182 246" stroke={INK} strokeWidth="9" strokeLinecap="round" fill="none" />
          <path d="M218 246 Q240 220 262 246" stroke={INK} strokeWidth="9" strokeLinecap="round" fill="none" />
        </>
      ) : (
        <>
          <g transform={`translate(160 242) scale(1 ${blink})`}>
            <ellipse rx={eyeRx} ry={eyeRy} fill="#fff" />
            <circle cx="0" cy="2" r={pupil} fill={INK} />
          </g>
          <g transform={`translate(240 242) scale(1 ${blink})`}>
            <ellipse rx={eyeRx} ry={eyeRy} fill="#fff" />
            <circle cx="0" cy="2" r={pupil} fill={INK} />
          </g>
        </>
      )}
      {/* brows */}
      <path d={BROWS[mood][0]} stroke={HAIR} strokeWidth="10" strokeLinecap="round" fill="none" />
      <path d={BROWS[mood][1]} stroke={HAIR} strokeWidth="10" strokeLinecap="round" fill="none" />
      {/* nose */}
      <path d="M200 252 Q191 280 205 283" stroke={SKIN_SHADE} strokeWidth="6" strokeLinecap="round" fill="none" />
      {/* mouth */}
      {mood === 'neutral' && <path d="M172 306 Q200 314 228 306" stroke={MOUTH} strokeWidth="8" strokeLinecap="round" fill="none" />}
      {mood === 'shocked' && <ellipse cx="200" cy="318" rx="22" ry="30" fill={MOUTH} />}
      {mood === 'happy' && (
        <>
          <path d="M158 296 Q200 350 242 296 Z" fill={MOUTH} />
          <path d="M172 298 Q200 308 228 298 L226 304 Q200 313 174 304 Z" fill="#fff" />
        </>
      )}
      {mood === 'worried' && (
        <>
          <path d="M170 320 Q200 298 230 320" stroke={MOUTH} strokeWidth="8" strokeLinecap="round" fill="none" />
          <path d="M312 176 C300 198 296 212 312 214 C328 212 324 198 312 176 Z" fill="#8EDCF5" />
        </>
      )}
    </svg>
  );
};
