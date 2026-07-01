/**
 * @author zhangzhihao
 */
interface ProgressBarProps {
  value: number;
  mini?: boolean;
  className?: string;
}

export function ProgressBar({ value, mini, className }: ProgressBarProps) {
  const wrapClass = ['progress-bar-wrap', mini ? 'progress-bar-mini' : '', className]
    .filter(Boolean)
    .join(' ');
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className={wrapClass}>
      <div className="progress-bar" style={{ width: `${pct}%` }} />
    </div>
  );
}
