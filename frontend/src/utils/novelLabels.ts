/**
 * @author zhangzhihao
 */

export const NOVEL_STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  planning: '规划中',
  planned: '待确认大纲',
  writing: '写作中',
  completed: '已完成',
  failed: '失败',
  review_required: '待复核',
  needs_review: '待复核',
};

/** completed 且 progress<100 表示本批写完、全书未完结，区别于「已完成」。 */
export function novelStatusLabel(status: string, progress?: number): string {
  if (status === 'completed' && progress != null && progress < 100) {
    return `连载中 ${progress}%`;
  }
  return NOVEL_STATUS_LABEL[status] ?? status;
}

export const GENRE_LABEL: Record<string, string> = {
  xuanhuan: '玄幻',
  dushi: '都市',
  xuanyi: '悬疑',
  tianai: '甜宠',
  kehuan: '科幻',
};
