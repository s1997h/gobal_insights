export const FPS = 30;

export type Mood = 'neutral' | 'shocked' | 'happy' | 'worried';

export type Visual = {
  type: 'template' | 'still' | 'hero_clip';
  template?: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  props?: Record<string, any>;
  prompt?: string | null;
  max_sec?: number | null;
};

export type Scene = {
  id: string;
  narration: string;
  visual: Visual;
  on_screen_text?: string | null;
  min_sec: number;
  chapter?: string | null;
};

export type Word = {word: string; start_ms: number; end_ms: number; scene_id?: string | null};
export type SceneSpan = {id: string; start_ms: number; end_ms: number};

export type Style = {
  palette: {bg: string; gold: string; teal: string; ink: string};
  font: string;
  fonts: {file: string; weight: string}[];
  captions: {max_words_per_line: number; highlight: string; position: 'lower_third' | 'center'};
  channel_name: string;
};

export type VideoProps = {
  run_id: string;
  format: 'long' | 'short';
  scenes: Scene[];
  timing: {total_sec: number; scenes: SceneSpan[]};
  words: Word[];
  images: Record<string, string>;
  style: Style;
};

export type ThumbProps = {text: string; mood: Mood; style: Style};
