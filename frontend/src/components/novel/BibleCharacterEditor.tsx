/**
 * @author zhangzhihao
 */
import { memo, useEffect, useState } from 'react';
import { characterDescription, type NovelBibleCharacter } from '../../utils/novelBible';
import { InlineSpinner } from '../Skeleton';

export type BibleCharacterEditorProps = {
  characters: NovelBibleCharacter[];
  onSave: (characters: NovelBibleCharacter[]) => void;
  saving: boolean;
  readOnly: boolean;
  sectionRef?: (el: HTMLElement | null) => void;
};

export const BibleCharacterEditor = memo(function BibleCharacterEditor({
  characters: initial,
  onSave,
  saving,
  readOnly,
  sectionRef,
}: BibleCharacterEditorProps) {
  const [characters, setCharacters] = useState(initial);

  useEffect(() => {
    setCharacters(initial);
  }, [initial]);

  return (
    <section className="bible-section bible-editable" ref={sectionRef}>
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
          onClick={() => onSave(characters)}
        >
          {saving ? <InlineSpinner label="保存中…" /> : '保存人物'}
        </button>
      )}
    </section>
  );
});
