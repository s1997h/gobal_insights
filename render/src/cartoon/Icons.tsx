import React from 'react';
import {INK} from './Character';

/** Small doodle icons, drawn in a 100 x 100 box centred on 0,0. */

const k = {stroke: INK, strokeWidth: 4, strokeLinejoin: 'round' as const, strokeLinecap: 'round' as const};

export type IconName =
  | 'alarm' | 'map' | 'music' | 'bank' | 'ticket' | 'tv_x' | 'friends' | 'run' | 'tree' | 'bulb' | 'star' | 'note'
  | 'question' | 'phone' | 'camera' | 'heart' | 'check' | 'cross' | 'bell';

export const Icon: React.FC<{name: IconName; size?: number}> = ({name, size = 100}) => {
  const s = size / 100;
  let body: React.ReactNode = null;
  switch (name) {
    case 'alarm':
      body = (
        <g>
          <circle cx={-26} cy={-30} r={12} fill="#f2b84b" {...k} />
          <circle cx={26} cy={-30} r={12} fill="#f2b84b" {...k} />
          <circle cx={0} cy={4} r={36} fill="#e9625a" {...k} />
          <circle cx={0} cy={4} r={27} fill="#fffaf0" {...k} />
          <path d="M 0 4 L 0 -14 M 0 4 L 13 12" {...k} fill="none" />
          <path d="M -22 36 L -30 46 M 22 36 L 30 46" {...k} />
        </g>
      );
      break;
    case 'map':
      body = (
        <g>
          <path d="M -42 -30 L -14 -40 L 14 -30 L 42 -40 L 42 34 L 14 44 L -14 34 L -42 44 Z" fill="#9fd6a8" {...k} />
          <path d="M -14 -40 L -14 34 M 14 -30 L 14 44" {...k} />
          <path d="M 4 -16 C 4 -30 26 -30 26 -16 C 26 -6 15 4 15 10 C 15 4 4 -6 4 -16 Z" fill="#e9625a" {...k} />
        </g>
      );
      break;
    case 'music':
      body = (
        <g>
          <path d="M -14 26 L -14 -30 L 32 -40 L 32 16" fill="none" {...k} />
          <ellipse cx={-26} cy={28} rx={14} ry={11} fill="#2ec4b6" {...k} />
          <ellipse cx={20} cy={18} rx={14} ry={11} fill="#2ec4b6" {...k} />
          <path d="M -14 -18 L 32 -28" {...k} />
        </g>
      );
      break;
    case 'bank':
      body = (
        <g>
          <rect x={-44} y={-28} width={88} height={58} rx={9} fill="#5b8def" {...k} />
          <rect x={-44} y={-16} width={88} height={12} fill={INK} />
          <rect x={-34} y={10} width={26} height={8} rx={2} fill="#f2b84b" />
        </g>
      );
      break;
    case 'ticket':
      body = (
        <g>
          <path d="M -44 -26 L 44 -26 L 44 -8 Q 34 0 44 8 L 44 26 L -44 26 L -44 8 Q -34 0 -44 -8 Z" fill="#f2b84b" {...k} />
          <path d="M 18 -26 L 18 26" stroke={INK} strokeWidth={3} strokeDasharray="5 5" />
          <path d="M -30 -6 L 0 -6 M -30 8 L -8 8" {...k} />
        </g>
      );
      break;
    case 'tv_x':
      body = (
        <g>
          <rect x={-44} y={-32} width={88} height={60} rx={8} fill="#5d6b84" {...k} />
          <rect x={-35} y={-24} width={70} height={44} rx={4} fill="#9fd3f0" {...k} />
          <path d="M -14 28 L -22 42 M 14 28 L 22 42" {...k} />
          <path d="M -40 -38 L 40 38 M 40 -38 L -40 38" stroke="#e9625a" strokeWidth={10} strokeLinecap="round" />
        </g>
      );
      break;
    case 'friends':
      body = (
        <g>
          <circle cx={-20} cy={-14} r={16} fill="#f2e8dc" {...k} />
          <circle cx={20} cy={-14} r={16} fill="#f2e8dc" {...k} />
          <path d="M -44 40 Q -44 6 -20 6 Q 4 6 4 40 Z" fill="#2ec4b6" {...k} />
          <path d="M -4 40 Q -4 6 20 6 Q 44 6 44 40 Z" fill="#f2b84b" {...k} />
        </g>
      );
      break;
    case 'run':
      body = (
        <g>
          <circle cx={10} cy={-34} r={11} fill="#f2e8dc" {...k} />
          <path d="M 4 -20 L -6 8 L 14 22 L 10 44 M -6 8 L -26 26 M 2 -14 L 24 -4 L 34 -16 M 2 -14 L -18 -8 L -28 -22" fill="none" stroke={INK} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      );
      break;
    case 'tree':
      body = (
        <g>
          <rect x={-7} y={6} width={14} height={38} fill="#8b5a3c" {...k} />
          <circle cx={0} cy={-14} r={34} fill="#5fae5a" {...k} />
          <circle cx={-14} cy={-22} r={8} fill="#7cc576" />
        </g>
      );
      break;
    case 'bulb':
      body = (
        <g>
          <path d="M 0 -44 C 26 -44 34 -20 26 -4 C 20 8 14 12 14 24 L -14 24 C -14 12 -20 8 -26 -4 C -34 -20 -26 -44 0 -44 Z" fill="#ffe27a" {...k} />
          <rect x={-14} y={24} width={28} height={14} rx={3} fill="#b9bec7" {...k} />
          <path d="M -8 6 L 0 -8 L 8 6" fill="none" {...k} />
        </g>
      );
      break;
    case 'star':
      body = <path d="M 0 -42 L 12 -12 L 42 -10 L 18 10 L 26 40 L 0 22 L -26 40 L -18 10 L -42 -10 L -12 -12 Z" fill="#f2b84b" {...k} />;
      break;
    case 'note':
      body = (
        <g>
          <rect x={-32} y={-40} width={64} height={80} rx={6} fill="#fffaf0" {...k} />
          <path d="M -20 -22 L 20 -22 M -20 -6 L 20 -6 M -20 10 L 8 10" {...k} />
        </g>
      );
      break;
    case 'question':
      body = (
        <g>
          <path d="M -18 -18 C -18 -44 22 -44 22 -18 C 22 -2 2 0 2 16" fill="none" stroke={INK} strokeWidth={12} strokeLinecap="round" />
          <circle cx={2} cy={36} r={7} fill={INK} />
        </g>
      );
      break;
    case 'phone':
      body = (
        <g>
          <rect x={-24} y={-44} width={48} height={88} rx={9} fill="#30343c" {...k} />
          <rect x={-18} y={-34} width={36} height={66} rx={3} fill="#9fd3f0" />
        </g>
      );
      break;
    case 'camera':
      body = (
        <g>
          <rect x={-42} y={-24} width={84} height={56} rx={8} fill="#5d6b84" {...k} />
          <rect x={-16} y={-36} width={32} height={14} rx={3} fill="#5d6b84" {...k} />
          <circle cx={0} cy={4} r={18} fill="#9fd3f0" {...k} />
        </g>
      );
      break;
    case 'heart':
      body = <path d="M 0 36 C -46 6 -40 -38 -12 -34 C -4 -33 0 -26 0 -20 C 0 -26 4 -33 12 -34 C 40 -38 46 6 0 36 Z" fill="#e9625a" {...k} />;
      break;
    case 'check':
      body = (
        <g>
          <circle cx={0} cy={0} r={40} fill="#2ec4b6" {...k} />
          <path d="M -18 0 L -4 14 L 20 -14" fill="none" stroke="#fff" strokeWidth={10} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      );
      break;
    case 'cross':
      body = (
        <g>
          <circle cx={0} cy={0} r={40} fill="#e9625a" {...k} />
          <path d="M -15 -15 L 15 15 M 15 -15 L -15 15" stroke="#fff" strokeWidth={10} strokeLinecap="round" />
        </g>
      );
      break;
    case 'bell':
      body = (
        <g>
          <path d="M -30 22 C -26 14 -24 6 -24 -8 C -24 -28 -12 -38 0 -38 C 12 -38 24 -28 24 -8 C 24 6 26 14 30 22 Z" fill="#f2b84b" {...k} />
          <circle cx={0} cy={30} r={7} fill="#f2b84b" {...k} />
        </g>
      );
      break;
  }
  return <g transform={`scale(${s})`}>{body}</g>;
};
