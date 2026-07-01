/**
 * @author zhangzhihao
 */

const VIDEO_TERMINAL = new Set(['completed', 'failed']);
const NOVEL_TERMINAL = new Set(['completed', 'failed', 'planned']);

export function isVideoInProgress(status: string): boolean {
  return !VIDEO_TERMINAL.has(status);
}

export function isNovelInProgress(status: string): boolean {
  return !NOVEL_TERMINAL.has(status);
}
