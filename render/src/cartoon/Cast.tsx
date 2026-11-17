import type {Look} from './Character';

/** The recurring cast. "you" is the viewer; the others are friends and strangers. */
export const CAST: Record<string, Look> = {
  you: {skin: '#f2e8dc', hair: 'short', hairColor: '#3b2a20', top: 'hoodie', topColor: '#3aa59b', pants: '#2f3a4f'},
  maya: {skin: '#e8c9a8', hair: 'long', hairColor: '#4a2f1d', top: 'hoodie', topColor: '#2f4a7a', pants: '#262b36'},
  leo: {skin: '#c99b74', hair: 'curly', hairColor: '#2e2018', top: 'sweater', topColor: '#4f7a43', pants: '#2b3242'},
  zoe: {skin: '#f2e8dc', hair: 'ponytail', hairColor: '#c8692e', top: 'hoodie', topColor: '#6a4f8f', pants: '#2b3242'},
  sam: {skin: '#a8754f', hair: 'spiky', hairColor: '#1f1a17', top: 'sweater', topColor: '#b5524a', pants: '#262b36', glasses: true},
  ana: {skin: '#dcb48f', hair: 'bob', hairColor: '#2a2220', top: 'tee', topColor: '#e3a23b', pants: '#3a3f4a'},
  eng: {skin: '#f3dcc6', hair: 'short', hairColor: '#5a3a22', top: 'sweater', topColor: '#2f8f88', pants: '#3a3f55', glasses: true, iris: '#5b3a1e'},
  eng_old: {skin: '#efd6be', hair: 'short', hairColor: '#c9c4bd', top: 'sweater', topColor: '#2f8f88', pants: '#3a3f55', glasses: true, iris: '#5b3a1e'},
  boss: {skin: '#ecc8a6', hair: 'short', hairColor: '#7a5434', top: 'suit', topColor: '#6b7684', tie: '#c0392b', pants: '#4a525e', mustache: '#7a5434', iris: '#3d6b8f'},
  exec1: {skin: '#f0d0b0', hair: 'short', hairColor: '#9b968f', top: 'suit', topColor: '#3b4250', tie: '#2f6db5', pants: '#2c313b', glasses: true, iris: '#4a5a6a'},
  exec2: {skin: '#d9a77e', hair: 'bald', hairColor: '#2e2a26', top: 'suit', topColor: '#5a4636', tie: '#d4a017', pants: '#3a2f27', mustache: '#3a2f27', iris: '#4a3020'},
  exec3: {skin: '#f2d4b8', hair: 'short', hairColor: '#ece8e0', top: 'suit', topColor: '#26354a', tie: '#a83232', pants: '#1f2a3a', mustache: '#ece8e0', iris: '#3d6b8f'},
  joy: {skin: '#f1d3b5', hair: 'long', hairColor: '#1e1a1a', top: 'labcoat', topColor: '#f6f4ef', shirt: '#6a8fbf', pants: '#3a4258', iris: '#4a3020'},
  fuji: {skin: '#efd2b2', hair: 'bob', hairColor: '#1f1b1a', top: 'suit', topColor: '#2e5e4e', tie: '#e8e2d0', pants: '#24302b', iris: '#3a2a1e'},
  techa: {skin: '#e9c49e', hair: 'curly', hairColor: '#2e2018', top: 'hoodie', topColor: '#e07a3f', pants: '#2b3242', iris: '#3a2a1e'},
  anchor: {skin: '#ecc9a8', hair: 'bob', hairColor: '#6b3f22', top: 'suit', topColor: '#b8323a', tie: 'none', shirt: '#f6f3ec', pants: '#2c313b', iris: '#3a2a1e'},
  vince: {skin: '#efcfae', hair: 'short', hairColor: '#4a3426', top: 'suit', topColor: '#7a6a52', tie: '#2f6db5', pants: '#3a332a', glasses: true, iris: '#3a2a1e'},
  kid1: {skin: '#f3d6bc', hair: 'spiky', hairColor: '#3a2618', top: 'hoodie', topColor: '#3b82c4', pants: '#2b3242', iris: '#3a2a1e'},
  kid2: {skin: '#f0d0b2', hair: 'ponytail', hairColor: '#5a3a22', top: 'tee', topColor: '#e0569b', pants: '#2b3242', iris: '#3a2a1e'},
  techb: {skin: '#f4dfcc', hair: 'ponytail', hairColor: '#c8692e', top: 'tee', topColor: '#7b5ea7', pants: '#2b3242', iris: '#3d6b8f'},
  zombie: {skin: '#a8bf92', hair: 'short', hairColor: '#3a3f2a', top: 'tee', topColor: '#6d6a5e', pants: '#3b3d33', torn: true},
};
