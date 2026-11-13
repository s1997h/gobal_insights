import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Background} from './components/Background';
import {You} from './components/You';
import {ensureFonts, fontFamily, rgba} from './theme';
import type {ThumbProps} from './types';

/** 1280x720 YouTube thumbnail: big short text on the left, the YOU character on the right. */
export const Thumbnail: React.FC<ThumbProps> = ({text, mood, style}) => {
  ensureFonts(style);
  const words = text.trim().split(/\s+/).filter(Boolean);
  // at most 3 lines: split words as evenly as possible
  const lines: string[] = [];
  const per = Math.ceil(words.length / Math.min(3, Math.max(1, words.length)));
  for (let i = 0; i < words.length; i += per) lines.push(words.slice(i, i + per).join(' '));
  const longest = Math.max(...lines.map((l) => l.length), 1);
  const size = Math.min(150, 640 / (longest * 0.6));
  return (
    <AbsoluteFill style={{fontFamily: fontFamily(style), backgroundColor: style.palette.bg}}>
      <Background style={style} />
      <div
        style={{
          position: 'absolute',
          right: 40,
          bottom: 0,
          width: 520,
          height: 640,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${rgba(style.palette.teal, 0.45)} 0%, ${rgba(style.palette.teal, 0)} 70%)`,
        }}
      />
      <div style={{position: 'absolute', right: 80, bottom: -20}}>
        <You mood={mood} height={580} />
      </div>
      <div
        style={{
          position: 'absolute',
          left: 56,
          top: 0,
          bottom: 0,
          width: 700,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
        }}
      >
        {lines.map((l, i) => (
          <div
            key={i}
            style={{
              fontSize: size,
              fontWeight: 800,
              lineHeight: 1.0,
              textTransform: 'uppercase',
              color: i === lines.length - 1 ? style.palette.gold : style.palette.ink,
              WebkitTextStroke: `6px ${style.palette.bg}`,
              paintOrder: 'stroke fill',
              textShadow: '0 8px 24px rgba(0,0,0,0.45)',
            }}
          >
            {l}
          </div>
        ))}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 56,
          top: 36,
          fontSize: 26,
          letterSpacing: 6,
          textTransform: 'uppercase',
          color: style.palette.teal,
          fontWeight: 700,
        }}
      >
        {style.channel_name}
      </div>
    </AbsoluteFill>
  );
};
