/**
 * @author zhangzhihao
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useEffect, useRef, useState } from 'react';
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
  type NovelResponse,
} from '../api/client';
import type { MainTab, LeftPanelMode } from '../components/novel/ChapterList';
import {
  beatsForChapter,
  parseNovelBible,
  type NovelBible,
  type NovelBibleCharacter,
  type NovelBibleForeshadowing,
  type NovelBibleItem,
  type NovelBibleOutlineItem,
  type NovelBibleVolume,
} from '../utils/novelBible';
import { isTerminalProgressStatus, useProgressEvents } from './useProgressEvents';
import { isTerminalStatus } from '../utils/workStatus';
import { useToastStore } from '../store/useToastStore';

export function useNovelWorkbench(novelId: string | undefined) {
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
  const [worldSaveVersion, setWorldSaveVersion] = useState(0);
  const [sseConnected, setSseConnected] = useState(false);
  const [chapterSidebarOpen, setChapterSidebarOpen] = useState(false);
  const initialSelectedRef = useRef(false);
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
      if (query.state.status === 'error') return 10000;
      const status = query.state.data?.status;
      if (status && isTerminalStatus(status)) return false;
      return 3000;
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
    if (initialSelectedRef.current || !novel?.chapters?.length) return;
    const lastCompleted = [...novel.chapters]
      .filter((c) => c.status === 'completed')
      .sort((a, b) => b.index - a.index)[0];
    if (lastCompleted) {
      setSelectedIndex(lastCompleted.index);
      initialSelectedRef.current = true;
    }
  }, [novel?.chapters]);

  useEffect(() => {
    if (isPlanned) {
      setMainTab('outline');
      setLeftPanel('plan');
    }
  }, [isPlanned]);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['novel', novelId] });

  const startWritingMutation = useMutation({
    mutationFn: (count: number) => startNovelWriting(novelId!, count),
    onSuccess: () => {
      setShowConfirmModal(false);
      showToast('success', '已开始写作');
      invalidate();
    },
    onError: onMutationError,
  });

  const continueMutation = useMutation({
    mutationFn: (count: number) => continueNovel(novelId!, count),
    onSuccess: () => {
      showToast('success', '续写任务已提交');
      invalidate();
    },
    onError: onMutationError,
  });

  const patchMutation = useMutation({
    mutationFn: (patch: Parameters<typeof patchNovelBible>[1]) =>
      patchNovelBible(novelId!, patch),
    onSuccess: (_data, patch) => {
      if (patch.world !== undefined || patch.power_system !== undefined) {
        setWorldSaveVersion((v) => v + 1);
      }
      showToast('success', '已保存');
      invalidate();
    },
    onError: onMutationError,
  });

  const approveMutation = useMutation({
    mutationFn: () => approveNovelChapter(novelId!, selectedIndex),
    onSuccess: () => {
      showToast('success', '章节已通过');
      invalidate();
    },
    onError: onMutationError,
  });

  const rewriteMutation = useMutation({
    mutationFn: () => rewriteNovelChapter(novelId!, selectedIndex),
    onSuccess: () => {
      showToast('success', '重写任务已提交');
      invalidate();
    },
    onError: onMutationError,
  });

  const replanMutation = useMutation({
    mutationFn: () => replanNovel(novelId!),
    onSuccess: () => {
      showToast('success', '大纲调整已提交');
      invalidate();
    },
    onError: onMutationError,
  });

  const retryPlanMutation = useMutation({
    mutationFn: () => retryNovelPlan(novelId!),
    onSuccess: () => {
      showToast('success', '规划续跑已提交');
      invalidate();
    },
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

  const chapters = novel ? [...novel.chapters].sort((a, b) => a.index - b.index) : [];
  const currentChapter: NovelChapterResponse | undefined = chapters.find(
    (c) => c.index === selectedIndex,
  );
  const chapterStatusByIndex = new Map(chapters.map((ch) => [ch.index, ch.status]));
  const chapterBeats = bible ? beatsForChapter(bible, selectedIndex) : [];

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

  return {
    novel: novel as NovelResponse | undefined,
    bible: bible as NovelBible | null,
    isLoading,
    isError,
    error,
    selectedIndex,
    mainTab,
    setMainTab,
    leftPanel,
    setLeftPanel,
    planScrollSection,
    setPlanScrollSection,
    chatInput,
    setChatInput,
    chatMessages,
    writeCount,
    setWriteCount,
    showConfirmModal,
    setShowConfirmModal,
    worldSaveVersion,
    chapterSidebarOpen,
    setChapterSidebarOpen,
    isPlanned,
    isFailed,
    isPlanning,
    isBusy,
    needsReview,
    chapters,
    currentChapter,
    chapterStatusByIndex,
    chapterBeats,
    openChapterFromOutline,
    handleSelectChapter,
    handlePlanNavClick,
    handleChat,
    saveWorldPatch: (patch: { world: string; power_system: string }) => patchMutation.mutate(patch),
    saveCharacters: (characters: NovelBibleCharacter[]) => patchMutation.mutate({ characters }),
    saveItems: (items: NovelBibleItem[]) => patchMutation.mutate({ items }),
    saveOutline: (outline: NovelBibleOutlineItem[]) => patchMutation.mutate({ outline }),
    saveVolumes: (volumes: NovelBibleVolume[]) => patchMutation.mutate({ volumes }),
    saveForeshadowing: (foreshadowing: NovelBibleForeshadowing[]) =>
      patchMutation.mutate({ foreshadowing }),
    patchMutation,
    approveMutation,
    rewriteMutation,
    replanMutation,
    retryPlanMutation,
    continueMutation,
    startWritingMutation,
    chatMutation,
  };
}
