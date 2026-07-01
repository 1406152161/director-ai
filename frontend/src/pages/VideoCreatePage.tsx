/**
 * @author zhangzhihao
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { createProject, fetchHealth } from '../api/client';
import { useAppStore } from '../store/useAppStore';

const STYLE_OPTIONS = [
  { value: 'cinematic', label: '电影感' },
  { value: 'anime', label: '动漫' },
  { value: 'documentary', label: '纪录片' },
  { value: 'vlog', label: 'Vlog' },
];

const DURATION_OPTIONS = [15, 30, 60, 120];

const ASPECT_OPTIONS = [
  { value: '16:9', label: '横屏 16:9' },
  { value: '9:16', label: '竖屏 9:16' },
  { value: '1:1', label: '方形 1:1' },
];

const STORY_MAX = 200;

function VideoCreatePage() {
  const navigate = useNavigate();
  const { draft, setDraft } = useAppStore();
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
    mutationFn: createProject,
    onSuccess: (project) => {
      navigate(`/video/progress/${project.id}`);
    },
  });

  const storyTrimmed = draft.story.trim();
  const storyLen = draft.story.length;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!storyTrimmed) {
      setShowEmptyHint(true);
      return;
    }
    setShowEmptyHint(false);
    createMutation.mutate({
      story: storyTrimmed,
      style: draft.style,
      duration: draft.duration,
      aspect_ratio: draft.aspectRatio,
    });
  };

  return (
    <section className="page home-page">
      <h1>一句话，生成完整短视频</h1>
      <p className="subtitle">输入创意，选择风格与版式，AI 导演为你完成从脚本到成片</p>

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
        <label htmlFor="story">你的创意</label>
        <textarea
          id="story"
          rows={4}
          maxLength={STORY_MAX}
          placeholder="例如：一只橘猫在雨夜穿越霓虹灯下的东京街头……"
          value={draft.story}
          onChange={(e) => {
            setDraft({ story: e.target.value });
            if (e.target.value.trim()) setShowEmptyHint(false);
          }}
        />
        <p className="char-count">
          {storyLen}/{STORY_MAX}
        </p>
        {showEmptyHint && !storyTrimmed && (
          <p className="form-hint form-error" role="alert">
            请先输入创意描述再开始创作
          </p>
        )}

        <div className="form-row">
          <label htmlFor="style">视觉风格</label>
          <select
            id="style"
            value={draft.style}
            onChange={(e) => setDraft({ style: e.target.value })}
          >
            {STYLE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <label htmlFor="duration">目标时长</label>
          <select
            id="duration"
            value={draft.duration}
            onChange={(e) => setDraft({ duration: Number(e.target.value) })}
          >
            {DURATION_OPTIONS.map((d) => (
              <option key={d} value={d}>
                {d} 秒
              </option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <label htmlFor="aspect">版式</label>
          <select
            id="aspect"
            value={draft.aspectRatio}
            onChange={(e) => setDraft({ aspectRatio: e.target.value })}
          >
            {ASPECT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <button
          type="submit"
          className="btn-primary"
          disabled={createMutation.isPending || healthError || !storyTrimmed}
        >
          {createMutation.isPending ? '提交中…' : '开始创作'}
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

export default VideoCreatePage;
