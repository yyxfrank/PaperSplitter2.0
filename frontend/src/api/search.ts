/* ==============================================================
 * 搜索 API
 *
 * 搜索也区分学科：physics 在 syllabus_physics 中搜索，
 * math 在 syllabus_math 中搜索。
 * ============================================================== */

import request from './request'
import type { Topic, Subject } from '@/types'

/**
 * 按关键词搜索章节
 * @param keyword 用户输入的关键词
 * @param subject 学科（默认 physics），用于确定搜索哪张表
 */
export function searchTopics(keyword: string, subject: Subject = 'physics'): Promise<Topic[]> {
  return request.get(`/subject/${subject}/search`, { params: { q: keyword } })
}
