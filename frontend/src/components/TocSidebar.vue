<template>
  <!--
    TOC 侧边栏组件

    原来 index.html#L8-L31 是整个 Jinja2 模板，
    现在抽成独立组件，只负责"显示 TOC"这一件事。

    对比原来 Jinja2：
    {% for chapter_prefix, topics in grouped.items() %}
      <div class="toc-chapter-group">
        <h3>Chapter {{ chapter_prefix }}</h3>
        {% for topic in topics %}
          <a href="#{{ topic['topic_id'] }}" class="toc-link">...</a>
        {% endfor %}
      </div>
    {% endfor %}
  -->
  <aside class="toc-sidebar">
    <h2 class="toc-title">Table of Contents</h2>

    <!-- ===== Physics / Math 大板块切换 ===== -->
    <div class="subject-tabs">
      <button
        class="subject-tab"
        :class="{ active: modelValue === 'physics' }"
        @click="$emit('update:modelValue', 'physics')"
      >
        <span class="subject-icon">⚛</span>
        <span>Physics</span>
      </button>
      <button
        class="subject-tab"
        :class="{ active: modelValue === 'math' }"
        @click="$emit('update:modelValue', 'math')"
      >
        <span class="subject-icon">∑</span>
        <span>Math</span>
      </button>
    </div>

    <!--
      v-if / v-else：Vue 的条件渲染
      对比原来 Jinja2：{% if grouped %} ... {% else %} ... {% endif %}
    -->
    <template v-if="grouped && Object.keys(grouped).length">
      <nav class="toc-nav">
        <!--
          v-for 遍历对象：v-for="(value, key) in object"
          grouped 是 { 'P': [...], 'S': [...], ... } 或 { 'M1': [...], 'M2': [...] }
          Object.entries() 把对象转成可遍历的数组
        -->
        <div
          v-for="[prefix, topics] of Object.entries(grouped)"
          :key="prefix"
          class="toc-chapter-group"
        >
          <h3 class="toc-chapter-heading">Chapter {{ prefix }}</h3>
          <ul class="toc-list">
            <li v-for="topic in topics" :key="topic.topic_id">
              <!--
                @click.prevent 替代 e.preventDefault()
                原因见下方 handleTocClick
              -->
              <a
                :href="`#${topic.topic_id}`"
                class="toc-link"
                :class="{ active: activeId === topic.topic_id }"
                @click.prevent="handleTocClick(topic.topic_id)"
              >
                <span class="toc-id">{{ topic.topic_id }}</span>
                <span class="toc-label">{{ topicLabel(topic) }}</span>
              </a>
            </li>
          </ul>
        </div>
      </nav>
    </template>

    <p v-else class="empty-hint">No syllabus data found.</p>
  </aside>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { GroupedTopics, Topic, Subject } from '@/types'

const props = defineProps<{
  modelValue: Subject
  grouped: GroupedTopics | null
}>()

defineEmits<{
  'update:modelValue': [value: Subject]
}>()

// 当前高亮的 topic_id
const activeId = ref('')

/** 兼容显示 topic 名称：physics 有 title，math 用 chapter 作为 fallback */
function topicLabel(topic: Topic): string {
  if ('title' in topic && topic.title) return topic.title
  return ""
}

/* ================================================================
   平滑滚动（原来 main.js#L31-L43 的 TOC 滚动）
   ================================================================
   原生 JS 实现：
     document.querySelectorAll(".toc-link").forEach(function(link) {
       link.addEventListener("click", function(e) {
         e.preventDefault()
         const target = document.getElementById(targetId)
         const top = target.getBoundingClientRect().top + window.scrollY - 80
         window.scrollTo({ top, behavior: "smooth" })
       })
     })

   Vue 实现：用 ref 和方法，更清晰
   ================================================================ */
function handleTocClick(topicId: string) {
  const el = document.getElementById(topicId)
  if (!el) return

  const top = el.getBoundingClientRect().top + window.scrollY - 80
  window.scrollTo({ top, behavior: 'smooth' })

  // 立即高亮被点击的链接
  activeId.value = topicId
}

/* ================================================================
   IntersectionObserver 滚动高亮（原来 main.js#L46-L70）
   ================================================================
   原生 JS 实现：自行创建 observer，手动查 DOM 找 toc-link，
   手动加 style.background 或 class

   Vue 实现：数据驱动，observer 只负责更新 activeId，
   Vue 自动把 active class 加到对应的 .toc-link 上
   优势：不需要操作 DOM 样式，不耦合 CSS 类名
   ================================================================ */
let observer: IntersectionObserver | null = null

onMounted(() => {
  // nextTick：等 DOM 渲染完再建立 observer
  setTimeout(() => {
    const cards = document.querySelectorAll('.topic-card[id]')
    if (!cards.length) return

    observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            activeId.value = entry.target.id
            break
          }
        }
      },
      { rootMargin: '-80px 0px -60% 0px' }
    )

    cards.forEach((card) => observer!.observe(card))
  }, 0)
})

// 组件卸载时清理 observer，避免内存泄漏
onUnmounted(() => {
  observer?.disconnect()
})
</script>

<style scoped>
/* ===== 原来 style.css#L84-L150 迁移 ===== */
.toc-sidebar {
  flex: 0 0 280px;
  position: sticky;
  top: 72px;
  background: #fff;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
  max-height: calc(100vh - 90px);
  overflow-y: auto;
}

.toc-title {
  font-size: 1rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e8e8f0;
}

.toc-chapter-group {
  margin-bottom: 1.25rem;
}

.toc-chapter-heading {
  font-size: 0.8rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.5rem;
}

.toc-list {
  list-style: none;
  padding: 0;
}

.toc-list li {
  margin-bottom: 0.3rem;
}

.toc-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.5rem;
  border-radius: 5px;
  font-size: 0.85rem;
  color: #374151 !important;
  transition: background 0.15s;
  text-decoration: none;
}
.toc-link:hover {
  background: #eff3f9;
  text-decoration: none;
}

/* Vue 数据驱动的 active 高亮 */
.toc-link.active {
  background: #e0e7f0;
}

.toc-id {
  font-weight: 600;
  color: #2d6a9f;
  min-width: 3.2em;
  font-size: 0.8rem;
}

.toc-label {
  color: #4b5563;
}

.empty-hint {
  color: #9ca3af;
  font-size: 0.9rem;
  text-align: center;
}

/* ----- Physics / Math 板块切换标签 ----- */
.subject-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.subject-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.6rem 0.5rem;
  border: 2px solid #e0e7f0;
  border-radius: 8px;
  background: #f9fafb;
  font-size: 0.9rem;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}
.subject-tab:hover {
  background: #eff3f9;
  border-color: #c8d4e3;
}
.subject-tab.active {
  background: #2d6a9f;
  border-color: #2d6a9f;
  color: #fff;
}
.subject-icon {
  font-size: 1.1rem;
}
</style>
