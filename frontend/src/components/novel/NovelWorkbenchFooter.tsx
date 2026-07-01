/**
 * @author zhangzhihao
 */
import { memo } from 'react';
import { exportNovelUrl } from '../../api/client';

function firstMutationError(
  ...mutations: Array<{ isError: boolean; error: unknown }>
): string | null {
  for (const m of mutations) {
    if (m.isError) {
      return (m.error as Error)?.message ?? '操作失败';
    }
  }
  return null;
}

export type NovelWorkbenchFooterProps = {
  novelId: string;
  isPlanned: boolean;
  isBusy: boolean;
  needsReview: boolean;
  writeCount: number;
  onWriteCountChange: (count: number) => void;
  onConfirmPlan: () => void;
  onContinueWrite: () => void;
  onReplan: () => void;
  continuePending: boolean;
  replanPending: boolean;
  showConfirmModal: boolean;
  onCloseConfirmModal: () => void;
  onStartWriting: () => void;
  startWritingPending: boolean;
  mutations: Array<{ isError: boolean; error: unknown }>;
};

export const NovelWorkbenchFooter = memo(function NovelWorkbenchFooter({
  novelId,
  isPlanned,
  isBusy,
  needsReview,
  writeCount,
  onWriteCountChange,
  onConfirmPlan,
  onContinueWrite,
  onReplan,
  continuePending,
  replanPending,
  showConfirmModal,
  onCloseConfirmModal,
  onStartWriting,
  startWritingPending,
  mutations,
}: NovelWorkbenchFooterProps) {
  const footerMutationError = firstMutationError(...mutations);

  return (
    <>
      <footer className="novel-workbench-footer">
        {footerMutationError && (
          <p className="form-error footer-mutation-error" role="alert">
            {footerMutationError}
          </p>
        )}
        {isPlanned && (
          <button type="button" className="btn-primary" disabled={isBusy} onClick={onConfirmPlan}>
            确认规划，开始写作
          </button>
        )}
        {!isPlanned && (
          <div className="continue-write-group">
            <label htmlFor="writeCount">续写</label>
            <input
              id="writeCount"
              type="number"
              min={1}
              max={20}
              value={writeCount}
              onChange={(e) => onWriteCountChange(Number(e.target.value))}
            />
            <span>章</span>
            <button
              type="button"
              className="btn-primary"
              disabled={isBusy || needsReview || continuePending}
              onClick={onContinueWrite}
            >
              {continuePending ? '提交中…' : '开始续写'}
            </button>
          </div>
        )}
        <a className="download-btn" href={exportNovelUrl(novelId, 'md')} download>
          导出 Markdown
        </a>
        <a className="download-btn" href={exportNovelUrl(novelId, 'txt')} download>
          导出 TXT
        </a>
        <button
          type="button"
          className="download-btn"
          disabled={isBusy || isPlanned || replanPending}
          onClick={onReplan}
        >
          {replanPending ? '调整中…' : '调整后续大纲'}
        </button>
      </footer>

      {showConfirmModal && (
        <div className="modal-overlay" onClick={onCloseConfirmModal}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3>确认规划并开始写作</h3>
            <p>整本大纲已就绪，请选择本次撰写的章数（最多 20 章）。</p>
            <div className="form-row">
              <label htmlFor="confirmWriteCount">本次撰写章数</label>
              <input
                id="confirmWriteCount"
                type="number"
                min={1}
                max={20}
                value={writeCount}
                onChange={(e) => onWriteCountChange(Number(e.target.value))}
              />
            </div>
            <div className="modal-actions">
              <button type="button" className="download-btn" onClick={onCloseConfirmModal}>
                取消
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={startWritingPending}
                onClick={onStartWriting}
              >
                {startWritingPending ? '提交中…' : '开始写作'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
});
