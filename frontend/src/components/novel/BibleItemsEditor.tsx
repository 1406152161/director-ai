/**
 * @author zhangzhihao
 */
import { memo, useEffect, useState } from 'react';
import type { NovelBibleItem } from '../../utils/novelBible';
import { InlineSpinner } from '../Skeleton';

export type BibleItemsEditorProps = {
  items: NovelBibleItem[];
  onSave: (items: NovelBibleItem[]) => void;
  saving: boolean;
  readOnly: boolean;
};

export const BibleItemsEditor = memo(function BibleItemsEditor({
  items: initial,
  onSave,
  saving,
  readOnly,
}: BibleItemsEditorProps) {
  const [items, setItems] = useState(initial);

  useEffect(() => {
    setItems(initial);
  }, [initial]);

  return (
    <section className="bible-section bible-editable">
      <h3>道具</h3>
      {items.length === 0 && <p className="placeholder-hint">暂无道具规划</p>}
      {items.map((item, i) => (
        <div key={i} className="bible-edit-row">
          <input
            placeholder="名称"
            value={item.name}
            disabled={readOnly}
            onChange={(e) => {
              const next = [...items];
              next[i] = { ...next[i], name: e.target.value };
              setItems(next);
            }}
          />
          <textarea
            placeholder="描述"
            rows={2}
            value={item.description ?? ''}
            disabled={readOnly}
            onChange={(e) => {
              const next = [...items];
              next[i] = { ...next[i], description: e.target.value };
              setItems(next);
            }}
          />
          <input
            placeholder="故事意义"
            value={item.significance ?? ''}
            disabled={readOnly}
            onChange={(e) => {
              const next = [...items];
              next[i] = { ...next[i], significance: e.target.value };
              setItems(next);
            }}
          />
        </div>
      ))}
      {!readOnly && items.length > 0 && (
        <button type="button" className="btn-primary btn-sm" disabled={saving} onClick={() => onSave(items)}>
          {saving ? <InlineSpinner label="保存中…" /> : '保存道具'}
        </button>
      )}
    </section>
  );
});
