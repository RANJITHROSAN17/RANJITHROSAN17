import { reddit } from '@devvit/web/server';
import { dayLabel, dayNumber } from '../../shared/game';
import { todayPuzzle } from './puzzle';

export const createPost = async () => {
  const day = dayNumber();
  const puzzle = todayPuzzle();
  return await reddit.submitCustomPost({
    title: `${dayLabel(day)} — Something's off. Spot it in 60 seconds.`,
    textFallback: { text: `One image. One anomaly. Tap Play and find the one thing that's wrong.\n\nPack: ${puzzle.pack} · Difficulty: ${puzzle.difficulty}/10\n\nEveryone plays the same image today. The crowd heatmap reveals where everyone looked.` },
  });
};
