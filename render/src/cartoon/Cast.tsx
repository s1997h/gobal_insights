import type {Look} from './Character';

/** The recurring cast. "you" is the viewer; the others are friends and strangers. */
export const CAST: Record<string, Look> = {
  you: {skin: '#f2e8dc', hair: 'short', hairColor: '#3b2a20', top: 'hoodie', topColor: '#3aa59b', pants: '#2f3a4f'},
  maya: {skin: '#e8c9a8', hair: 'long', hairColor: '#4a2f1d', top: 'hoodie', topColor: '#2f4a7a', pants: '#262b36'},
  leo: {skin: '#c99b74', hair: 'curly', hairColor: '#2e2018', top: 'sweater', topColor: '#4f7a43', pants: '#2b3242'},
  zoe: {skin: '#f2e8dc', hair: 'ponytail', hairColor: '#c8692e', top: 'hoodie', topColor: '#6a4f8f', pants: '#2b3242'},
  sam: {skin: '#a8754f', hair: 'spiky', hairColor: '#1f1a17', top: 'sweater', topColor: '#b5524a', pants: '#262b36', glasses: true},
  ana: {skin: '#dcb48f', hair: 'bob', hairColor: '#2a2220', top: 'tee', topColor: '#e3a23b', pants: '#3a3f4a'},
  zombie: {skin: '#a8bf92', hair: 'short', hairColor: '#3a3f2a', top: 'tee', topColor: '#6d6a5e', pants: '#3b3d33', torn: true},
};
