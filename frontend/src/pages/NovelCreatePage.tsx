/**
 * @author zhangzhihao
 */
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { createNovel } from '../api/client';

const GENRE_OPTIONS = [
  { value: 'xuanhuan', label: '玄幻' },
  { value: 'dushi', label: '都市' },
  { value: 'xuanyi', label: '悬疑' },
  { value: 'tianai', label: '甜宠' },
  { value: 'kehuan', label: '科幻' },
];

function NovelCreatePage() {
  const navigate = useNavigate();
  const [premise, setPremise] = useState('');
  const [genre, setGenre] = useState('xuanhuan');

  const createMutation = useMutation({
    mutationFn: createNovel,
    onSuccess: (novel) => {
      navigate(`/novel/${novel.id}`);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!premise.trim()) return;
    createMutation.mutate({ premise: premise.trim(), genre });
  };

  return (
    <section className="page novel-create-page">
      <h1>一句话，开启长篇小说</h1>
      <p className="subtitle">选择题材、输入创意，AI 为你规划大纲并撰写前三章</p>

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

        <label htmlFor="premise">你的创意</label>
        <textarea
          id="premise"
          rows={5}
          maxLength={500}
          placeholder="例如：废柴少年偶得上古传承，踏上修仙之路……"
          value={premise}
          onChange={(e) => setPremise(e.target.value)}
        />

        <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
          {createMutation.isPending ? '提交中…' : '开始创作'}
        </button>
      </form>
    </section>
  );
}

export default NovelCreatePage;
