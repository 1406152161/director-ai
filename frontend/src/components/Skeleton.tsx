/**
 * @author zhangzhihao
 */
import './Skeleton.css';

type CardSkeletonProps = {
  count?: number;
};

export function CardSkeleton({ count = 3 }: CardSkeletonProps) {
  return (
    <div className="skeleton-card-grid" aria-hidden="true">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-block skeleton-card-thumb" />
          <div className="skeleton-line skeleton-line-lg" />
          <div className="skeleton-line skeleton-line-sm" />
        </div>
      ))}
    </div>
  );
}

export function ContentSkeleton() {
  return (
    <div className="skeleton-content-layout" aria-hidden="true">
      <aside className="skeleton-sidebar">
        <div className="skeleton-line skeleton-line-lg" />
        <div className="skeleton-line" />
        <div className="skeleton-line" />
        <div className="skeleton-line skeleton-line-sm" />
      </aside>
      <div className="skeleton-main">
        <div className="skeleton-line skeleton-line-lg" />
        <div className="skeleton-block skeleton-paragraph" />
        <div className="skeleton-block skeleton-paragraph" />
      </div>
    </div>
  );
}

type InlineSpinnerProps = {
  label?: string;
};

export function InlineSpinner({ label }: InlineSpinnerProps) {
  return (
    <span className="inline-spinner" role="status">
      <span className="inline-spinner-icon" aria-hidden="true" />
      {label && <span className="inline-spinner-label">{label}</span>}
    </span>
  );
}
