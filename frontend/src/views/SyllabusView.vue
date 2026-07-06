<template>
  <!--
    首页 Main View —— 展示全部 Syllabus

    原来这些内容写在 index.html 中，由 Flask 的
    @app.route('/') 路由 + render_template 去渲染。

    现在这是一个独立的 .vue 文件，
    它自己"管自己"——自己调 API、自己渲染、自己管样式。
  -->
  <div class="syllabus-layout">
    <!--
      ===== 左侧：TOC 侧边栏 =====
      原来 index.html#L8-L31 直接用 Jinja2 写在页面里，
      现在变成 <TocSidebar> 组件标签，一行搞定。
      好处：这个页面文件更短、更聚焦。
    -->
    <!--
      v-model:modelValue — 双向绑定 activeSubject
      TocSidebar 里点击 Physics/Math 标签时会 emit update:modelValue，
      这里自动更新 activeSubject，同时 grouped 数据自动重新加载
    -->
    <TocSidebar
      v-model:modelValue="activeSubject"
      :grouped="grouped"
    />

    <!--
      ===== 右侧：主内容区 =====
    -->
    <div class="syllabus-content">
      <div class="page-header">
        <h1 class="page-title">Syllabus</h1>

        <!-- 筛选开关 -->
        <div class="filter-bar">
          <el-switch
            v-model="hasQuestionsOnly"
            size="small"
            active-color="#2d6a9f"
            @change="onFilterChange"
          />
          <span class="filter-label">Contain Questions Only</span>
          <el-tag v-if="hasQuestionsOnly" size="small" type="warning" effect="plain" class="filter-tag">
            {{ topicCountWithQuestions }} topics
          </el-tag>
        </div>
      </div>

      <!--
        ===== 场景 1：无数据库（grouped === null） =====
        原来 index.html#L37-L46：
        {% if grouped is none %}
          <div class="empty-state">... 一大段 HTML ...</div>
        {% endif %}
      -->
      <EmptyState
        v-if="grouped === null"
        title="No Database Found"
        description="The master database master_exam_data.db has not been created yet."
        :steps="[
          'Run your data pipeline to extract a syllabus and classify questions.',
          'Run build_database.py to populate the database.',
          'Refresh this page.'
        ]"
      />

      <!--
        ===== 场景 2：有数据 =====
        原来 index.html#L47-L71：
        {% elif grouped %}
          {% for chapter_prefix, topics in grouped.items() %}
            <section class="chapter-section">
              <h2>Chapter {{ chapter_prefix }}</h2>
              {% for topic in topics %}
                <article id="{{ topic['topic_id'] }}" class="topic-card">
                  ... 卡片内容 ...
                </article>
              {% endfor %}
            </section>
          {% endfor %}
        {% endif %}
      -->
      <template v-else-if="grouped && Object.keys(grouped).length">
        <section
          v-for="[prefix, topics] of Object.entries(grouped)"
          :key="prefix"
          class="chapter-section"
        >
          <h2 class="chapter-header">Chapter {{ prefix }}</h2>

          <!--
            卡片列表：TopicCard 组件复用
            注意这里给 card 加了 id，用于 TOC 滚动定位
          -->
          <div
            v-for="topic in topics"
            :key="topic.topic_id"
            :id="topic.topic_id"
          >
            <!--
              :topic="topic" → 把当前话题数据传给子组件
              :subject="activeSubject" → 告知当前所属学科，用于路由跳转和标题显示
              不加冒号就是字符串 "topic"，加冒号说明是 JS 表达式
            -->
            <TopicCard :topic="topic" :subject="activeSubject" />
          </div>
        </section>
      </template>

      <!-- 场景 3：分组对象存在但为空（边界情况） -->
      <EmptyState
        v-else
        title="No Data"
        description="Syllabus data is empty."
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/* ================================================================
   <script setup> — Vue 3 组合式 API 的写法

   对比原来代码的三个文件：
   - index.html      → 模板 (template)
   - style.css 中 syllabus 部分 → 样式 (scoped style)
   - main.js 中 TOC 交互部分 → JS 逻辑 (script setup)

   原来三个文件分离，现在一个 .vue 文件自己包含所有。
   ================================================================ */

import { ref, computed, watch, onMounted, onActivated, onDeactivated, nextTick } from 'vue'

// 显式声明组件名，确保 keep-alive 的 include 匹配能正确识别
defineOptions({ name: 'SyllabusView' })

// --- 导入 API 函数（在 .ts 文件里定义的） ---
import { getGroupedSyllabus } from '@/api/syllabus'
import type { GroupedTopics, Subject } from '@/types'

// --- 导入子组件，本页面由这些组件拼装而成 ---
import TocSidebar from '@/components/TocSidebar.vue'
import TopicCard from '@/components/TopicCard.vue'
import EmptyState from '@/components/EmptyState.vue'

// --- 导入 MathJax 渲染函数（让 LaTeX 公式正确显示） ---
import { useMathJax } from '@/composables/useMathJax'
const { renderMath } = useMathJax()

// ===== ref 创建响应式数据 =====
const grouped = ref<GroupedTopics | null>(null)
const loading = ref(false)
const error = ref('')

// 当前选中的学科（默认 physics），与 TocSidebar 双向绑定
const activeSubject = ref<Subject>('physics')

// 筛选状态：是否只显示有题目的 topic
const hasQuestionsOnly = ref(false)

// 有题目的 topic 总数（用于筛选标签上的计数）
const topicCountWithQuestions = computed(() => {
  if (!grouped.value) return 0
  return Object.values(grouped.value).reduce((sum, topics) => sum + topics.length, 0)
})

/** 统一的 syllabus 数据加载函数 */
async function loadSyllabus(subject: Subject) {
  loading.value = true
  error.value = ''
  try {
    const data = await getGroupedSyllabus(subject, hasQuestionsOnly.value)
    grouped.value = data
    await renderMath()
  } catch (e: any) {
    error.value = e.message || '加载 Syllabus 失败'
    grouped.value = null
  } finally {
    loading.value = false
  }
}

// 当筛选开关切换时，重新加载数据
async function onFilterChange() {
  await loadSyllabus(activeSubject.value)
}

// 监听学科切换，自动重载数据
watch(activeSubject, async (newSubject) => {
  // 滚动到页面顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
  await loadSyllabus(newSubject)
})

/**
 * onMounted — Vue 的生命周期钩子
 *
 * 通俗理解：这个函数在"组件被挂载到页面后"自动执行。
 * 相当于原来 jQuery 的 $(document).ready()，
 * 或者原来 main.js 里的 DOMContentLoaded 事件。
 *
 * 这里放"页面一打开就需要做的事情"——即获取数据。
 */
onMounted(async () => {
  // 首次加载默认学科（physics）的数据
  await loadSyllabus(activeSubject.value)
})

/* ================================================================
   keep-alive 生命周期适配

   父级 DefaultLayout.vue 已用 <keep-alive :include="['syllabus']">
   将本组件包裹。这意味着：

   1. 离开页面时组件不会被销毁，所有 ref 状态（hasQuestionsOnly、
      grouped 等）自动保留，不重置。
   2. onMounted 只在首次进入时执行一次，再次进入不会重复调用。
   3. 再次激活时触发 onActivated，需要在这里恢复滚动位置并
      重新触发 MathJax 渲染（因为 DOM 可能被重建）。
   ================================================================ */

// 保存离开时的滚动位置
const savedScrollTop = ref(0)

onDeactivated(() => {
  // 用户离开页面（点面包屑跳转）时，记录当前滚动位置
  savedScrollTop.value = window.scrollY
})

onActivated(async () => {
  // 用户回到本页面时：
  // 1. 恢复之前的滚动位置
  await nextTick()
  window.scrollTo(0, savedScrollTop.value)

  // 2. 重新触发 MathJax 渲染，确保公式正确显示
  //    因为 keep-alive 缓存了 DOM，但 MathJax 可能未扫描到变化
  await renderMath()
})
</script>

<style scoped>
/* ================================================================
   原有 CSS 迁移说明

   原来这些样式在 style.css#L77-L171 中，
   是"全局"样式。现在搬进 SyllabusView.vue 的 scoped 中。

   scoped 效果：以下所有 CSS 选择器会自动加上
   这个组件独有的属性选择器，不会污染全局。

   比如 .syllabus-layout 在浏览器里变成：
     .syllabus-layout[data-v-xxxx] { ... }
   其他地方即使有同名类也不会被影响。
   ================================================================ */

.syllabus-layout {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}

.syllabus-content {
  flex: 1;
  min-width: 0;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0;
  color: #1a1a2e;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-label {
  font-size: 0.875rem;
  color: #555;
  white-space: nowrap;
  cursor: pointer;
}

.filter-tag {
  font-weight: 600;
}

.chapter-section {
  margin-bottom: 2.5rem;
}

.chapter-header {
  font-size: 1.3rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 3px solid #2d6a9f;
}

/* 响应式：屏幕小于 900px 时变单列 */
@media (max-width: 900px) {
  .syllabus-layout {
    flex-direction: column;
  }
}
</style>
