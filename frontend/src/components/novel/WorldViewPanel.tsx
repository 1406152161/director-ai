/**
 * @author zhangzhihao
 */
import { memo, useEffect, useRef } from 'react';
import {
  formatRollingSummary,
  type NovelBible,
  type NovelBibleCharacter,
  type NovelBibleForeshadowing,
  type NovelBibleItem,
  type NovelBibleVolume,
} from '../../utils/novelBible';
import { BibleCharacterEditor } from './BibleCharacterEditor';
import { BibleItemsEditor } from './BibleItemsEditor';
import { BibleVolumeEditor } from './BibleVolumeEditor';
import { BibleWorldEditor } from './BibleWorldEditor';

export type WorldViewPanelProps = {
  bible: NovelBible;
  novelSynopsis: string;
  worldSaveVersion: number;
  onSaveWorld: (patch: { world: string; power_system: string }) => void;
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
  worldSaveVersion,
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

      <BibleWorldEditor
        world={bible.world}
        powerSystem={bible.power_system ?? ''}
        saveVersion={worldSaveVersion}
        onSave={onSaveWorld}
        saving={saving}
        readOnly={readOnly}
        sectionRef={(el) => {
          sectionRefs.current.world = el;
        }}
      />

      <BibleCharacterEditor
        characters={bible.characters}
        onSave={onSaveCharacters}
        saving={saving}
        readOnly={readOnly}
        sectionRef={(el) => {
          sectionRefs.current.characters = el;
        }}
      />

      <BibleItemsEditor
        items={bible.items ?? []}
        onSave={onSaveItems}
        saving={saving}
        readOnly={readOnly}
      />

      <BibleVolumeEditor
        volumes={bible.volumes ?? []}
        foreshadowing={bible.foreshadowing ?? []}
        onSaveVolumes={onSaveVolumes}
        onSaveForeshadowing={onSaveForeshadowing}
        saving={saving}
        readOnly={readOnly}
        volumesSectionRef={(el) => {
          sectionRefs.current.volumes = el;
        }}
      />
    </div>
  );
});
