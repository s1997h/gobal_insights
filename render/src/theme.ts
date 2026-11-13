import {loadFont} from '@remotion/fonts';
import {staticFile, useVideoConfig} from 'remotion';
import type {Style} from './types';

const loaded = new Set<string>();

/** Load the style's font files from the run folder (Remotion's public dir). Safe to call every render. */
export const ensureFonts = (style: Style) => {
  for (const f of style.fonts ?? []) {
    const key = `${style.font}|${f.file}`;
    if (loaded.has(key)) continue;
    loaded.add(key);
    loadFont({family: style.font, url: staticFile(f.file), weight: f.weight}).catch((e) =>
      console.warn('font failed to load', f.file, e),
    );
  }
};

export const fontFamily = (style: Style) => `'${style.font}', 'Helvetica Neue', Arial, sans-serif`;

/** Layout numbers that adapt to 16:9 and 9:16. `u` scales sizes designed for 1920 wide (or 1080 wide in portrait). */
export const useLayout = () => {
  const {width, height} = useVideoConfig();
  const portrait = height > width;
  const u = portrait ? width / 1080 : width / 1920;
  return {
    w: width,
    h: height,
    portrait,
    u,
    // Keep text clear of the top and bottom 15% in portrait, where app interfaces overlay.
    safeTop: portrait ? height * 0.15 : height * 0.06,
    safeBottom: portrait ? height * 0.15 : height * 0.06,
  };
};

export const hexToRgb = (hex: string): [number, number, number] => {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
};

export const mix = (a: string, b: string, t: number) => {
  const [r1, g1, b1] = hexToRgb(a);
  const [r2, g2, b2] = hexToRgb(b);
  const c = (x: number, y: number) => Math.round(x + (y - x) * t);
  return `rgb(${c(r1, r2)}, ${c(g1, g2)}, ${c(b1, b2)})`;
};

export const rgba = (hex: string, a: number) => {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
};
