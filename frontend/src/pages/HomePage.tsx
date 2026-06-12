/**
 * @author zhangzhihao
 */
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
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

function HomePage() {
  const navigate = useNavigate();
  const { draft, setDraft } = useAppStore();

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      navigate(`/progress/${project.id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.story.trim()) return;
    createMutation.mutate({
      story: draft.story,
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
          后端状态: {health.status}
        </p>
      )}

      <form className="creation-form" onSubmit={handleSubmit}>
        <label htmlFor="story">你的创意</label>
        <textarea
          id="story"
          rows={4}
          maxLength={200}
          placeholder="例如：一只橘猫在雨夜穿越霓虹灯下的东京街头……"
          value={draft.story}
          onChange={(e) => setDraft({ story: e.target.value })}
        />

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

        <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
          {createMutation.isPending ? '提交中…' : '开始创作'}
        </button>
      </form>
    </section>
  );
}

export default HomePage;
