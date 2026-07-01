/**
 * @author zhangzhihao
 */
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { fetchArticle } from '../api/client';
import { ContentSkeleton } from '../components/Skeleton';

function ArticlePreviewPage() {
  const { articleId } = useParams<{ articleId: string }>();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['article', articleId],
    queryFn: () => fetchArticle(articleId!),
    enabled: Boolean(articleId),
  });

  if (isLoading) {
    return (
      <section className="page article-preview-page">
        <ContentSkeleton />
      </section>
    );
  }

  if (isError) {
    return (
      <section className="page article-preview-page">
        <h1>图文预览</h1>
        <p className="error-text" role="alert">
          加载失败：{(error as Error)?.message ?? '请稍后重试'}
        </p>
        <div className="progress-actions">
          <Link to="/library?tab=article" className="btn-secondary">
            我的作品
          </Link>
        </div>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="page article-preview-page">
        <p className="empty-state">图文不存在或已被删除</p>
      </section>
    );
  }

  return (
    <section className="page article-preview-page">
      <header className="article-preview-header">
        <h1>{data.title}</h1>
        <p className="subtitle">
          状态：{data.status === 'preview' ? '预览占位' : data.status}
        </p>
      </header>
      <pre className="article-md-preview">{data.body_md}</pre>
      <div className="progress-actions">
        <Link to="/article" className="btn-secondary">
          再创作
        </Link>
        <Link to="/library?tab=article" className="btn-secondary">
          我的作品
        </Link>
      </div>
    </section>
  );
}

export default ArticlePreviewPage;
