/**
 * @author zhangzhihao
 */
interface StatusBadgeProps {
  status: string;
  label: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const cls = ['status-badge', `status-${status}`, className].filter(Boolean).join(' ');
  return <span className={cls}>{label}</span>;
}
