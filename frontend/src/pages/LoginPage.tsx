/**
 * @author zhangzhihao
 */
import { useMutation } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { login, register } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';

function LoginPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');

  const mutation = useMutation({
    mutationFn: () =>
      mode === 'login'
        ? login({ email, password })
        : register({ email, password, display_name: displayName }),
    onSuccess: (data) => {
      setSession(data.access_token, data.user);
      navigate('/');
    },
  });

  return (
    <section className="page auth-page">
      <h1>{mode === 'login' ? '登录' : '注册'}</h1>
      <p className="subtitle">SaaS 多租户模式需在后端启用 AUTH_ENABLED=true</p>

      <form
        className="create-form"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        {mode === 'register' && (
          <label>
            昵称
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          </label>
        )}
        <label>
          邮箱
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          密码
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {mutation.isError && (
          <p className="form-error" role="alert">
            {(mutation.error as Error).message}
          </p>
        )}
        <button type="submit" className="btn-primary" disabled={mutation.isPending}>
          {mutation.isPending ? '提交中…' : mode === 'login' ? '登录' : '注册'}
        </button>
      </form>

      <p className="form-hint">
        {mode === 'login' ? (
          <>
            没有账号？{' '}
            <button type="button" className="link-btn" onClick={() => setMode('register')}>
              注册
            </button>
          </>
        ) : (
          <>
            已有账号？{' '}
            <button type="button" className="link-btn" onClick={() => setMode('login')}>
              登录
            </button>
          </>
        )}{' '}
        · <Link to="/">返回首页</Link>
      </p>
    </section>
  );
}

export default LoginPage;
