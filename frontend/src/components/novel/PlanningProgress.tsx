/**
 * @author zhangzhihao
 */
import { memo } from 'react';
import { StatusBadge } from '../StatusBadge';
import { formatPlanningProgress, type NovelBible } from '../../utils/novelBible';
import { GENRE_LABEL, novelStatusLabel } from '../../utils/novelLabels';

export type NovelWorkbenchHeaderProps = {
  title: string;
  genre: string;
  subtitle: string;
  status: string;
  progress: number;
  isBusy: boolean;
};

export const NovelWorkbenchHeader = memo(function NovelWorkbenchHeader({
  title,
  genre,
  subtitle,
  status,
  progress,
  isBusy,
}: NovelWorkbenchHeaderProps) {
  return (
    <header className="novel-workbench-header">
      <div>
        <h1>{title || '未命名小说'}</h1>
        <p className="subtitle">
          {GENRE_LABEL[genre] ?? genre} · {subtitle}
        </p>
      </div>
      <StatusBadge
        status={status}
        label={`${novelStatusLabel(status, progress)}${isBusy ? ` ${progress}%` : ''}`}
      />
    </header>
  );
});

export type PlanningProgressProps = {
  isPlanned: boolean;
  isPlanning: boolean;
  isFailed: boolean;
  needsReview: boolean;
  novelError?: string | null;
  progress: number;
  bible: NovelBible;
  retryPlanPending: boolean;
  onRetryPlan: () => void;
};

export const PlanningProgress = memo(function PlanningProgress({
  isPlanned,
  isPlanning,
  isFailed,
  needsReview,
  novelError,
  progress,
  bible,
  retryPlanPending,
  onRetryPlan,
}: PlanningProgressProps) {
  return (
    <>
      {isPlanned && (
        <div className="planned-banner">
          整本规划已生成，请审阅世界观与章节大纲。确认后选择本次撰写章数即可开始写作。
        </div>
      )}

      {isPlanning && bible.meta?.planning_state && (
        <div className="planned-banner planning-progress-banner">
          <span>{formatPlanningProgress(bible.meta)}</span>
          <div className="planning-progress-bar">
            <div className="planning-progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <span className="planning-progress-pct">{progress}%</span>
        </div>
      )}

      {novelError && <p className="error-text">{novelError}</p>}
      {isFailed && (
        <div className="planned-banner error-banner">
          规划中断，已保留进度。点击下方从断点续跑（不会清空已生成大纲）。
          <button
            type="button"
            className="btn-primary btn-sm"
            disabled={retryPlanPending}
            onClick={onRetryPlan}
          >
            {retryPlanPending ? '提交中…' : '续跑规划'}
          </button>
        </div>
      )}
      {needsReview && (
        <p className="error-text review-banner">
          有章节未通过质量校验，请查看标黄章节；处理前无法续写。
        </p>
      )}
    </>
  );
});
