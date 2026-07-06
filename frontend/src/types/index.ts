/* ==============================================================
 * 类型约束 —— 定义数据长什么样
 *
 * 通俗理解：给 JS 加上"语法说明书"，
 * 写代码时编辑器会提示"这个对象有哪些属性，分别是什么类型"，
 * 传错类型 IDE 会直接报红，不用等运行才发现 bug。
 * ============================================================== */

/** 学科类型：physics 或 math */
export type Subject = 'physics' | 'math'

/** syllabus_physics 表 的一条记录（有 title） */
export interface PhysicsTopic {
  topic_id: string       // 如 "P1.1"
  title: string          // 章节标题
  objectives: string     // 学习目标（可能含 HTML）
  paper_name: string | null  // 所属试卷
}

/** syllabus_math 表 的一条记录（无 title，有 chapter） */
export interface MathTopic {
  topic_id: string       // 如 "M1.1"
  chapter: string        // 章节名称，如 "M1"
  objectives: string     // 学习目标（可能含 HTML）
  paper_name: string | null  // 所属试卷
}

/** 联合类型：一个 topic 可能是 physics 或 math */
export type Topic = PhysicsTopic | MathTopic

/** questions 表 的一条记录 */
export interface Question {
  id: number
  paper_name: string
  question_number: string
  image_path: string     // 相对路径，如 "output_questions/ENGAA_2016_S1/Question_1.png"
  topic_id: string
}

/** Flask API 返回的统一结构 */
export interface ApiResponse<T> {
  code: number           // 0 成功，非 0 失败
  message: string
  data: T
}

/** 首页 syllabus 按前缀分组后的结构 */
export interface GroupedTopics {
  [prefix: string]: Topic[]   // 如 { "P": [...], "S": [...] }
}

/** 题目详情页需要的全部数据 */
export interface TopicDetailData {
  topic: Topic
  questions: Question[]
  questions_by_paper: Record<string, Question[]>
}

/** 搜索参数 */
export interface SearchParams {
  q: string
}
