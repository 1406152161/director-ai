/**
 * @author zhangzhihao
 */
import { useMutation } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { createArticle, fetchHealth } from '../api/client';
import { useQuery } from '@tanstack/react-query';

const PLATFORMS = [
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'wechat', label: '公众号' },
  { value: 'weibo', label: '微博' },
  { value: 'general', label: '通用' },
];

function ArticleCreatePage() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('xiaohongshu');
  const [tone, setTone] = useState('friendly');

  const { data: health, isError: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    retry: 1,
  });

  const createMutation = useMutation({
    mutationFn: () => createArticle({ topic: topic.trim(), platform, tone }),
    onSuccess: (article) => navigate(`/article/${article.id}`),
  });

  const topicTrimmed = topic.trim();

  return (
    <section className="page create-page">
      <h1>图文创作</h1>
      <p className="subtitle">输入主题，生成平台化图文预览（完整 Pipeline 后续接入）</p>

      {healthError && (
        <p className="form-error" role="alert">
          无法连接后端 API，请确认服务已启动。
        </p>
      )}
      {health && health.status !== 'ok' && (
        <p className="form-error" role="alert">
          服务状态异常：{health.status}
        </p>
      )}

      <form
        className="create-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!topicTrimmed) return;
          createMutation.mutate();
        }}
      >
        <label>
          创作主题
          <textarea
            rows={4}
            placeholder="例：春季露营必备装备清单"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
        </label>
        <label>
          目标平台
          <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
            {PLATFORMS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          语气
          <select value={tone} onChange={(e) => setTone(e.target.value)}>
            <option value="friendly">轻松友好</option>
            <option value="formal">专业正式</option>
            <option value="playful">活泼种草</option>
          </select>
        </label>
        {createMutation.isError && (
          <p className="form-error" role="alert">
            {(createMutation.error as Error).message}
          </p>
        )}
        <button
          type="submit"
          className="btn-primary"
          disabled={createMutation.isPending || healthError || !topicTrimmed}
        >
          {createMutation.isPending ? '生成中…' : '生成预览'}
        </button>
      </form>

      <p className="form-hint">
        <Link to="/">返回首页</Link>
      </p>
    </section>
  );
}

export default ArticleCreatePage;
