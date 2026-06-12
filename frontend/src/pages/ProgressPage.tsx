/**
 * @author zhangzhihao
 */
import { useParams } from 'react-router-dom';

const PIPELINE_STEPS = [
  { key: 'script', label: '脚本 & 分镜' },
  { key: 'asset', label: '资产生成' },
  { key: 'keyframe', label: '关键帧' },
  { key: 'video', label: '视频片段' },
  { key: 'tts', label: '配音' },
  { key: 'compose', label: '合成成片' },
];

function ProgressPage() {
  const { projectId } = useParams<{ projectId: string }>();

  return (
    <section className="page progress-page">
      <h1>创作进度</h1>
      <p className="project-id">项目 ID: {projectId}</p>
      <p className="placeholder-hint">M0 占位页 — M2 接入 SSE/WebSocket 实时进度</p>

      <ol className="pipeline-steps">
        {PIPELINE_STEPS.map((step) => (
          <li key={step.key} className="pipeline-step">
            <span className="step-label">{step.label}</span>
            <span className="step-status">等待中</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default ProgressPage;
