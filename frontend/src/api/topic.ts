/* ==============================================================
 * 题目详情页 API
 *
 * 由于 Physics / Math 分表存储，所有 API 都需要指定 subject 参数。
 * ============================================================== */

import request from './request'
import type { TopicDetailData, Subject } from '@/types'

/**
 * 获取某个主题的详细信息 + 所有题目
 * @param subject "physics" 或 "math"
 * @param topicId 如 "P1.1" 或 "M1.1"
 */
export function getTopicDetail(subject: Subject, topicId: string): Promise<TopicDetailData> {
  return request.get(`/subject/${subject}/topics/${topicId}`)
}
