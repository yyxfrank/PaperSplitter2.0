/* ==============================================================
 * Syllabus（大纲）相关 API
 *
 * 由于 Physics / Math 分表存储，所有 API 都需要指定 subject 参数。
 * ============================================================== */

import request from './request'
import type { Topic, GroupedTopics, Subject } from '@/types'

/**
 * 获取指定学科的所有 syllabus 主题（扁平列表）
 * @param subject "physics" 或 "math"
 */
export function getSyllabus(subject: Subject, hasQuestions?: boolean): Promise<Topic[]> {
  const params: Record<string, string> = {}
  if (hasQuestions) params.has_questions = '1'
  return request.get(`/subject/${subject}/topics`, { params })
}

/**
 * 获取指定学科按前缀分组后的 syllabus
 * @param subject "physics" 或 "math"
 */
export function getGroupedSyllabus(subject: Subject, hasQuestions?: boolean): Promise<GroupedTopics> {
  const params: Record<string, string> = {}
  if (hasQuestions) params.has_questions = '1'
  return request.get(`/subject/${subject}/topics/grouped`, { params })
}
