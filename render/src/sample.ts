import type {ThumbProps, VideoProps} from './types';

const style: VideoProps['style'] = {
  palette: {bg: '#0B1B33', gold: '#F2B84B', teal: '#2EC4B6', ink: '#F4F6FA'},
  font: 'Inter',
  fonts: [],
  captions: {max_words_per_line: 4, highlight: '#F2B84B', position: 'lower_third'},
  channel_name: 'What IF You...',
};

const narr = ['You open the email at seven oh two.', 'The number has too many zeros.', 'Your coffee goes cold.'];
export const sampleVideo = (format: 'long' | 'short'): VideoProps => ({
  run_id: 'sample',
  format,
  scenes: narr.map((n, i) => ({
    id: `s${i + 1}`,
    narration: n,
    visual: i === 0 ? {type: 'template', template: 'title_card', props: {title: 'What if you won the lottery?'}} : {type: 'template', template: 'you_reaction', props: {mood: 'shocked'}},
    min_sec: 3,
  })),
  timing: {total_sec: 9, scenes: [0, 1, 2].map((i) => ({id: `s${i + 1}`, start_ms: i * 3000, end_ms: (i + 1) * 3000}))},
  words: narr.flatMap((n, i) =>
    n.split(' ').map((w, k, a) => ({word: w, start_ms: i * 3000 + (k * 2400) / a.length, end_ms: i * 3000 + ((k + 1) * 2400) / a.length, scene_id: `s${i + 1}`})),
  ),
  images: {},
  style,
});

export const sampleThumb: ThumbProps = {text: 'WHAT IF YOU?', mood: 'shocked', style};
