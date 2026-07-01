/**
 * @author zhangzhihao
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { useCallback, useEffect, useState } from 'react';
import {
  approveNovelChapter,
  chatNovel,
  continueNovel,
  fetchNovel,
  patchNovelBible,
  replanNovel,
  retryNovelPlan,
  rewriteNovelChapter,
  startNovelWriting,
  type NovelChapterResponse,
} from '../api/client';
import { ChapterList, type MainTab, type LeftPanelMode } from '../components/novel/ChapterList';
import { ChapterReader } from '../components/novel/ChapterReader';
import { NovelChatPanel } from '../components/novel/NovelChatPanel';
import { NovelWorkbenchFooter } from '../components/novel/NovelWorkbenchFooter';
import { OutlinePanel } from '../components/novel/OutlinePanel';
import { NovelWorkbenchHeader, PlanningProgress } from '../components/novel/PlanningProgress';
import { WorldViewPanel } from '../components/novel/WorldViewPanel';
import {
  beatsForChapter,
  parseNovelBible,
  type NovelBibleCharacter,
  type NovelBibleForeshadowing,
  type NovelBibleItem,
  type NovelBibleOutlineItem,
  type NovelBibleVolume,
} from '../utils/novelBible';
import { isTerminalProgressStatus, useProgressEvents } from '../hooks/useProgressEvents';
import { ContentSkeleton } from '../components/Skeleton';
import { useToastStore } from '../store/useToastStore';

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
  const [chapterSidebarOpen, setChapterSidebarOpen] = useState(false);
  const showToast = useToastStore((s) => s.showToast);
  const onMutationError = useCallback(
    (err: unknown) => showToast('error', (err as Error)?.message ?? '操作失败'),
    [showToast],
  );

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
    onError: onMutationError,
  });

  const continueMutation = useMutation({
    mutationFn: (count: number) => continueNovel(novelId!, count),
    onSuccess: invalidate,
    onError: onMutationError,
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
    onError: onMutationError,
  });

  const approveMutation = useMutation({
    mutationFn: () => approveNovelChapter(novelId!, selectedIndex),
    onSuccess: invalidate,
    onError: onMutationError,
  });

  const rewriteMutation = useMutation({
    mutationFn: () => rewriteNovelChapter(novelId!, selectedIndex),
    onSuccess: invalidate,
    onError: onMutationError,
  });

  const replanMutation = useMutation({
    mutationFn: () => replanNovel(novelId!),
    onSuccess: invalidate,
    onError: onMutationError,
  });

  const retryPlanMutation = useMutation({
    mutationFn: () => retryNovelPlan(novelId!),
    onSuccess: invalidate,
    onError: onMutationError,
  });

  const chatMutation = useMutation({
    mutationFn: (message: string) => chatNovel(novelId!, message),
    onSuccess: (data) => {
      setChatMessages((prev) => [...prev, { role: 'assistant', text: data.reply }]);
      invalidate();
    },
    onError: onMutationError,
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
        <ContentSkeleton />
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
        <ContentSkeleton />
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

  const handleSelectChapter = (index: number) => {
    setSelectedIndex(index);
    setMainTab('read');
  };

  const handlePlanNavClick = (tab: MainTab, section?: string) => {
    setMainTab(tab);
    if (section) {
      setPlanScrollSection(section);
    }
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

  return (
    <section className="page novel-workbench">
      <NovelWorkbenchHeader
        title={novel.title}
        genre={novel.genre}
        subtitle={novel.synopsis || novel.premise}
        status={novel.status}
        progress={novel.progress}
        isBusy={isBusy}
      />

      <PlanningProgress
        isPlanned={isPlanned}
        isPlanning={isPlanning}
        isFailed={isFailed}
        needsReview={needsReview}
        novelError={novel.error}
        progress={novel.progress}
        bible={bible}
        retryPlanPending={retryPlanMutation.isPending}
        onRetryPlan={() => retryPlanMutation.mutate()}
      />

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

      <div className={`novel-workbench-layout ${chapterSidebarOpen ? 'sidebar-open' : ''}`}>
        <button
          type="button"
          className="chapter-sidebar-toggle download-btn"
          onClick={() => setChapterSidebarOpen((open) => !open)}
        >
          {chapterSidebarOpen ? '收起目录' : '章节目录'}
        </button>
        <ChapterList
          chapters={chapters}
          selectedIndex={selectedIndex}
          onSelectChapter={handleSelectChapter}
          leftPanel={leftPanel}
          onLeftPanelChange={setLeftPanel}
          mainTab={mainTab}
          onPlanNavClick={handlePlanNavClick}
          bible={bible}
          isBusy={isBusy}
          isPlanned={isPlanned}
        />

        <article className="novel-reader-panel">
          {mainTab === 'read' && (
            <ChapterReader
              currentChapter={currentChapter}
              chapterBeats={chapterBeats}
              isBusy={isBusy}
              isPlanned={isPlanned}
              approvePending={approveMutation.isPending}
              rewritePending={rewriteMutation.isPending}
              onApprove={() => approveMutation.mutate()}
              onRewrite={() => rewriteMutation.mutate()}
            />
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

        <NovelChatPanel
          messages={chatMessages}
          input={chatInput}
          onInputChange={setChatInput}
          onSubmit={handleChat}
          isBusy={isBusy}
          chatPending={chatMutation.isPending}
        />
      </div>

      <NovelWorkbenchFooter
        novelId={novel.id}
        isPlanned={isPlanned}
        isBusy={isBusy}
        needsReview={needsReview}
        writeCount={writeCount}
        onWriteCountChange={setWriteCount}
        onConfirmPlan={() => setShowConfirmModal(true)}
        onContinueWrite={() => continueMutation.mutate(writeCount)}
        onReplan={() => replanMutation.mutate()}
        continuePending={continueMutation.isPending}
        replanPending={replanMutation.isPending}
        showConfirmModal={showConfirmModal}
        onCloseConfirmModal={() => setShowConfirmModal(false)}
        onStartWriting={() => startWritingMutation.mutate(writeCount)}
        startWritingPending={startWritingMutation.isPending}
        mutations={[
          startWritingMutation,
          continueMutation,
          patchMutation,
          approveMutation,
          rewriteMutation,
          replanMutation,
          retryPlanMutation,
          chatMutation,
        ]}
      />
    </section>
  );
}

export default NovelWorkbenchPage;
