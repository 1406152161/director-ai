/**
 * @author zhangzhihao
 */
import { memo, type FormEvent } from 'react';

export type ChatMessage = { role: 'user' | 'assistant'; text: string };

export type NovelChatPanelProps = {
  messages: ChatMessage[];
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
  isBusy: boolean;
  chatPending: boolean;
};

export const NovelChatPanel = memo(function NovelChatPanel({
  messages,
  input,
  onInputChange,
  onSubmit,
  isBusy,
  chatPending,
}: NovelChatPanelProps) {
  return (
    <aside className="novel-chat-panel">
      <h2>改稿对话</h2>
      <p className="placeholder-hint chat-hint">
        卷弧、伏笔等可用对话微调；世界观/人物/章纲支持表单编辑
      </p>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-${m.role}`}>
            {m.text}
          </div>
        ))}
      </div>
      <form className="chat-form" onSubmit={onSubmit}>
        <textarea
          rows={2}
          placeholder="例如：把第二卷冲突改成宗门内斗"
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          disabled={isBusy}
        />
        <button type="submit" className="btn-primary" disabled={chatPending || isBusy}>
          发送
        </button>
      </form>
    </aside>
  );
});
