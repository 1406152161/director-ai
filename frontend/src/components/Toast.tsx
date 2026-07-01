/**
 * @author zhangzhihao
 */
import { useToastStore, type ToastType } from '../store/useToastStore';
import './Toast.css';

const TYPE_LABEL: Record<ToastType, string> = {
  error: '错误',
  success: '成功',
  warning: '警告',
  info: '提示',
};

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const dismissToast = useToastStore((s) => s.dismissToast);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast-${toast.type}`} role="alert">
          <span className="toast-type">{TYPE_LABEL[toast.type]}</span>
          <span className="toast-message">{toast.message}</span>
          <button
            type="button"
            className="toast-close"
            aria-label="关闭"
            onClick={() => dismissToast(toast.id)}
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
