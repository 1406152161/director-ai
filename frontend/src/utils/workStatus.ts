/**
 * @author zhangzhihao
 */

export const TERMINAL_STATUSES = ['completed', 'failed', 'cancelled', 'review_required'] as const;

const VIDEO_TERMINAL = new Set<string>(['completed', 'failed']);
const NOVEL_TERMINAL = new Set<string>([...TERMINAL_STATUSES, 'planned']);

export function isTerminalStatus(status: string): boolean {
  return (TERMINAL_STATUSES as readonly string[]).includes(status);
}

export function isVideoInProgress(status: string): boolean {
  return !VIDEO_TERMINAL.has(status);
}

export function isNovelInProgress(status: string): boolean {
  return !NOVEL_TERMINAL.has(status);
}
