/**
 * @author zhangzhihao
 */
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { fetchArticle } from '../api/client';
import { QueryState } from '../components/QueryState';

function ArticlePreviewPage() {
  const { articleId } = useParams<{ articleId: string }>();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['article', articleId],
    queryFn: () => fetchArticle(articleId!),
    enabled: Boolean(articleId),
  });

  return (
    <section className="page article-preview-page">
      <QueryState isLoading={isLoading} isError={isError} error={error} loadingText="加载图文…">
        {data && (
          <>
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
          </>
        )}
      </QueryState>
    </section>
  );
}

export default ArticlePreviewPage;
