/* ==============================================================
 * Syllabus（大纲）相关 API
 *
 * 这层叫"API 封装层"——把"请求什么地址"的细节藏在这里，
 * 页面组件只管调用 getSyllabus()，不用关心它到底 GET 了哪个 URL。
 * ============================================================== */

import request from './request'
import type { Topic, GroupedTopics } from '@/types'

/** 获取所有 syllabus 主题（扁平列表） */
export function getSyllabus(hasQuestions?: boolean): Promise<Topic[]> {
  const params = hasQuestions ? { has_questions: '1' } : undefined
  return request.get('/topics', { params })
}

/** 获取按前缀分组后的 syllabus */
export function getGroupedSyllabus(hasQuestions?: boolean): Promise<GroupedTopics> {
  const params = hasQuestions ? { has_questions: '1' } : undefined
  return request.get('/topics/grouped', { params })
}
