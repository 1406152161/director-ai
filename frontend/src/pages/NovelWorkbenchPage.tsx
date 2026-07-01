/**
 * @author zhangzhihao
 */
import { Link, useParams } from 'react-router-dom';
import { ChapterList } from '../components/novel/ChapterList';
import { ChapterReader } from '../components/novel/ChapterReader';
import { NovelChatPanel } from '../components/novel/NovelChatPanel';
import { NovelWorkbenchFooter } from '../components/novel/NovelWorkbenchFooter';
import { OutlinePanel } from '../components/novel/OutlinePanel';
import { NovelWorkbenchHeader, PlanningProgress } from '../components/novel/PlanningProgress';
import { WorldViewPanel } from '../components/novel/WorldViewPanel';
import { ContentSkeleton } from '../components/Skeleton';
import { useNovelWorkbench } from '../hooks/useNovelWorkbench';

function NovelWorkbenchPage() {
  const { novelId } = useParams<{ novelId: string }>();
  const wb = useNovelWorkbench(novelId);

  if (wb.isLoading) {
    return (
      <section className="page novel-workbench">
        <ContentSkeleton />
      </section>
    );
  }

  if (wb.isError || !wb.novel) {
    return (
      <section className="page novel-workbench">
        <h1>小说工作台</h1>
        <p className="error-text" role="alert">
          {wb.error
            ? `加载失败：${(wb.error as Error).message}`
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

  if (!wb.bible) {
    return (
      <section className="page novel-workbench">
        <ContentSkeleton />
      </section>
    );
  }

  const { novel, bible } = wb;

  return (
    <section className="page novel-workbench">
      <NovelWorkbenchHeader
        title={novel.title}
        genre={novel.genre}
        subtitle={novel.synopsis || novel.premise}
        status={novel.status}
        progress={novel.progress}
        isBusy={wb.isBusy}
      />

      <PlanningProgress
        isPlanned={wb.isPlanned}
        isPlanning={wb.isPlanning}
        isFailed={wb.isFailed}
        needsReview={wb.needsReview}
        novelError={novel.error}
        progress={novel.progress}
        bible={bible}
        retryPlanPending={wb.retryPlanMutation.isPending}
        onRetryPlan={() => wb.retryPlanMutation.mutate()}
      />

      <div className="novel-main-tabs">
        {(['read', 'world', 'outline'] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            className={wb.mainTab === tab ? 'active' : ''}
            onClick={() => wb.setMainTab(tab)}
          >
            {tab === 'read' ? '正文' : tab === 'world' ? '世界观' : '大纲'}
          </button>
        ))}
      </div>

      <div className={`novel-workbench-layout ${wb.chapterSidebarOpen ? 'sidebar-open' : ''}`}>
        <button
          type="button"
          className="chapter-sidebar-toggle download-btn"
          onClick={() => wb.setChapterSidebarOpen((open) => !open)}
        >
          {wb.chapterSidebarOpen ? '收起目录' : '章节目录'}
        </button>
        <ChapterList
          chapters={wb.chapters}
          selectedIndex={wb.selectedIndex}
          onSelectChapter={wb.handleSelectChapter}
          leftPanel={wb.leftPanel}
          onLeftPanelChange={wb.setLeftPanel}
          mainTab={wb.mainTab}
          onPlanNavClick={wb.handlePlanNavClick}
          bible={bible}
          isBusy={wb.isBusy}
          isPlanned={wb.isPlanned}
        />

        <article className="novel-reader-panel">
          {wb.mainTab === 'read' && (
            <ChapterReader
              currentChapter={wb.currentChapter}
              chapterBeats={wb.chapterBeats}
              isBusy={wb.isBusy}
              isPlanned={wb.isPlanned}
              approvePending={wb.approveMutation.isPending}
              rewritePending={wb.rewriteMutation.isPending}
              onApprove={() => wb.approveMutation.mutate()}
              onRewrite={() => wb.rewriteMutation.mutate()}
            />
          )}

          {wb.mainTab === 'world' && (
            <WorldViewPanel
              bible={bible}
              novelSynopsis={novel.synopsis}
              worldSaveVersion={wb.worldSaveVersion}
              onSaveWorld={wb.saveWorldPatch}
              onSaveCharacters={wb.saveCharacters}
              onSaveItems={wb.saveItems}
              onSaveVolumes={wb.saveVolumes}
              onSaveForeshadowing={wb.saveForeshadowing}
              saving={wb.patchMutation.isPending}
              readOnly={wb.isBusy}
              scrollToSection={wb.planScrollSection}
              onScrolled={() => wb.setPlanScrollSection(null)}
            />
          )}

          {wb.mainTab === 'outline' && (
            <OutlinePanel
              novelId={novelId!}
              bible={bible}
              chapterStatusByIndex={wb.chapterStatusByIndex}
              onOpenChapter={wb.openChapterFromOutline}
              onSaveOutline={wb.saveOutline}
              saving={wb.patchMutation.isPending}
              readOnly={wb.isBusy}
            />
          )}
        </article>

        <NovelChatPanel
          messages={wb.chatMessages}
          input={wb.chatInput}
          onInputChange={wb.setChatInput}
          onSubmit={wb.handleChat}
          isBusy={wb.isBusy}
          chatPending={wb.chatMutation.isPending}
        />
      </div>

      <NovelWorkbenchFooter
        novelId={novel.id}
        isPlanned={wb.isPlanned}
        isBusy={wb.isBusy}
        needsReview={wb.needsReview}
        writeCount={wb.writeCount}
        onWriteCountChange={wb.setWriteCount}
        onConfirmPlan={() => wb.setShowConfirmModal(true)}
        onContinueWrite={() => wb.continueMutation.mutate(wb.writeCount)}
        onReplan={() => wb.replanMutation.mutate()}
        continuePending={wb.continueMutation.isPending}
        replanPending={wb.replanMutation.isPending}
        showConfirmModal={wb.showConfirmModal}
        onCloseConfirmModal={() => wb.setShowConfirmModal(false)}
        onStartWriting={() => wb.startWritingMutation.mutate(wb.writeCount)}
        startWritingPending={wb.startWritingMutation.isPending}
      />
    </section>
  );
}

export default NovelWorkbenchPage;
