/**
 * @author zhangzhihao
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  approveNovelChapter,
  chatNovel,
  continueNovel,
  exportNovelUrl,
  fetchNovel,
  patchNovelBible,
  replanNovel,
  retryNovelPlan,
  rewriteNovelChapter,
  startNovelWriting,
  type NovelChapterResponse,
} from '../api/client';
import { OutlinePanel } from '../components/novel/OutlinePanel';
import { StatusBadge } from '../components/StatusBadge';
import {
  beatsForChapter,
  characterDescription,
  formatPlanningProgress,
  formatRollingSummary,
  parseNovelBible,
  type NovelBibleBeat,
  type NovelBibleCharacter,
  type NovelBibleForeshadowing,
  type NovelBibleItem,
  type NovelBibleOutlineItem,
  type NovelBibleVolume,
} from '../utils/novelBible';
import { GENRE_LABEL, NOVEL_STATUS_LABEL, novelStatusLabel } from '../utils/novelLabels';
import { isTerminalProgressStatus, useProgressEvents } from '../hooks/useProgressEvents';

type MainTab = 'read' | 'world' | 'outline';
type LeftPanelMode = 'chapters' | 'plan';

const PLAN_NAV_ITEMS: { label: string; tab: MainTab; section?: string }[] = [
  { label: '正文阅读', tab: 'read' },
  { label: '世界观 / 体系', tab: 'world', section: 'world' },
  { label: '人物 / 道具', tab: 'world', section: 'characters' },
  { label: '卷弧 / 伏笔', tab: 'world', section: 'volumes' },
  { label: '章节大纲', tab: 'outline' },
];

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

/** 安全解析章节校验问题 JSON，避免 malformed 数据导致页面崩溃。 */
function parseValidationIssues(raw: string | null | undefined): string[] {
  try {
    const parsed = JSON.parse(raw || '[]');
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return ['解析问题列表失败，请刷新重试'];
  }
}

function NovelWorkbenchPage() {
  const { novelId } = useParams<{ novelId: string }>();
  const queryClient = useQueryClient();
  const [selectedIndex, setSelectedIndex] = useState(1);
  const [mainTab, setMainTab] = useState<MainTab>('read');
  const [leftPanel, setLeftPanel] = useState<LeftPanelMode>('chapters');
  const [planScrollSection, setPlanScrollSection] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'assistant'; text: string }[]>(
    [],
  );
  const [writeCount, setWriteCount] = useState(3);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [editWorld, setEditWorld] = useState('');
  const [editPower, setEditPower] = useState('');
  /** SSE 刷新 bible 时，若用户正在编辑世界观则不同步覆盖。 */
  const [worldDirty, setWorldDirty] = useState(false);
  const [sseConnected, setSseConnected] = useState(false);

  const { data: novel, isLoading, isError, error } = useQuery({
    queryKey: ['novel', novelId],
    queryFn: () => fetchNovel(novelId!),
    enabled: !!novelId,
    refetchInterval: (query) => {
      if (sseConnected) return false;
      const status = query.state.data?.status;
      return status && !['completed', 'failed', 'planned'].includes(status) ? 2000 : false;
    },
  });

  const onNovelProgress = useCallback(() => {
    setSseConnected(true);
    if (novelId) {
      queryClient.invalidateQueries({ queryKey: ['novel', novelId] });
    }
  }, [novelId, queryClient]);

  useProgressEvents(
    'novel',
    novelId,
    !!novelId && !isTerminalProgressStatus('novel', novel?.status),
    onNovelProgress,
  );

  const bible = novel ? parseNovelBible(novel.bible_json) : null;
  const isPlanned = novel?.status === 'planned';
  const isFailed = novel?.status === 'failed';
  const isPlanning = novel?.status === 'planning';
  const isBusy = isPlanning || novel?.status === 'writing';
  const needsReview = novel?.status === 'review_required';

  useEffect(() => {
    if (!novel?.chapters?.length) return;
    const completed = novel.chapters.filter((c) => c.status === 'completed');
    if (completed.length > 0) {
      setSelectedIndex(completed[completed.length - 1].index);
    }
  }, [novel?.chapters, novel?.status]);

  useEffect(() => {
    if (isPlanned) {
      setMainTab('outline');
      setLeftPanel('plan');
    }
  }, [isPlanned]);

  useEffect(() => {
    if (worldDirty || !bible) return;
    setEditWorld(bible.world);
    setEditPower(bible.power_system ?? '');
  }, [bible?.world, bible?.power_system, novel?.bible_json, worldDirty]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['novel', novelId] });

  const startWritingMutation = useMutation({
    mutationFn: (count: number) => startNovelWriting(novelId!, count),
    onSuccess: () => {
      setShowConfirmModal(false);
      invalidate();
    },
  });

  const continueMutation = useMutation({
    mutationFn: (count: number) => continueNovel(novelId!, count),
    onSuccess: invalidate,
  });

  const patchMutation = useMutation({
    mutationFn: (patch: Parameters<typeof patchNovelBible>[1]) =>
      patchNovelBible(novelId!, patch),
    onSuccess: (_data, patch) => {
      if (patch.world !== undefined || patch.power_system !== undefined) {
        setWorldDirty(false);
      }
      invalidate();
    },
  });

  const approveMutation = useMutation({
    mutationFn: () => approveNovelChapter(novelId!, selectedIndex),
    onSuccess: invalidate,
  });

  const rewriteMutation = useMutation({
    mutationFn: () => rewriteNovelChapter(novelId!, selectedIndex),
    onSuccess: invalidate,
  });

  const replanMutation = useMutation({
    mutationFn: () => replanNovel(novelId!),
    onSuccess: invalidate,
  });

  const retryPlanMutation = useMutation({
    mutationFn: () => retryNovelPlan(novelId!),
    onSuccess: invalidate,
  });

  const chatMutation = useMutation({
    mutationFn: (message: string) => chatNovel(novelId!, message),
    onSuccess: (data) => {
      setChatMessages((prev) => [...prev, { role: 'assistant', text: data.reply }]);
      invalidate();
    },
  });

  const handleChat = (e: React.FormEvent) => {
    e.preventDefault();
    const msg = chatInput.trim();
    if (!msg) return;
    setChatMessages((prev) => [...prev, { role: 'user', text: msg }]);
    setChatInput('');
    chatMutation.mutate(msg);
  };

  if (isLoading) {
    return (
      <section className="page novel-workbench">
        <p>加载中…</p>
      </section>
    );
  }

  if (isError || !novel) {
    return (
      <section className="page novel-workbench">
        <h1>小说工作台</h1>
        <p className="error-text" role="alert">
          {error
            ? `加载失败：${(error as Error).message}`
            : '小说不存在或已被删除'}
        </p>
        <div className="progress-actions">
          <Link to="/library?tab=novel" className="btn-secondary">
            我的作品
          </Link>
          <Link to="/novel" className="btn-primary">
            新建小说
          </Link>
        </div>
      </section>
    );
  }

  if (!bible) {
    return (
      <section className="page novel-workbench">
        <p>加载中…</p>
      </section>
    );
  }

  const chapters = [...novel.chapters].sort((a, b) => a.index - b.index);
  const currentChapter: NovelChapterResponse | undefined = chapters.find(
    (c) => c.index === selectedIndex,
  );
  const chapterStatusByIndex = new Map(chapters.map((ch) => [ch.index, ch.status]));

  const openChapterFromOutline = (item: NovelBibleOutlineItem) => {
    setMainTab('read');
    setSelectedIndex(item.index);
  };

  const saveWorldPatch = () => {
    patchMutation.mutate({ world: editWorld, power_system: editPower });
  };

  const handleEditWorld = (value: string) => {
    setWorldDirty(true);
    setEditWorld(value);
  };

  const handleEditPower = (value: string) => {
    setWorldDirty(true);
    setEditPower(value);
  };

  const saveCharacters = (characters: NovelBibleCharacter[]) => {
    patchMutation.mutate({ characters });
  };

  const saveItems = (items: NovelBibleItem[]) => {
    patchMutation.mutate({ items });
  };

  const saveOutline = (outline: NovelBibleOutlineItem[]) => {
    patchMutation.mutate({ outline });
  };

  const saveVolumes = (volumes: NovelBibleVolume[]) => {
    patchMutation.mutate({ volumes });
  };

  const saveForeshadowing = (foreshadowing: NovelBibleForeshadowing[]) => {
    patchMutation.mutate({ foreshadowing });
  };

  const chapterBeats = beatsForChapter(bible, selectedIndex);

  const footerMutationError = firstMutationError(
    startWritingMutation,
    continueMutation,
    patchMutation,
    approveMutation,
    rewriteMutation,
    replanMutation,
    retryPlanMutation,
    chatMutation,
  );

  return (
    <section className="page novel-workbench">
      <header className="novel-workbench-header">
        <div>
          <h1>{novel.title || '未命名小说'}</h1>
          <p className="subtitle">
            {GENRE_LABEL[novel.genre] ?? novel.genre} · {novel.synopsis || novel.premise}
          </p>
        </div>
        <StatusBadge
          status={novel.status}
          label={`${novelStatusLabel(novel.status, novel.progress)}${isBusy ? ` ${novel.progress}%` : ''}`}
        />
      </header>

      {isPlanned && (
        <div className="planned-banner">
          整本规划已生成，请审阅世界观与章节大纲。确认后选择本次撰写章数即可开始写作。
        </div>
      )}

      {isPlanning && bible.meta?.planning_state && (
        <div className="planned-banner planning-progress-banner">
          <span>{formatPlanningProgress(bible.meta)}</span>
          <div className="planning-progress-bar">
            <div className="planning-progress-fill" style={{ width: `${novel.progress}%` }} />
          </div>
          <span className="planning-progress-pct">{novel.progress}%</span>
        </div>
      )}

      {novel.error && <p className="error-text">{novel.error}</p>}
      {isFailed && (
        <div className="planned-banner error-banner">
          规划中断，已保留进度。点击下方从断点续跑（不会清空已生成大纲）。
          <button
            type="button"
            className="btn-primary btn-sm"
            disabled={retryPlanMutation.isPending}
            onClick={() => retryPlanMutation.mutate()}
          >
            {retryPlanMutation.isPending ? '提交中…' : '续跑规划'}
          </button>
        </div>
      )}
      {needsReview && (
        <p className="error-text review-banner">
          有章节未通过质量校验，请查看标黄章节；处理前无法续写。
        </p>
      )}

      <div className="novel-main-tabs">
        <button
          type="button"
          className={mainTab === 'read' ? 'active' : ''}
          onClick={() => setMainTab('read')}
        >
          正文
        </button>
        <button
          type="button"
          className={mainTab === 'world' ? 'active' : ''}
          onClick={() => setMainTab('world')}
        >
          世界观
        </button>
        <button
          type="button"
          className={mainTab === 'outline' ? 'active' : ''}
          onClick={() => setMainTab('outline')}
        >
          大纲
        </button>
      </div>

      <div className="novel-workbench-layout">
        <aside className="novel-chapters-panel">
          <div className="left-panel-toggle">
            <button
              type="button"
              className={leftPanel === 'chapters' ? 'active' : ''}
              onClick={() => setLeftPanel('chapters')}
            >
              目录
            </button>
            <button
              type="button"
              className={leftPanel === 'plan' ? 'active' : ''}
              onClick={() => setLeftPanel('plan')}
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
                  onClick={() => {
                    setSelectedIndex(ch.index);
                    setMainTab('read');
                  }}
                >
                  <span>
                    第{ch.index}章 {ch.title}
                  </span>
                  <span className={`chapter-status status-${ch.status}`}>
                    {NOVEL_STATUS_LABEL[ch.status] ?? ch.status}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {bible.meta?.total_chapters && (
            <p className="chapter-meta-hint">
              全书规划 {bible.meta.total_chapters} 章
              {bible.meta.l2_detail_to
                ? ` · 已详细化 1–${bible.meta.l2_detail_to} 章`
                : ''}
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
                      onClick={() => {
                        setMainTab(item.tab);
                        if (item.section) {
                          setPlanScrollSection(item.section);
                        }
                      }}
                    >
                      {item.label}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          )}
        </aside>

        <article className="novel-reader-panel">
          {mainTab === 'read' && (
            <>
              {currentChapter ? (
                <>
                  <h2>
                    第{currentChapter.index}章 {currentChapter.title}
                  </h2>
                  {currentChapter.status === 'completed' ||
                  currentChapter.status === 'needs_review' ? (
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
                        {parseValidationIssues(currentChapter.validation_issues).map(
                          (issue, i) => (
                            <li key={i}>{issue}</li>
                          ),
                        )}
                      </ul>
                      <button
                        type="button"
                        className="btn-primary"
                        disabled={approveMutation.isPending || rewriteMutation.isPending || isBusy}
                        onClick={() => approveMutation.mutate()}
                      >
                        {approveMutation.isPending ? '处理中…' : '确认放行本章'}
                      </button>
                      <button
                        type="button"
                        className="download-btn"
                        disabled={approveMutation.isPending || rewriteMutation.isPending || isBusy}
                        onClick={() => rewriteMutation.mutate()}
                      >
                        {rewriteMutation.isPending ? '重写中…' : '重写本章'}
                      </button>
                    </div>
                  )}
                  {currentChapter.word_count > 0 && (
                    <p className="word-count">约 {currentChapter.word_count} 字</p>
                  )}
                  {chapterBeats.length > 0 && (
                    <ChapterBeatsPanel beats={chapterBeats} />
                  )}
                </>
              ) : (
                <p className="placeholder-hint">
                  {isBusy
                    ? 'AI 正在规划与写作，请稍候…'
                    : isPlanned
                      ? '请审阅「世界观」「大纲」Tab，确认后开始写作'
                      : '请选择章节阅读'}
                </p>
              )}
            </>
          )}

          {mainTab === 'world' && (
            <WorldViewPanel
              bible={bible}
              novelSynopsis={novel.synopsis}
              editWorld={editWorld}
              editPower={editPower}
              onEditWorld={handleEditWorld}
              onEditPower={handleEditPower}
              onSaveWorld={saveWorldPatch}
              onSaveCharacters={saveCharacters}
              onSaveItems={saveItems}
              onSaveVolumes={saveVolumes}
              onSaveForeshadowing={saveForeshadowing}
              saving={patchMutation.isPending}
              readOnly={isBusy}
              scrollToSection={planScrollSection}
              onScrolled={() => setPlanScrollSection(null)}
            />
          )}

          {mainTab === 'outline' && (
            <OutlinePanel
              novelId={novelId!}
              bible={bible}
              chapterStatusByIndex={chapterStatusByIndex}
              onOpenChapter={openChapterFromOutline}
              onSaveOutline={saveOutline}
              saving={patchMutation.isPending}
              readOnly={isBusy}
            />
          )}
        </article>

        <aside className="novel-chat-panel">
          <h2>改稿对话</h2>
          <p className="placeholder-hint chat-hint">
            卷弧、伏笔等可用对话微调；世界观/人物/章纲支持表单编辑
          </p>
          <div className="chat-messages">
            {chatMessages.map((m, i) => (
              <div key={i} className={`chat-bubble chat-${m.role}`}>
                {m.text}
              </div>
            ))}
          </div>
          <form className="chat-form" onSubmit={handleChat}>
            <textarea
              rows={2}
              placeholder="例如：把第二卷冲突改成宗门内斗"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={isBusy}
            />
            <button type="submit" className="btn-primary" disabled={chatMutation.isPending || isBusy}>
              发送
            </button>
          </form>
        </aside>
      </div>

      <footer className="novel-workbench-footer">
        {footerMutationError && (
          <p className="form-error footer-mutation-error" role="alert">
            {footerMutationError}
          </p>
        )}
        {isPlanned && (
          <button
            type="button"
            className="btn-primary"
            disabled={isBusy}
            onClick={() => setShowConfirmModal(true)}
          >
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
              onChange={(e) => setWriteCount(Number(e.target.value))}
            />
            <span>章</span>
            <button
              type="button"
              className="btn-primary"
              disabled={isBusy || needsReview || continueMutation.isPending}
              onClick={() => continueMutation.mutate(writeCount)}
            >
              {continueMutation.isPending ? '提交中…' : '开始续写'}
            </button>
          </div>
        )}
        <a className="download-btn" href={exportNovelUrl(novel.id, 'md')} download>
          导出 Markdown
        </a>
        <a className="download-btn" href={exportNovelUrl(novel.id, 'txt')} download>
          导出 TXT
        </a>
        <button
          type="button"
          className="download-btn"
          disabled={isBusy || isPlanned || replanMutation.isPending}
          onClick={() => replanMutation.mutate()}
        >
          {replanMutation.isPending ? '调整中…' : '调整后续大纲'}
        </button>
      </footer>

      {showConfirmModal && (
        <div className="modal-overlay" onClick={() => setShowConfirmModal(false)}>
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
                onChange={(e) => setWriteCount(Number(e.target.value))}
              />
            </div>
            <div className="modal-actions">
              <button type="button" className="download-btn" onClick={() => setShowConfirmModal(false)}>
                取消
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={startWritingMutation.isPending}
                onClick={() => startWritingMutation.mutate(writeCount)}
              >
                {startWritingMutation.isPending ? '提交中…' : '开始写作'}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

function ChapterBeatsPanel({ beats }: { beats: NovelBibleBeat[] }) {
  return (
    <section className="chapter-beats-panel">
      <details>
        <summary>场景 Beat（{beats.length}）</summary>
        <ol className="bible-beat-list">
          {beats.map((beat) => (
            <li key={beat.index}>
              <strong>Beat {beat.index} · {beat.scene}</strong>
              {beat.goal && <p className="bible-meta">目标：{beat.goal}</p>}
              {beat.conflict && <p className="bible-meta">冲突：{beat.conflict}</p>}
              {beat.outcome && <p className="bible-meta">结果：{beat.outcome}</p>}
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
}

function WorldViewPanel({
  bible,
  novelSynopsis,
  editWorld,
  editPower,
  onEditWorld,
  onEditPower,
  onSaveWorld,
  onSaveCharacters,
  onSaveItems,
  onSaveVolumes,
  onSaveForeshadowing,
  saving,
  readOnly,
  scrollToSection,
  onScrolled,
}: {
  bible: ReturnType<typeof parseNovelBible>;
  novelSynopsis: string;
  editWorld: string;
  editPower: string;
  onEditWorld: (v: string) => void;
  onEditPower: (v: string) => void;
  onSaveWorld: () => void;
  onSaveCharacters: (c: NovelBibleCharacter[]) => void;
  onSaveItems: (items: NovelBibleItem[]) => void;
  onSaveVolumes: (volumes: NovelBibleVolume[]) => void;
  onSaveForeshadowing: (items: NovelBibleForeshadowing[]) => void;
  saving: boolean;
  readOnly: boolean;
  scrollToSection?: string | null;
  onScrolled?: () => void;
}) {
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({});

  useEffect(() => {
    if (!scrollToSection) return;
    const el = sectionRefs.current[scrollToSection];
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      onScrolled?.();
    }
  }, [scrollToSection, onScrolled]);

  const [characters, setCharacters] = useState(bible.characters);
  const [items, setItems] = useState(bible.items ?? []);
  const [volumes, setVolumes] = useState(bible.volumes ?? []);
  const [foreshadowing, setForeshadowing] = useState(bible.foreshadowing ?? []);

  useEffect(() => {
    setCharacters(bible.characters);
    setItems(bible.items ?? []);
    setVolumes(bible.volumes ?? []);
    setForeshadowing(bible.foreshadowing ?? []);
  }, [bible.characters, bible.items, bible.volumes, bible.foreshadowing]);

  return (
    <div className="novel-bible-panel">
      {novelSynopsis && (
        <section className="bible-section">
          <h3>简介</h3>
          <p className="bible-text">{novelSynopsis}</p>
        </section>
      )}

      {formatRollingSummary(bible) && (
        <section className="bible-section">
          <h3>滚动摘要</h3>
          <p className="bible-text">{formatRollingSummary(bible)}</p>
        </section>
      )}

      <section
        className="bible-section bible-editable"
        ref={(el) => {
          sectionRefs.current.world = el;
        }}
      >
        <h3>世界观</h3>
        <textarea
          rows={4}
          value={editWorld}
          onChange={(e) => onEditWorld(e.target.value)}
          disabled={readOnly}
        />
        <h3>体系 / 规则</h3>
        <textarea
          rows={3}
          value={editPower}
          onChange={(e) => onEditPower(e.target.value)}
          disabled={readOnly}
        />
        {!readOnly && (
          <button type="button" className="btn-primary btn-sm" disabled={saving} onClick={onSaveWorld}>
            {saving ? '保存中…' : '保存世界观'}
          </button>
        )}
      </section>

      <section
        className="bible-section bible-editable"
        ref={(el) => {
          sectionRefs.current.characters = el;
        }}
      >
        <h3>人物</h3>
        {characters.map((char, i) => (
          <div key={i} className="bible-edit-row">
            <input
              placeholder="姓名"
              value={char.name}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...characters];
                next[i] = { ...next[i], name: e.target.value };
                setCharacters(next);
              }}
            />
            <input
              placeholder="角色"
              value={char.role ?? ''}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...characters];
                next[i] = { ...next[i], role: e.target.value };
                setCharacters(next);
              }}
            />
            <textarea
              placeholder="人设"
              rows={2}
              value={characterDescription(char)}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...characters];
                next[i] = { ...next[i], traits: e.target.value };
                setCharacters(next);
              }}
            />
          </div>
        ))}
        {!readOnly && (
          <button
            type="button"
            className="btn-primary btn-sm"
            disabled={saving}
            onClick={() => onSaveCharacters(characters)}
          >
            保存人物
          </button>
        )}
      </section>

      <section className="bible-section bible-editable">
        <h3>道具</h3>
        {items.length === 0 && <p className="placeholder-hint">暂无道具规划</p>}
        {items.map((item, i) => (
          <div key={i} className="bible-edit-row">
            <input
              placeholder="名称"
              value={item.name}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...items];
                next[i] = { ...next[i], name: e.target.value };
                setItems(next);
              }}
            />
            <textarea
              placeholder="描述"
              rows={2}
              value={item.description ?? ''}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...items];
                next[i] = { ...next[i], description: e.target.value };
                setItems(next);
              }}
            />
            <input
              placeholder="故事意义"
              value={item.significance ?? ''}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...items];
                next[i] = { ...next[i], significance: e.target.value };
                setItems(next);
              }}
            />
          </div>
        ))}
        {!readOnly && items.length > 0 && (
          <button type="button" className="btn-primary btn-sm" disabled={saving} onClick={() => onSaveItems(items)}>
            保存道具
          </button>
        )}
      </section>

      {(volumes.length > 0 || !readOnly) && (
        <section
          className="bible-section bible-editable"
          ref={(el) => {
            sectionRefs.current.volumes = el;
          }}
        >
          <h3>卷 / 弧</h3>
          {volumes.length === 0 && <p className="placeholder-hint">暂无卷弧规划</p>}
          {volumes.map((vol, i) => (
            <div key={vol.id || i} className="bible-edit-row">
              <input
                placeholder="卷标题"
                value={vol.title}
                disabled={readOnly}
                onChange={(e) => {
                  const next = [...volumes];
                  next[i] = { ...next[i], title: e.target.value };
                  setVolumes(next);
                }}
              />
              <input
                placeholder="主题"
                value={vol.theme ?? ''}
                disabled={readOnly}
                onChange={(e) => {
                  const next = [...volumes];
                  next[i] = { ...next[i], theme: e.target.value };
                  setVolumes(next);
                }}
              />
              <div className="bible-inline-range">
                <label>
                  起
                  <input
                    type="number"
                    min={1}
                    value={vol.chapter_from}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...volumes];
                      next[i] = { ...next[i], chapter_from: Number(e.target.value) };
                      setVolumes(next);
                    }}
                  />
                </label>
                <label>
                  止
                  <input
                    type="number"
                    min={1}
                    value={vol.chapter_to}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...volumes];
                      next[i] = { ...next[i], chapter_to: Number(e.target.value) };
                      setVolumes(next);
                    }}
                  />
                </label>
              </div>
              {(vol.arcs?.length ?? 0) > 0 && (
                <ul className="bible-arc-list">
                  {vol.arcs!.map((arc) => (
                    <li key={arc.id}>
                      {arc.title}（第{arc.chapter_from}–{arc.chapter_to}章）
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
          {!readOnly && volumes.length > 0 && (
            <button type="button" className="btn-primary btn-sm" disabled={saving} onClick={() => onSaveVolumes(volumes)}>
              {saving ? '保存中…' : '保存卷弧'}
            </button>
          )}
        </section>
      )}

      {(foreshadowing.length > 0 || !readOnly) && (
        <section className="bible-section bible-editable">
          <h3>伏笔</h3>
          {foreshadowing.length === 0 && <p className="placeholder-hint">暂无伏笔规划</p>}
          {foreshadowing.map((fs, i) => (
            <div key={fs.id || i} className="bible-edit-row">
              <textarea
                placeholder="伏笔内容"
                rows={2}
                value={fs.content}
                disabled={readOnly}
                onChange={(e) => {
                  const next = [...foreshadowing];
                  next[i] = { ...next[i], content: e.target.value };
                  setForeshadowing(next);
                }}
              />
              <div className="bible-inline-range">
                <label>
                  埋设
                  <input
                    type="number"
                    min={1}
                    value={fs.plant_chapter}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...foreshadowing];
                      next[i] = { ...next[i], plant_chapter: Number(e.target.value) };
                      setForeshadowing(next);
                    }}
                  />
                </label>
                <label>
                  回收
                  <input
                    type="number"
                    min={1}
                    value={fs.resolve_chapter}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...foreshadowing];
                      next[i] = { ...next[i], resolve_chapter: Number(e.target.value) };
                      setForeshadowing(next);
                    }}
                  />
                </label>
                <label>
                  状态
                  <select
                    value={fs.status ?? 'planned'}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...foreshadowing];
                      next[i] = { ...next[i], status: e.target.value };
                      setForeshadowing(next);
                    }}
                  >
                    <option value="planned">待埋设</option>
                    <option value="planted">已埋设</option>
                    <option value="resolved">已回收</option>
                  </select>
                </label>
              </div>
            </div>
          ))}
          {!readOnly && foreshadowing.length > 0 && (
            <button
              type="button"
              className="btn-primary btn-sm"
              disabled={saving}
              onClick={() => onSaveForeshadowing(foreshadowing)}
            >
              {saving ? '保存中…' : '保存伏笔'}
            </button>
          )}
        </section>
      )}
    </div>
  );
}

export default NovelWorkbenchPage;
