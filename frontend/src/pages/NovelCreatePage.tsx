/**
 * @author zhangzhihao
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { createNovel, fetchHealth } from '../api/client';

const GENRE_OPTIONS = [
  { value: 'xuanhuan', label: '玄幻' },
  { value: 'dushi', label: '都市' },
  { value: 'xuanyi', label: '悬疑' },
  { value: 'tianai', label: '甜宠' },
  { value: 'kehuan', label: '科幻' },
];

const PREMISE_MAX = 500;

function NovelCreatePage() {
  const navigate = useNavigate();
  const [premise, setPremise] = useState('');
  const [genre, setGenre] = useState('xuanhuan');
  const [targetChapters, setTargetChapters] = useState<string>('');
  const [showEmptyHint, setShowEmptyHint] = useState(false);

  const {
    data: health,
    isError: healthError,
    error: healthFetchError,
  } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: createNovel,
    onSuccess: (novel) => {
      navigate(`/novel/${novel.id}`);
    },
  });

  const premiseTrimmed = premise.trim();
  const premiseLen = premise.length;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!premiseTrimmed) {
      setShowEmptyHint(true);
      return;
    }
    setShowEmptyHint(false);
    const parsedTarget = targetChapters.trim() ? Number(targetChapters) : undefined;
    createMutation.mutate({
      premise: premiseTrimmed,
      genre,
      target_chapters: parsedTarget,
    });
  };

  return (
    <section className="page novel-create-page">
      <h1>一句话，开启长篇小说</h1>
      <p className="subtitle">
        AI 将生成整本小说的世界观、人物、道具、卷弧、伏笔与章节大纲；确认规划后再选择撰写章数
      </p>

      {health && (
        <p className="health-badge" data-status={health.status}>
          后端已连接
        </p>
      )}
      {healthError && (
        <p className="form-error health-offline" role="alert">
          无法连接后端：{(healthFetchError as Error)?.message ?? '请确认 API 已启动'}
        </p>
      )}

      <form className="creation-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label htmlFor="genre">题材</label>
          <select
            id="genre"
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
          >
            {GENRE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <label htmlFor="targetChapters">目标章数（8–10000，可留空；AI 可在目标±200 内定最终章数）</label>
          <input
            id="targetChapters"
            type="number"
            min={8}
            max={10000}
            placeholder="留空由 AI 建议"
            value={targetChapters}
            onChange={(e) => setTargetChapters(e.target.value)}
          />
        </div>

        <label htmlFor="premise">你的创意</label>
        <textarea
          id="premise"
          rows={5}
          maxLength={PREMISE_MAX}
          placeholder="例如：废柴少年偶得上古传承，踏上修仙之路……"
          value={premise}
          onChange={(e) => {
            setPremise(e.target.value);
            if (e.target.value.trim()) setShowEmptyHint(false);
          }}
        />
        <p className="char-count">
          {premiseLen}/{PREMISE_MAX}
        </p>
        {showEmptyHint && !premiseTrimmed && (
          <p className="form-hint form-error" role="alert">
            请先输入创意描述再开始规划
          </p>
        )}

        <button
          type="submit"
          className="btn-primary"
          disabled={createMutation.isPending || healthError || !premiseTrimmed}
        >
          {createMutation.isPending ? '提交中…' : '生成整本规划'}
        </button>
        {createMutation.isError && (
          <p className="form-error" role="alert">
            创建失败：{(createMutation.error as Error)?.message ?? '请稍后重试'}
          </p>
        )}
      </form>
    </section>
  );
}

export default NovelCreatePage;
