/**
 * @author zhangzhihao
 */
import { memo, useEffect, useState } from 'react';
import type { NovelBibleForeshadowing, NovelBibleVolume } from '../../utils/novelBible';
import { InlineSpinner } from '../Skeleton';

export type BibleVolumeEditorProps = {
  volumes: NovelBibleVolume[];
  foreshadowing: NovelBibleForeshadowing[];
  onSaveVolumes: (volumes: NovelBibleVolume[]) => void;
  onSaveForeshadowing: (items: NovelBibleForeshadowing[]) => void;
  saving: boolean;
  readOnly: boolean;
  volumesSectionRef?: (el: HTMLElement | null) => void;
};

export const BibleVolumeEditor = memo(function BibleVolumeEditor({
  volumes: initialVolumes,
  foreshadowing: initialForeshadowing,
  onSaveVolumes,
  onSaveForeshadowing,
  saving,
  readOnly,
  volumesSectionRef,
}: BibleVolumeEditorProps) {
  const [volumes, setVolumes] = useState(initialVolumes);
  const [foreshadowing, setForeshadowing] = useState(initialForeshadowing);

  useEffect(() => {
    setVolumes(initialVolumes);
  }, [initialVolumes]);

  useEffect(() => {
    setForeshadowing(initialForeshadowing);
  }, [initialForeshadowing]);

  const showVolumes = volumes.length > 0 || !readOnly;
  const showForeshadowing = foreshadowing.length > 0 || !readOnly;

  return (
    <>
      {showVolumes && (
        <section className="bible-section bible-editable" ref={volumesSectionRef}>
          <h3>卷 / 弧</h3>
          {volumes.length === 0 && <p className="placeholder-hint">暂无卷弧规划</p>}
          {volumes.map((vol, i) => (
            <div key={vol.id || i} className="bible-edit-row">
              <input
                placeholder="卷标题"
                value={vol.title}
                disabled={readOnly}
                onChange={(e) => {
                  const next = [...volumes];
                  next[i] = { ...next[i], title: e.target.value };
                  setVolumes(next);
                }}
              />
              <input
                placeholder="主题"
                value={vol.theme ?? ''}
                disabled={readOnly}
                onChange={(e) => {
                  const next = [...volumes];
                  next[i] = { ...next[i], theme: e.target.value };
                  setVolumes(next);
                }}
              />
              <div className="bible-inline-range">
                <label>
                  起
                  <input
                    type="number"
                    min={1}
                    value={vol.chapter_from}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...volumes];
                      next[i] = { ...next[i], chapter_from: Number(e.target.value) };
                      setVolumes(next);
                    }}
                  />
                </label>
                <label>
                  止
                  <input
                    type="number"
                    min={1}
                    value={vol.chapter_to}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...volumes];
                      next[i] = { ...next[i], chapter_to: Number(e.target.value) };
                      setVolumes(next);
                    }}
                  />
                </label>
              </div>
              {(vol.arcs?.length ?? 0) > 0 && (
                <ul className="bible-arc-list">
                  {vol.arcs!.map((arc) => (
                    <li key={arc.id}>
                      {arc.title}（第{arc.chapter_from}–{arc.chapter_to}章）
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
          {!readOnly && volumes.length > 0 && (
            <button type="button" className="btn-primary btn-sm" disabled={saving} onClick={() => onSaveVolumes(volumes)}>
              {saving ? <InlineSpinner label="保存中…" /> : '保存卷弧'}
            </button>
          )}
        </section>
      )}

      {showForeshadowing && (
        <section className="bible-section bible-editable">
          <h3>伏笔</h3>
          {foreshadowing.length === 0 && <p className="placeholder-hint">暂无伏笔规划</p>}
          {foreshadowing.map((fs, i) => (
            <div key={fs.id || i} className="bible-edit-row">
              <textarea
                placeholder="伏笔内容"
                rows={2}
                value={fs.content}
                disabled={readOnly}
                onChange={(e) => {
                  const next = [...foreshadowing];
                  next[i] = { ...next[i], content: e.target.value };
                  setForeshadowing(next);
                }}
              />
              <div className="bible-inline-range">
                <label>
                  埋设
                  <input
                    type="number"
                    min={1}
                    value={fs.plant_chapter}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...foreshadowing];
                      next[i] = { ...next[i], plant_chapter: Number(e.target.value) };
                      setForeshadowing(next);
                    }}
                  />
                </label>
                <label>
                  回收
                  <input
                    type="number"
                    min={1}
                    value={fs.resolve_chapter}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...foreshadowing];
                      next[i] = { ...next[i], resolve_chapter: Number(e.target.value) };
                      setForeshadowing(next);
                    }}
                  />
                </label>
                <label>
                  状态
                  <select
                    value={fs.status ?? 'planned'}
                    disabled={readOnly}
                    onChange={(e) => {
                      const next = [...foreshadowing];
                      next[i] = { ...next[i], status: e.target.value };
                      setForeshadowing(next);
                    }}
                  >
                    <option value="planned">待埋设</option>
                    <option value="planted">已埋设</option>
                    <option value="resolved">已回收</option>
                  </select>
                </label>
              </div>
            </div>
          ))}
          {!readOnly && foreshadowing.length > 0 && (
            <button
              type="button"
              className="btn-primary btn-sm"
              disabled={saving}
              onClick={() => onSaveForeshadowing(foreshadowing)}
            >
              {saving ? <InlineSpinner label="保存中…" /> : '保存伏笔'}
            </button>
          )}
        </section>
      )}
    </>
  );
});
