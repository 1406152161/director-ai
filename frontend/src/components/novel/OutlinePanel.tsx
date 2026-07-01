/**
 * @author zhangzhihao
 */
import { useQuery } from '@tanstack/react-query';
import { memo, useEffect, useState } from 'react';
import { fetchNovelOutline } from '../../api/client';
import {
  parseNovelBible,
  type NovelBibleOutlineItem,
  type NovelBibleVolume,
} from '../../utils/novelBible';
import { chapterStatusLabel } from '../../utils/novelLabels';

export const OUTLINE_PAGE_SIZE = 50;

function groupOutlineByVolume(
  items: NovelBibleOutlineItem[],
  volumes: NovelBibleVolume[],
): { volume: NovelBibleVolume | null; items: NovelBibleOutlineItem[] }[] {
  if (volumes.length === 0) {
    return [{ volume: null, items }];
  }

  const sortedVolumes = [...volumes].sort((a, b) => a.chapter_from - b.chapter_from);
  const assigned = new Set<number>();
  const groups: { volume: NovelBibleVolume | null; items: NovelBibleOutlineItem[] }[] = [];

  for (const vol of sortedVolumes) {
    const volItems = items.filter(
      (item) =>
        item.index >= vol.chapter_from &&
        item.index <= vol.chapter_to &&
        !assigned.has(item.index),
    );
    volItems.forEach((item) => assigned.add(item.index));
    if (volItems.length > 0) {
      groups.push({ volume: vol, items: volItems });
    }
  }

  const unassigned = items.filter((item) => !assigned.has(item.index));
  if (unassigned.length > 0) {
    groups.push({ volume: null, items: unassigned });
  }

  return groups.length > 0 ? groups : [{ volume: null, items }];
}

export interface OutlinePanelProps {
  novelId: string;
  bible: ReturnType<typeof parseNovelBible>;
  chapterStatusByIndex: Map<number, string>;
  onOpenChapter: (item: NovelBibleOutlineItem) => void;
  onSaveOutline: (outline: NovelBibleOutlineItem[]) => void;
  saving: boolean;
  readOnly: boolean;
}

export const OutlinePanel = memo(function OutlinePanel({
  novelId,
  bible,
  chapterStatusByIndex,
  onOpenChapter,
  onSaveOutline,
  saving,
  readOnly,
}: OutlinePanelProps) {
  const totalChapters = bible.meta?.total_chapters ?? bible.outline.length;
  const usePaginated = Boolean(bible.meta?.outline_in_db && totalChapters > 0);
  const totalPages = Math.max(1, Math.ceil(totalChapters / OUTLINE_PAGE_SIZE));
  const [page, setPage] = useState(1);
  const [detailFilter, setDetailFilter] = useState<'all' | 'skeleton' | 'detailed'>('all');
  const [localOutline, setLocalOutline] = useState<NovelBibleOutlineItem[]>([]);

  const fromChapter = (page - 1) * OUTLINE_PAGE_SIZE + 1;
  const toChapter = Math.min(page * OUTLINE_PAGE_SIZE, totalChapters);

  const { data: pageOutline, isLoading: outlineLoading } = useQuery({
    queryKey: ['novel-outline', novelId, fromChapter, toChapter, detailFilter],
    queryFn: () =>
      fetchNovelOutline(
        novelId,
        fromChapter,
        toChapter,
        detailFilter === 'all' ? undefined : detailFilter,
      ),
    enabled: usePaginated,
  });

  useEffect(() => {
    setPage(1);
  }, [totalChapters]);

  useEffect(() => {
    if (usePaginated && pageOutline) {
      setLocalOutline(pageOutline);
    } else if (!usePaginated) {
      setLocalOutline(bible.outline);
    }
  }, [usePaginated, pageOutline, bible.outline]);

  const outline = localOutline;

  if (usePaginated && outlineLoading && outline.length === 0) {
    return <p className="placeholder-hint">加载大纲第 {fromChapter}–{toChapter} 章…</p>;
  }

  if (!usePaginated && outline.length === 0) {
    return <p className="placeholder-hint">大纲生成中或暂无数据…</p>;
  }

  if (usePaginated && outline.length === 0 && !outlineLoading) {
    return (
      <p className="placeholder-hint">
        第 {fromChapter}–{toChapter} 章暂无大纲（规划可能尚未覆盖此区间）
      </p>
    );
  }

  const sorted = [...outline].sort((a, b) => a.index - b.index);
  const volumes = bible.volumes ?? [];
  const volumeGroups = groupOutlineByVolume(sorted, volumes);

  const renderOutlineItem = (item: NovelBibleOutlineItem) => {
    const chStatus = chapterStatusByIndex.get(item.index);
    const isWritten = chStatus === 'completed';
    const idx = sorted.findIndex((o) => o.index === item.index);
    const detailLevel = (item as NovelBibleOutlineItem & { detail_level?: string }).detail_level;
    return (
      <li key={item.index} className={isWritten ? 'outline-written' : ''}>
        <div className="outline-edit-header">
          <button type="button" className="outline-item-btn" onClick={() => onOpenChapter(item)}>
            <span className="outline-item-title">
              第{item.index}章 {item.title}
              {detailLevel && detailLevel !== 'detailed' && (
                <span className="outline-level-tag">骨架</span>
              )}
            </span>
            <span className="outline-item-status">
              {chStatus ? chapterStatusLabel(chStatus) : '未写'}
            </span>
          </button>
        </div>
        {!readOnly ? (
          <>
            <input
              className="outline-edit-title"
              value={item.title}
              onChange={(e) => {
                const next = [...sorted];
                next[idx] = { ...next[idx], title: e.target.value };
                setLocalOutline(next);
              }}
            />
            <textarea
              className="outline-edit-summary"
              rows={2}
              placeholder="本章摘要"
              value={item.summary}
              onChange={(e) => {
                const next = [...sorted];
                next[idx] = { ...next[idx], summary: e.target.value };
                setLocalOutline(next);
              }}
            />
            <input
              className="outline-edit-hook"
              placeholder="章末钩子"
              value={item.hook ?? ''}
              onChange={(e) => {
                const next = [...sorted];
                next[idx] = { ...next[idx], hook: e.target.value };
                setLocalOutline(next);
              }}
            />
          </>
        ) : (
          <>
            {item.summary && <p className="bible-text outline-summary">{item.summary}</p>}
            {item.hook && <p className="bible-text outline-hook">钩子：{item.hook}</p>}
          </>
        )}
      </li>
    );
  };

  return (
    <div className="novel-bible-panel">
      <section className="bible-section">
        <div className="outline-panel-toolbar">
          <h3>
            章节大纲（全书 {totalChapters} 章
            {usePaginated ? ` · 第 ${fromChapter}–${toChapter} 章` : ''}）
          </h3>
          {usePaginated && (
            <div className="outline-pagination">
              <label htmlFor="outlineDetailFilter">层级</label>
              <select
                id="outlineDetailFilter"
                value={detailFilter}
                onChange={(e) => {
                  setDetailFilter(e.target.value as 'all' | 'skeleton' | 'detailed');
                  setPage(1);
                }}
              >
                <option value="all">全部</option>
                <option value="skeleton">仅骨架</option>
                <option value="detailed">仅详细</option>
              </select>
              <button
                type="button"
                className="download-btn"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                上一页
              </button>
              <span className="outline-page-info">
                第 {page}/{totalPages} 页
              </span>
              <input
                className="outline-page-jump"
                type="number"
                min={1}
                max={totalPages}
                value={page}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  if (n >= 1 && n <= totalPages) setPage(n);
                }}
              />
              <button
                type="button"
                className="download-btn"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                下一页
              </button>
            </div>
          )}
        </div>
        {volumeGroups.map(({ volume, items: volItems }) => (
          <div key={volume?.id ?? `ungrouped-${volItems[0]?.index ?? 0}`} className="outline-volume-group">
            {volume && (
              <h4 className="outline-volume-header">
                {volume.title}（第{volume.chapter_from}–{volume.chapter_to}章）
              </h4>
            )}
            {!volume && volumes.length > 0 && volItems.length > 0 && (
              <h4 className="outline-volume-header">其他章节</h4>
            )}
            <ol className="bible-outline-list">
              {volItems.map((item) => renderOutlineItem(item))}
            </ol>
          </div>
        ))}
        {!readOnly && (
          <button
            type="button"
            className="btn-primary btn-sm"
            disabled={saving}
            onClick={() => onSaveOutline(outline)}
          >
            {saving ? '保存中…' : usePaginated ? '保存本页大纲' : '保存大纲'}
          </button>
        )}
        {bible.outline_truncated && (
          <p className="placeholder-hint outline-truncation-hint">
            仅展示前 500 章大纲，完整大纲请通过分页接口获取
          </p>
        )}
      </section>
    </div>
  );
});
