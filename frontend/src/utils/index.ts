/* ==============================================================
 * 工具函数 —— 纯逻辑，和 Vue 无关
 * ============================================================== */

/**
 * 根据图片相对路径，拼出完整的可访问 URL
 * 原项目：Flask 通过 send_from_directory 提供 /question_images/xxx
 * 迁到 Vue 后，改为直接访问 /api/question_images/xxx
 */
export function getImageUrl(relativePath: string): string {
  return `/api/question_images/${relativePath}`
}
