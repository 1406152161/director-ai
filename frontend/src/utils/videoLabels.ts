/**
 * @author zhangzhihao
 */

export const VIDEO_STYLE_LABEL: Record<string, string> = {
  cinematic: '电影感',
  anime: '动漫',
  documentary: '纪录片',
  vlog: 'Vlog',
};

export const VIDEO_STATUS_LABEL: Record<string, string> = {
  pending: '排队中',
  scripting: '脚本生成中',
  asseting: '资产生成中',
  imaging: '配图生成中',
  videoing: '视频生成中',
  synthesizing: '合成中',
  completed: '已完成',
  failed: '生成失败',
};

export const VIDEO_ASPECT_LABEL: Record<string, string> = {
  '16:9': '横屏 16:9',
  '9:16': '竖屏 9:16',
  '1:1': '方形 1:1',
};
