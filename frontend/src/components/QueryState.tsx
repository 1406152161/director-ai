/**
 * @author zhangzhihao
 */
import type { ReactNode } from 'react';

interface QueryStateProps {
  isLoading?: boolean;
  isError?: boolean;
  error?: unknown;
  loadingText?: string;
  children: ReactNode;
}

export function QueryState({
  isLoading,
  isError,
  error,
  loadingText = '加载中…',
  children,
}: QueryStateProps) {
  if (isLoading) {
    return <p className="placeholder-hint">{loadingText}</p>;
  }
  if (isError) {
    const message = error instanceof Error ? error.message : '请稍后重试';
    return (
      <p className="form-error" role="alert">
        加载失败：{message}
      </p>
    );
  }
  return <>{children}</>;
}
