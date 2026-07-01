/**
 * @author zhangzhihao
 */
import { memo, useEffect, useState } from 'react';
import { InlineSpinner } from '../Skeleton';

export type BibleWorldEditorProps = {
  world: string;
  powerSystem: string;
  /** 父级保存成功后递增，用于清除 dirty 并同步 bible。 */
  saveVersion: number;
  onSave: (patch: { world: string; power_system: string }) => void;
  saving: boolean;
  readOnly: boolean;
  sectionRef?: (el: HTMLElement | null) => void;
};

export const BibleWorldEditor = memo(function BibleWorldEditor({
  world,
  powerSystem,
  saveVersion,
  onSave,
  saving,
  readOnly,
  sectionRef,
}: BibleWorldEditorProps) {
  const [editWorld, setEditWorld] = useState(world);
  const [editPower, setEditPower] = useState(powerSystem);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (dirty) return;
    setEditWorld(world);
    setEditPower(powerSystem);
  }, [world, powerSystem, dirty]);

  useEffect(() => {
    setDirty(false);
    setEditWorld(world);
    setEditPower(powerSystem);
  }, [saveVersion, world, powerSystem]);

  const handleSave = () => {
    onSave({ world: editWorld, power_system: editPower });
  };

  return (
    <section
      className="bible-section bible-editable"
      ref={sectionRef}
    >
      <h3>世界观</h3>
      <textarea
        rows={4}
        value={editWorld}
        onChange={(e) => {
          setDirty(true);
          setEditWorld(e.target.value);
        }}
        disabled={readOnly}
      />
      <h3>体系 / 规则</h3>
      <textarea
        rows={3}
        value={editPower}
        onChange={(e) => {
          setDirty(true);
          setEditPower(e.target.value);
        }}
        disabled={readOnly}
      />
      {!readOnly && (
        <button type="button" className="btn-primary btn-sm" disabled={saving} onClick={handleSave}>
          {saving ? <InlineSpinner label="保存中…" /> : '保存世界观'}
        </button>
      )}
    </section>
  );
});
