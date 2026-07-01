/**
 * @author zhangzhihao
 */
export interface NovelPlanningState {
  phase?: 'l1_skeleton' | 'l2_detail' | 'done';
  l1_done_through?: number;
  l2_done_through?: number;
  last_error?: string | null;
}

export interface NovelBibleMeta {
  total_chapters?: number;
  target_chapters_user?: number | null;
  l2_detail_to?: number;
  outline_in_db?: boolean;
  planning_state?: NovelPlanningState;
  chapter_flex_range?: [number, number];
  chapter_count_reason?: string;
  initial_write_count?: number;
  plan_mode?: 'auto' | 'review';
  rolling_summary?: {
    book?: string;
    volume?: string;
    arc?: string;
  };
}

export interface NovelBibleCharacter {
  name: string;
  role?: string;
  traits?: string;
  profile?: string;
  growth_arc?: string;
}

export interface NovelBibleArc {
  id: string;
  title: string;
  conflict?: string;
  chapter_from: number;
  chapter_to: number;
}

export interface NovelBibleVolume {
  id: string;
  title: string;
  theme?: string;
  chapter_from: number;
  chapter_to: number;
  arcs?: NovelBibleArc[];
}

export interface NovelBibleOutlineItem {
  index: number;
  title: string;
  summary: string;
  hook?: string;
  arc_id?: string;
  volume_id?: string;
}

export interface NovelBibleForeshadowing {
  id: string;
  content: string;
  plant_chapter: number;
  resolve_chapter: number;
  status?: string;
  linked_characters?: string[];
  linked_items?: string[];
}

export interface NovelBibleBeat {
  index: number;
  scene: string;
  goal?: string;
  conflict?: string;
  outcome?: string;
}

export interface NovelBibleItem {
  id?: string;
  name: string;
  description?: string;
  significance?: string;
  first_chapter?: number;
}

export interface NovelBible {
  meta?: NovelBibleMeta;
  world: string;
  power_system?: string;
  items?: NovelBibleItem[];
  facts: string[];
  characters: NovelBibleCharacter[];
  volumes?: NovelBibleVolume[];
  outline: NovelBibleOutlineItem[];
  foreshadowing?: NovelBibleForeshadowing[];
  beats?: Record<string, NovelBibleBeat[]>;
}

export function parseNovelBible(bibleJson: string): NovelBible {
  if (!bibleJson || bibleJson.trim() === '' || bibleJson.trim() === '{}') {
    return { world: '', facts: [], characters: [], outline: [], items: [] };
  }
  try {
    const raw = JSON.parse(bibleJson) as Partial<NovelBible>;
    return {
      meta: raw.meta,
      world: raw.world ?? '',
      power_system: raw.power_system ?? '',
      items: Array.isArray(raw.items) ? raw.items : [],
      facts: Array.isArray(raw.facts) ? raw.facts : [],
      characters: Array.isArray(raw.characters) ? raw.characters : [],
      volumes: Array.isArray(raw.volumes) ? raw.volumes : [],
      outline: Array.isArray(raw.outline) ? raw.outline : [],
      foreshadowing: Array.isArray(raw.foreshadowing) ? raw.foreshadowing : [],
      beats: raw.beats ?? {},
    };
  } catch {
    return { world: '', facts: [], characters: [], outline: [], items: [] };
  }
}

export function characterDescription(char: NovelBibleCharacter): string {
  return char.traits || char.profile || '';
}

export function beatsForChapter(bible: NovelBible, chapterIndex: number): NovelBibleBeat[] {
  const beats = bible.beats ?? {};
  return beats[String(chapterIndex)] ?? [];
}

export function foreshadowStatusLabel(status?: string): string {
  const map: Record<string, string> = {
    planned: '待埋设',
    planted: '已埋设',
    resolved: '已回收',
  };
  return map[status ?? ''] ?? status ?? '未知';
}

export function formatPlanningProgress(meta?: NovelBibleMeta): string {
  const state = meta?.planning_state;
  const total = meta?.total_chapters ?? 0;
  if (!state || !total) {
    return '规划进行中…';
  }
  if (state.phase === 'l1_skeleton') {
    return `L1 骨架 ${state.l1_done_through ?? 0}/${total} 章`;
  }
  if (state.phase === 'l2_detail') {
    const l2To = Math.min(meta?.l2_detail_to ?? 60, total);
    return `L2 详细 ${state.l2_done_through ?? 0}/${l2To} 章`;
  }
  return '规划收尾中…';
}

export function formatRollingSummary(bible: NovelBible): string {
  const rs = bible.meta?.rolling_summary;
  if (!rs) return '';
  const parts: string[] = [];
  if (rs.book) parts.push(`全书：${rs.book}`);
  if (rs.volume) parts.push(`当前卷：${rs.volume}`);
  if (rs.arc) parts.push(`当前弧：${rs.arc}`);
  return parts.join('\n');
}
