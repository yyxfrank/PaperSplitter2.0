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
    <TocSidebar :grouped="grouped" />

    <!--
      ===== 右侧：主内容区 =====
    -->
    <div class="syllabus-content">
      <h1 class="page-title">Syllabus</h1>

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
              不加冒号就是字符串 "topic"，加冒号说明是 JS 表达式
            -->
            <TopicCard :topic="topic" />
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

import { ref, onMounted } from 'vue'

// --- 导入 API 函数（在 .ts 文件里定义的） ---
import { getGroupedSyllabus } from '@/api/syllabus'
import type { GroupedTopics } from '@/types'

// --- 导入子组件，本页面由这些组件拼装而成 ---
import TocSidebar from '@/components/TocSidebar.vue'
import TopicCard from '@/components/TopicCard.vue'
import EmptyState from '@/components/EmptyState.vue'

// --- 导入 MathJax 渲染函数（让 LaTeX 公式正确显示） ---
import { useMathJax } from '@/composables/useMathJax'
const { renderMath } = useMathJax()

// ref 创建响应式数据：Vue 会追踪它的变化，变了就自动更新页面
const grouped = ref<GroupedTopics | null>(null)
const loading = ref(false)
const error = ref('')

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
  loading.value = true
  try {
    // await getGroupedSyllabus() → 等 API 返回数据
    // 原来 Flask 在路由函数里查数据库 → render_template 直接塞数据
    // Vue 方式：组件自己调 API 拿数据
    const data = await getGroupedSyllabus()
    grouped.value = data

    // 数据加载完后让 MathJax 重新渲染页面中的 LaTeX 公式
    // 因为公式内容是异步加载的，MathJax 不会自动感知到 DOM 变化
    await renderMath()
  } catch (e: any) {
    error.value = e.message || '加载 Syllabus 失败'
  } finally {
    loading.value = false
  }
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

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 2rem;
  color: #1a1a2e;
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
