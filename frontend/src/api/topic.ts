/* ==============================================================
 * 题目详情页 API
 * ============================================================== */

import request from './request'
import type { TopicDetailData } from '@/types'

/**
 * 获取某个主题的详细信息 + 所有题目
 * @param topicId 如 "P1.1"
 */
export function getTopicDetail(topicId: string): Promise<TopicDetailData> {
  return request.get(`/topics/${topicId}`)
}
