/**
 * @author zhangzhihao
 */
import { memo } from 'react';
import type { NovelChapterResponse } from '../../api/client';
import { InlineSpinner } from '../Skeleton';
import type { NovelBibleBeat } from '../../utils/novelBible';
import { NOVEL_STATUS_LABEL } from '../../utils/novelLabels';

/** 安全解析章节校验问题 JSON，避免 malformed 数据导致页面崩溃。 */
export function parseValidationIssues(raw: string | null | undefined): string[] {
  try {
    const parsed = JSON.parse(raw || '[]');
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return ['解析问题列表失败，请刷新重试'];
  }
}

const ChapterBeatsPanel = memo(function ChapterBeatsPanel({ beats }: { beats: NovelBibleBeat[] }) {
  return (
    <section className="chapter-beats-panel">
      <details>
        <summary>场景 Beat（{beats.length}）</summary>
        <ol className="bible-beat-list">
          {beats.map((beat) => (
            <li key={beat.index}>
              <strong>
                Beat {beat.index} · {beat.scene}
              </strong>
              {beat.goal && <p className="bible-meta">目标：{beat.goal}</p>}
              {beat.conflict && <p className="bible-meta">冲突：{beat.conflict}</p>}
              {beat.outcome && <p className="bible-meta">结果：{beat.outcome}</p>}
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
});

export type ChapterReaderProps = {
  currentChapter?: NovelChapterResponse;
  chapterBeats: NovelBibleBeat[];
  isBusy: boolean;
  isPlanned: boolean;
  approvePending: boolean;
  rewritePending: boolean;
  onApprove: () => void;
  onRewrite: () => void;
};

export const ChapterReader = memo(function ChapterReader({
  currentChapter,
  chapterBeats,
  isBusy,
  isPlanned,
  approvePending,
  rewritePending,
  onApprove,
  onRewrite,
}: ChapterReaderProps) {
  if (!currentChapter) {
    return (
      <p className="placeholder-hint">
        {isBusy
          ? 'AI 正在规划与写作，请稍候…'
          : isPlanned
            ? '请审阅「世界观」「大纲」Tab，确认后开始写作'
            : '请选择章节阅读'}
      </p>
    );
  }

  return (
    <>
      <h2>
        第{currentChapter.index}章 {currentChapter.title}
      </h2>
      {currentChapter.status === 'completed' || currentChapter.status === 'needs_review' ? (
        <div className="novel-content">
          {currentChapter.content.split('\n').map((para, i) => (
            <p key={i}>{para}</p>
          ))}
        </div>
      ) : (
        <p className="placeholder-hint">
          本章{NOVEL_STATUS_LABEL[currentChapter.status] ?? '生成中'}…
        </p>
      )}
      {currentChapter.status === 'needs_review' && (
        <div className="validation-issues">
          <h3>责编问题（评分 {currentChapter.validation_score}）</h3>
          <ul>
            {parseValidationIssues(currentChapter.validation_issues).map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
          <button
            type="button"
            className="btn-primary"
            disabled={approvePending || rewritePending || isBusy}
            onClick={onApprove}
          >
            {approvePending ? <InlineSpinner label="处理中…" /> : '确认放行本章'}
          </button>
          <button
            type="button"
            className="download-btn"
            disabled={approvePending || rewritePending || isBusy}
            onClick={onRewrite}
          >
            {rewritePending ? <InlineSpinner label="重写中…" /> : '重写本章'}
          </button>
        </div>
      )}
      {currentChapter.word_count > 0 && (
        <p className="word-count">约 {currentChapter.word_count} 字</p>
      )}
      {chapterBeats.length > 0 && <ChapterBeatsPanel beats={chapterBeats} />}
    </>
  );
});
