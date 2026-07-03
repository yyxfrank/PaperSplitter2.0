/* ==============================================================
 * 搜索 API
 * ============================================================== */

import request from './request'
import type { Topic } from '@/types'

/**
 * 按关键词搜索章节
 * @param keyword 用户输入的关键词
 */
export function searchTopics(keyword: string): Promise<Topic[]> {
  return request.get('/search', { params: { q: keyword } })
}
