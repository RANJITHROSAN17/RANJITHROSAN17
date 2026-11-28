import { Hono } from 'hono';
import { createPost } from '../core/post';

export const scheduler = new Hono();

/** Daily cron (00:05 UTC) — creates today's LENS post. */
scheduler.post('/daily-post', async (c) => {
  try {
    const post = await createPost();
    return c.json({ status: 'success', postId: post.id }, 200);
  } catch (error) {
    console.error(`Daily post failed: ${error}`);
    return c.json({ status: 'error', message: 'Failed to create daily post' }, 500);
  }
});
