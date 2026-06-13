/**
 * @author zhangzhihao
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import {
  chatNovel,
  continueNovel,
  exportNovelUrl,
  fetchNovel,
  type NovelChapterResponse,
} from '../api/client';

const STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  planning: '规划中',
  writing: '写作中',
  completed: '已完成',
  failed: '失败',
};

const GENRE_LABEL: Record<string, string> = {
  xuanhuan: '玄幻',
  dushi: '都市',
  xuanyi: '悬疑',
  tianai: '甜宠',
  kehuan: '科幻',
};

function NovelWorkbenchPage() {
  const { novelId } = useParams<{ novelId: string }>();
  const queryClient = useQueryClient();
  const [selectedIndex, setSelectedIndex] = useState(1);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'assistant'; text: string }[]>(
    [],
  );

  const { data: novel, isLoading } = useQuery({
    queryKey: ['novel', novelId],
    queryFn: () => fetchNovel(novelId!),
    enabled: !!novelId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && !['completed', 'failed'].includes(status) ? 2000 : false;
    },
  });

  useEffect(() => {
    if (!novel?.chapters?.length) return;
    const completed = novel.chapters.filter((c) => c.status === 'completed');
    if (completed.length > 0) {
      setSelectedIndex(completed[completed.length - 1].index);
    }
  }, [novel?.chapters, novel?.status]);

  const continueMutation = useMutation({
    mutationFn: () => continueNovel(novelId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['novel', novelId] });
    },
  });

  const chatMutation = useMutation({
    mutationFn: (message: string) => chatNovel(novelId!, message),
    onSuccess: (data) => {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', text: data.reply },
      ]);
      queryClient.invalidateQueries({ queryKey: ['novel', novelId] });
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

  if (isLoading || !novel) {
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

  const isBusy = novel.status === 'planning' || novel.status === 'writing';

  return (
    <section className="page novel-workbench">
      <header className="novel-workbench-header">
        <div>
          <h1>{novel.title || '未命名小说'}</h1>
          <p className="subtitle">
            {GENRE_LABEL[novel.genre] ?? novel.genre} · {novel.synopsis || novel.premise}
          </p>
        </div>
        <span className={`status-badge status-${novel.status}`}>
          {STATUS_LABEL[novel.status] ?? novel.status}
          {isBusy && ` ${novel.progress}%`}
        </span>
      </header>

      {novel.error && <p className="error-text">{novel.error}</p>}

      <div className="novel-workbench-layout">
        <aside className="novel-chapters-panel">
          <h2>章节目录</h2>
          <ul className="chapter-list">
            {chapters.length === 0 && <li className="chapter-empty">暂无章节</li>}
            {chapters.map((ch) => (
              <li key={ch.id}>
                <button
                  type="button"
                  className={`chapter-item ${selectedIndex === ch.index ? 'active' : ''}`}
                  onClick={() => setSelectedIndex(ch.index)}
                >
                  <span>第{ch.index}章 {ch.title}</span>
                  <span className={`chapter-status status-${ch.status}`}>
                    {STATUS_LABEL[ch.status] ?? ch.status}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <article className="novel-reader-panel">
          {currentChapter ? (
            <>
              <h2>第{currentChapter.index}章 {currentChapter.title}</h2>
              {currentChapter.status === 'completed' ? (
                <div className="novel-content">
                  {currentChapter.content.split('\n').map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              ) : (
                <p className="placeholder-hint">本章{STATUS_LABEL[currentChapter.status] ?? '生成中'}…</p>
              )}
              {currentChapter.word_count > 0 && (
                <p className="word-count">约 {currentChapter.word_count} 字</p>
              )}
            </>
          ) : (
            <p className="placeholder-hint">
              {isBusy ? 'AI 正在规划与写作，请稍候…' : '请选择章节阅读'}
            </p>
          )}
        </article>

        <aside className="novel-chat-panel">
          <h2>改稿对话</h2>
          <div className="chat-messages">
            {chatMessages.length === 0 && (
              <p className="placeholder-hint">可在此调整人设、大纲等（不自动重写已发布章节）</p>
            )}
            {chatMessages.map((m, i) => (
              <div key={i} className={`chat-bubble chat-${m.role}`}>
                {m.text}
              </div>
            ))}
          </div>
          <form className="chat-form" onSubmit={handleChat}>
            <textarea
              rows={2}
              placeholder="例如：把女主改成更主动的性格"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
            />
            <button type="submit" className="btn-primary" disabled={chatMutation.isPending}>
              发送
            </button>
          </form>
        </aside>
      </div>

      <footer className="novel-workbench-footer">
        <button
          type="button"
          className="btn-primary"
          disabled={isBusy || continueMutation.isPending}
          onClick={() => continueMutation.mutate()}
        >
          {continueMutation.isPending ? '提交中…' : '续写下一章'}
        </button>
        <a
          className="download-btn"
          href={exportNovelUrl(novel.id, 'md')}
          download
        >
          导出 Markdown
        </a>
        <a
          className="download-btn"
          href={exportNovelUrl(novel.id, 'txt')}
          download
        >
          导出 TXT
        </a>
      </footer>
    </section>
  );
}

export default NovelWorkbenchPage;
