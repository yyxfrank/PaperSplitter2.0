<template>
  <div class="topic-detail">
    <el-skeleton :loading="loading" animated>
      <template #default>
        <!--
          错误状态：API 返回 404 或数据库异常
          直接用 <el-result> 显示错误信息
        -->
        <div v-if="error" class="error-state">
          <el-result status="error" :title="error">
            <template #extra>
              <router-link to="/" class="btn-back">← 返回 Syllabus</router-link>
            </template>
          </el-result>
        </div>

        <!--
          正常数据渲染
          v-if="detail" 确保 detail.topic 存在再渲染
        -->
        <template v-if="detail">
          <!-- 面包屑导航 + 返回按钮 -->
          <div class="detail-header">
            <router-link to="/" class="btn-back">← 返回 Syllabus</router-link>
          </div>

          <!--
            Topic 基本信息区
            类似 TopicCard.vue 的 header 结构，但更完整
          -->
          <div class="topic-info">
            <el-tag type="primary" size="small" effect="dark">
              {{ detail.topic.topic_id }}
            </el-tag>
            <h1 class="topic-title">{{ topicTitle }}</h1>
          </div>

          <!--
            Objectives 学习目标列表
            和 TopicCard.vue 里的 objectivesList 同样的处理逻辑
          -->
          <div v-if="objectivesList.length" class="topic-objectives">
            <h3 class="section-title">Learning Objectives</h3>
            <ul>
              <li v-for="(obj, idx) in objectivesList" :key="idx">
                {{ obj }}<span v-if="!obj.endsWith('.')">.</span>
              </li>
            </ul>
          </div>

          <!--
            题目区：按试卷分组展示

            questions_by_paper 结构：
            { "ENGAA 2016 S1": [...], "ENGAA 2017 S1": [...] }

            Object.entries() 把它变成可遍历的 [paperName, questions[]] 对
          -->
          <div class="questions-section">
            <h3 class="section-title">
              Questions
              <span class="question-count">{{ totalCount }} 题</span>
            </h3>

            <div
              v-for="[paper, questions] of Object.entries(detail.questions_by_paper)"
              :key="paper"
              class="paper-group"
            >
              <!-- 试卷名称作为分组标题 -->
              <h4 class="paper-title">
                <el-tag size="small" type="warning" effect="plain">{{ paper }}</el-tag>
              </h4>

              <!--
                题目网格：每个 QuestionCard 显示一道题
                2 列网格，图片自适应
              -->
              <div class="questions-grid">
                <QuestionCard
                  v-for="q in questions"
                  :key="q.id"
                  :question="q"
                />
              </div>
            </div>

            <!--
              没有题目时的状态
              questions_by_paper 存在但为空对象 {} 时显示
            -->
            <EmptyState
              v-if="totalCount === 0"
              title="No Questions"
              description="该章节暂无可用的题目图片。"
            />
          </div>
        </template>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getTopicDetail } from '@/api/topic'
import type { TopicDetailData, Subject } from '@/types'
import QuestionCard from '@/components/QuestionCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useMathJax } from '@/composables/useMathJax'
const { renderMath } = useMathJax()

// topicId 和 subject 由路由传到 props（见 router/index.ts 中 props: true）
const props = defineProps<{ subject: Subject; topicId: string }>()

const loading = ref(true)
const error = ref('')
const detail = ref<TopicDetailData | null>(null)

/** 兼容 physics/math 的标题显示 */
const topicTitle = computed(() => {
  if (!detail.value) return ''
  const t = detail.value.topic
  if ('title' in t && t.title) return t.title
  if ('chapter' in t && t.chapter) return t.chapter
  return t.topic_id
})

/** 把 objectives 按 \n 拆成数组，和 TopicCard.vue 一样 */
const objectivesList = computed(() => {
  if (!detail.value?.topic.objectives) return []
  return detail.value.topic.objectives
    .split('\n')
    .filter(s => s.trim() !== '')
})

/** 计算题目总数 */
const totalCount = computed(() => {
  if (!detail.value) return 0
  let count = 0
  for (const paper in detail.value.questions_by_paper) {
    count += detail.value.questions_by_paper[paper].length
  }
  return count
})

onMounted(async () => {
  try {
    const data = await getTopicDetail(props.subject, props.topicId)
    detail.value = data
    loading.value = false  // 先关闭骨架屏，让内容显示到 DOM 中

    // 然后让 MathJax 渲染 LaTeX 公式
    await renderMath()
  } catch (e: any) {
    error.value = e.message || '加载失败'
    loading.value = false
  }
})
</script>

<style scoped>
.topic-detail {
  max-width: 1000px;
  margin: 0 auto;
}

/* ----- 头部导航 ----- */
.detail-header {
  margin-bottom: 1.5rem;
}

.btn-back {
  font-size: 0.9rem;
  font-weight: 600;
  color: #2d6a9f;
  text-decoration: none;
  transition: opacity 0.15s;
}
.btn-back:hover {
  opacity: 0.75;
}

/* ----- Topic 基本信息 ----- */
.topic-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.topic-title {
  font-size: 1.6rem;
  font-weight: 700;
  margin: 0;
  color: #1a1a2e;
}

/* ----- 章节标题（复用） ----- */
.section-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 1rem 0;
  padding-bottom: 0.4rem;
  border-bottom: 2px solid #2d6a9f;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.question-count {
  font-size: 0.85rem;
  font-weight: 500;
  color: #6b7280;
}

/* ----- Objectives 列表 ----- */
.topic-objectives {
  margin-bottom: 2rem;
}

.topic-objectives ul {
  list-style: disc;
  padding-left: 1.5rem;
  font-size: 0.95rem;
  color: #4b5563;
  line-height: 1.7;
}

/* ----- 题目分组 ----- */
.paper-group {
  margin-bottom: 2rem;
}

.paper-title {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  font-weight: 600;
}

.questions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

/* 小屏幕改为一列 */
@media (max-width: 700px) {
  .questions-grid {
    grid-template-columns: 1fr;
  }
}

/* ----- 错误状态 ----- */
.error-state {
  padding: 2rem 0;
}
</style>
