/**
 * @author zhangzhihao
 */
import { useState } from 'react';

type LoadableImageProps = {
  src: string;
  alt: string;
  className?: string;
  placeholderClassName?: string;
  errorLabel?: string;
};

type LoadableVideoProps = {
  src: string;
  className?: string;
  placeholderClassName?: string;
  errorLabel?: string;
  controls?: boolean;
};

export function LoadableImage({
  src,
  alt,
  className,
  placeholderClassName = 'media-load-error',
  errorLabel = '图片加载失败',
}: LoadableImageProps) {
  const [failed, setFailed] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  if (failed) {
    return (
      <div className={placeholderClassName} role="alert">
        <span>{errorLabel}</span>
        <button
          type="button"
          className="media-retry-btn"
          onClick={() => {
            setFailed(false);
            setRetryKey((k) => k + 1);
          }}
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <img
      key={retryKey}
      src={src}
      alt={alt}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}

export function LoadableVideo({
  src,
  className,
  placeholderClassName = 'media-load-error',
  errorLabel = '视频加载失败',
  controls = true,
}: LoadableVideoProps) {
  const [failed, setFailed] = useState(false);
  const [retryKey, setRetryKey] = useState(0);

  if (failed) {
    return (
      <div className={placeholderClassName} role="alert">
        <span>{errorLabel}</span>
        <button
          type="button"
          className="media-retry-btn"
          onClick={() => {
            setFailed(false);
            setRetryKey((k) => k + 1);
          }}
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <video
      key={retryKey}
      controls={controls}
      className={className}
      src={src}
      onError={() => setFailed(true)}
    >
      您的浏览器不支持视频播放
    </video>
  );
}
