/**
 * @author zhangzhihao
 */
import { useEffect, useRef } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

export type ProgressResourceKind = 'project' | 'novel';

export interface ProgressEventPayload {
  type: 'progress' | 'heartbeat';
  status?: string;
  progress?: number;
  error?: string | null;
  done?: boolean;
}

const TERMINAL_PROJECT = new Set(['completed', 'failed']);
const TERMINAL_NOVEL = new Set(['completed', 'failed', 'planned', 'review_required']);

export function isTerminalProgressStatus(kind: ProgressResourceKind, status: string | undefined): boolean {
  if (!status) return false;
  return kind === 'project' ? TERMINAL_PROJECT.has(status) : TERMINAL_NOVEL.has(status);
}

/**
 * 订阅 SSE；断线指数退避重连，多次失败后 onDisconnected 回退轮询。
 */
export function useProgressEvents(
  kind: ProgressResourceKind,
  resourceId: string | undefined,
  enabled: boolean,
  onProgress: (payload: ProgressEventPayload) => void,
  onConnected?: () => void,
  onDisconnected?: () => void,
) {
  const onProgressRef = useRef(onProgress);
  const onConnectedRef = useRef(onConnected);
  const onDisconnectedRef = useRef(onDisconnected);
  onProgressRef.current = onProgress;
  onConnectedRef.current = onConnected;
  onDisconnectedRef.current = onDisconnected;

  useEffect(() => {
    if (!resourceId || !enabled) return;

    const prefix = kind === 'project' ? 'projects' : 'novels';
    const url = `${API_BASE}/api/${prefix}/${resourceId}/events`;
    let source: EventSource | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let retryAttempt = 0;
    let closed = false;

    const connect = () => {
      source = new EventSource(url);
      source.onopen = () => {
        retryAttempt = 0;
        onConnectedRef.current?.();
      };
      source.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as ProgressEventPayload;
          if (payload.type === 'heartbeat') return;
          onProgressRef.current(payload);
          if (payload.done) {
            closed = true;
            source?.close();
          }
        } catch {
          /* ignore */
        }
      };
      source.onerror = () => {
        source?.close();
        if (closed) return;
        retryAttempt += 1;
        if (retryAttempt >= 4) {
          onDisconnectedRef.current?.();
          return;
        }
        const delay = Math.min(1000 * 2 ** (retryAttempt - 1), 8000);
        retryTimer = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      closed = true;
      const currentSource = source;
      const currentTimer = retryTimer;
      source = null;
      retryTimer = null;
      if (currentTimer) clearTimeout(currentTimer);
      currentSource?.close();
    };
  }, [kind, resourceId, enabled]);
}
