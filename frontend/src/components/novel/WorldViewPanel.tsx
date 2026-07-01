/**
 * @author zhangzhihao
 */
import { memo, useEffect, useRef, useState } from 'react';
import {
  characterDescription,
  formatRollingSummary,
  type NovelBible,
  type NovelBibleCharacter,
  type NovelBibleForeshadowing,
  type NovelBibleItem,
  type NovelBibleVolume,
} from '../../utils/novelBible';

export type WorldViewPanelProps = {
  bible: NovelBible;
  novelSynopsis: string;
  editWorld: string;
  editPower: string;
  onEditWorld: (v: string) => void;
  onEditPower: (v: string) => void;
  onSaveWorld: () => void;
  onSaveCharacters: (c: NovelBibleCharacter[]) => void;
  onSaveItems: (items: NovelBibleItem[]) => void;
  onSaveVolumes: (volumes: NovelBibleVolume[]) => void;
  onSaveForeshadowing: (items: NovelBibleForeshadowing[]) => void;
  saving: boolean;
  readOnly: boolean;
  scrollToSection?: string | null;
  onScrolled?: () => void;
};

export const WorldViewPanel = memo(function WorldViewPanel({
  bible,
  novelSynopsis,
  editWorld,
  editPower,
  onEditWorld,
  onEditPower,
  onSaveWorld,
  onSaveCharacters,
  onSaveItems,
  onSaveVolumes,
  onSaveForeshadowing,
  saving,
  readOnly,
  scrollToSection,
  onScrolled,
}: WorldViewPanelProps) {
  const sectionRefs = useRef<Record<string, HTMLElement | null>>({});

  useEffect(() => {
    if (!scrollToSection) return;
    const el = sectionRefs.current[scrollToSection];
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      onScrolled?.();
    }
  }, [scrollToSection, onScrolled]);

  const [characters, setCharacters] = useState(bible.characters);
  const [items, setItems] = useState(bible.items ?? []);
  const [volumes, setVolumes] = useState(bible.volumes ?? []);
  const [foreshadowing, setForeshadowing] = useState(bible.foreshadowing ?? []);

  useEffect(() => {
    setCharacters(bible.characters);
    setItems(bible.items ?? []);
    setVolumes(bible.volumes ?? []);
    setForeshadowing(bible.foreshadowing ?? []);
  }, [bible.characters, bible.items, bible.volumes, bible.foreshadowing]);

  return (
    <div className="novel-bible-panel">
      {novelSynopsis && (
        <section className="bible-section">
          <h3>简介</h3>
          <p className="bible-text">{novelSynopsis}</p>
        </section>
      )}

      {formatRollingSummary(bible) && (
        <section className="bible-section">
          <h3>滚动摘要</h3>
          <p className="bible-text">{formatRollingSummary(bible)}</p>
        </section>
      )}

      <section
        className="bible-section bible-editable"
        ref={(el) => {
          sectionRefs.current.world = el;
        }}
      >
        <h3>世界观</h3>
        <textarea
          rows={4}
          value={editWorld}
          onChange={(e) => onEditWorld(e.target.value)}
          disabled={readOnly}
        />
        <h3>体系 / 规则</h3>
        <textarea
          rows={3}
          value={editPower}
          onChange={(e) => onEditPower(e.target.value)}
          disabled={readOnly}
        />
        {!readOnly && (
          <button type="button" className="btn-primary btn-sm" disabled={saving} onClick={onSaveWorld}>
            {saving ? '保存中…' : '保存世界观'}
          </button>
        )}
      </section>

      <section
        className="bible-section bible-editable"
        ref={(el) => {
          sectionRefs.current.characters = el;
        }}
      >
        <h3>人物</h3>
        {characters.map((char, i) => (
          <div key={i} className="bible-edit-row">
            <input
              placeholder="姓名"
              value={char.name}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...characters];
                next[i] = { ...next[i], name: e.target.value };
                setCharacters(next);
              }}
            />
            <input
              placeholder="角色"
              value={char.role ?? ''}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...characters];
                next[i] = { ...next[i], role: e.target.value };
                setCharacters(next);
              }}
            />
            <textarea
              placeholder="人设"
              rows={2}
              value={characterDescription(char)}
              disabled={readOnly}
              onChange={(e) => {
                const next = [...characters];
                next[i] = { ...next[i], traits: e.target.value };
                setCharacters(next);
              }}
            />
          </div>
        ))}
        {!readOnly && (
          <button
            type="button"
            className="btn-primary btn-sm"
            disabled={saving}
            onClick={() => onSaveCharacters(characters)}
          >
            保存人物
          </button>
        )}
      </section>

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
          <button type="button" className="btn-primary btn-sm" disabled={saving} onClick={() => onSaveItems(items)}>
            保存道具
          </button>
        )}
      </section>

      {(volumes.length > 0 || !readOnly) && (
        <section
          className="bible-section bible-editable"
          ref={(el) => {
            sectionRefs.current.volumes = el;
          }}
        >
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
              {saving ? '保存中…' : '保存卷弧'}
            </button>
          )}
        </section>
      )}

      {(foreshadowing.length > 0 || !readOnly) && (
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
              {saving ? '保存中…' : '保存伏笔'}
            </button>
          )}
        </section>
      )}
    </div>
  );
});
