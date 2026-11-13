import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene, Style} from '../types';
import {fontFamily, rgba, useLayout} from '../theme';

/** 2 to 5 labelled boxes joined by arrows. They appear one after another. */
export const Diagram: React.FC<{scene: Scene; style: Style; dur: number}> = ({scene, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {portrait, u, w, h} = useLayout();
  const nodes: string[] = (scene.visual.props?.nodes ?? []).slice(0, 5);
  const n = Math.max(1, nodes.length);
  const gap = (portrait ? 46 : 70) * u;

  // box geometry
  let boxW: number;
  let boxH: number;
  let x0: number;
  let y0: number;
  if (portrait) {
    const avail = h * 0.36;
    boxH = Math.min(120 * u, (avail - (n - 1) * gap) / n);
    boxW = w * 0.78;
    x0 = (w - boxW) / 2;
    y0 = h * 0.25 + (avail - (n * boxH + (n - 1) * gap)) / 2;
  } else {
    boxW = Math.min(360 * u, (w * 0.86 - (n - 1) * gap) / n);
    boxH = 170 * u;
    x0 = (w - (n * boxW + (n - 1) * gap)) / 2;
    y0 = h * 0.4 - boxH / 2;
  }
  const prog = (i: number) => spring({frame: frame - (8 + i * 14), fps, config: {damping: 15, stiffness: 130}});

  return (
    <AbsoluteFill style={{fontFamily: fontFamily(style)}}>
      {nodes.map((label, i) => {
        const p = prog(i);
        const left = portrait ? x0 : x0 + i * (boxW + gap);
        const top = portrait ? y0 + i * (boxH + gap) : y0;
        const arrowP = i < n - 1 ? prog(i + 1) : 0;
        return (
          <React.Fragment key={i}>
            <div
              style={{
                position: 'absolute',
                left,
                top,
                width: boxW,
                height: boxH,
                borderRadius: 24 * u,
                background: rgba(style.palette.bg, 0.8),
                border: `${4 * u}px solid ${i === n - 1 ? style.palette.gold : style.palette.teal}`,
                color: style.palette.ink,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                textAlign: 'center',
                padding: 14 * u,
                fontSize: (portrait ? 40 : 38) * u,
                fontWeight: 700,
                transform: `scale(${0.7 + 0.3 * p})`,
                opacity: Math.min(1, p),
              }}
            >
              {label}
            </div>
            {i < n - 1 && (
              <svg
                style={{
                  position: 'absolute',
                  left: portrait ? left + boxW / 2 - 24 * u : left + boxW + 8 * u,
                  top: portrait ? top + boxH + 4 * u : top + boxH / 2 - 24 * u,
                  opacity: Math.min(1, arrowP),
                }}
                width={portrait ? 48 * u : gap - 16 * u}
                height={portrait ? gap - 8 * u : 48 * u}
                viewBox={portrait ? '0 0 48 40' : '0 0 54 48'}
                preserveAspectRatio="none"
              >
                {portrait ? (
                  <path d="M24 2 L24 30 M10 20 L24 36 L38 20" stroke={style.palette.gold} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                ) : (
                  <path d="M2 24 L44 24 M32 10 L48 24 L32 38" stroke={style.palette.gold} strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" fill="none" />
                )}
              </svg>
            )}
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};
