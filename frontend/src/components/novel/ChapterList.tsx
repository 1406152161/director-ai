/**
 * @author zhangzhihao
 */
import { memo } from 'react';
import type { NovelChapterResponse } from '../../api/client';
import type { NovelBible } from '../../utils/novelBible';
import { chapterStatusLabel } from '../../utils/novelLabels';

export type MainTab = 'read' | 'world' | 'outline';
export type LeftPanelMode = 'chapters' | 'plan';

const PLAN_NAV_ITEMS: { label: string; tab: MainTab; section?: string }[] = [
  { label: '正文阅读', tab: 'read' },
  { label: '世界观 / 体系', tab: 'world', section: 'world' },
  { label: '人物 / 道具', tab: 'world', section: 'characters' },
  { label: '卷弧 / 伏笔', tab: 'world', section: 'volumes' },
  { label: '章节大纲', tab: 'outline' },
];

export type ChapterListProps = {
  chapters: NovelChapterResponse[];
  selectedIndex: number;
  onSelectChapter: (index: number) => void;
  leftPanel: LeftPanelMode;
  onLeftPanelChange: (mode: LeftPanelMode) => void;
  mainTab: MainTab;
  onPlanNavClick: (tab: MainTab, section?: string) => void;
  bible: NovelBible;
  isBusy: boolean;
  isPlanned: boolean;
};

export const ChapterList = memo(function ChapterList({
  chapters,
  selectedIndex,
  onSelectChapter,
  leftPanel,
  onLeftPanelChange,
  mainTab,
  onPlanNavClick,
  bible,
  isBusy,
  isPlanned,
}: ChapterListProps) {
  return (
    <aside className="novel-chapters-panel">
      <div className="left-panel-toggle">
        <button
          type="button"
          className={leftPanel === 'chapters' ? 'active' : ''}
          onClick={() => onLeftPanelChange('chapters')}
        >
          目录
        </button>
        <button
          type="button"
          className={leftPanel === 'plan' ? 'active' : ''}
          onClick={() => onLeftPanelChange('plan')}
        >
          规划
        </button>
      </div>

      <h2>章节目录</h2>
      <ul className="chapter-list">
        {chapters.length === 0 && (
          <li className="chapter-empty">
            {isBusy ? '规划/写作进行中…' : isPlanned ? '确认规划后开始写作' : '暂无章节'}
          </li>
        )}
        {chapters.map((ch) => (
          <li key={ch.id}>
            <button
              type="button"
              className={`chapter-item ${selectedIndex === ch.index ? 'active' : ''} ${ch.status === 'needs_review' ? 'needs-review' : ''}`}
              onClick={() => onSelectChapter(ch.index)}
            >
              <span>
                第{ch.index}章 {ch.title}
              </span>
              <span className={`chapter-status status-${ch.status}`}>
                {chapterStatusLabel(ch.status)}
              </span>
            </button>
          </li>
        ))}
      </ul>
      {bible.meta?.total_chapters && (
        <p className="chapter-meta-hint">
          全书规划 {bible.meta.total_chapters} 章
          {bible.meta.l2_detail_to ? ` · 已详细化 1–${bible.meta.l2_detail_to} 章` : ''}
          {bible.meta.outline_in_db && bible.outline.length < bible.meta.total_chapters
            ? ` · 大纲列表展示前 ${bible.outline.length} 章`
            : ''}
        </p>
      )}

      {leftPanel === 'plan' && (
        <nav className="plan-section-nav">
          <p className="placeholder-hint plan-nav-hint">审阅分区后确认规划并开始写作</p>
          <ul>
            {PLAN_NAV_ITEMS.map((item) => (
              <li key={item.label}>
                <button
                  type="button"
                  className={`plan-nav-item ${mainTab === item.tab ? 'active' : ''}`}
                  onClick={() => onPlanNavClick(item.tab, item.section)}
                >
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </aside>
  );
});
