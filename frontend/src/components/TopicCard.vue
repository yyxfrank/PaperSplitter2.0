<template>
  <!--
    话题卡片组件

    原来 Jinja2 写法（index.html#L51-L68）：
    <article id="{{ topic['topic_id'] }}" class="topic-card">
      <div class="topic-card-header">
        <span class="topic-id-badge">{{ topic['topic_id'] }}</span>
        <h3 class="topic-title">{{ topic['title'] }}</h3>
        <a href="{{ url_for('topic_detail', ...) }}" class="btn-view-questions">
          View Questions →
        </a>
      </div>
      <div class="topic-objectives">
        {% for obj in objectives %}
          <li>{{ obj }}{% if not obj.endswith('.') %}.{% endif %}</li>
        {% endfor %}
      </div>
    </article>

    Vue 改动点：
    1. {{ }} 在 Vue 里也是模板语法，但直接读 props
    2. v-for 替代 Jinja2 的 {% for %}
    3. router-link 替代 <a href="{{ url_for(...) }}"> —— 前端路由跳转，不刷新页面
  -->
  <article class="topic-card">
    <div class="topic-card-header">
      <el-tag type="primary" size="small" effect="dark">
        {{ topic.topic_id }}
      </el-tag>
      <h3 class="topic-title">{{ topic.title }}</h3>
      <router-link
        :to="`/topic/${topic.topic_id}`"
        class="btn-view-questions"
      >
        View Questions →
      </router-link>
    </div>

    <div class="topic-objectives">
      <ul>
        <!--
          v-for="obj in objectives" — Vue 版循环
          对比原 Jinja2: {% for obj in objectives %}
          :key 是 Vue 虚拟 DOM 优化的必填项，用索引 idx 即可
        -->
        <li v-for="(obj, idx) in objectivesList" :key="idx">
          {{ obj }}<span v-if="!obj.endsWith('.')">.</span>
        </li>
      </ul>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Topic } from '@/types'

const props = defineProps<{
  topic: Topic
}>()

/**
 * computed — 计算属性
 *
 * 通俗理解：它基于已有数据"算出"新数据，
 * 而且只有依赖变了才重新算（有缓存，性能好）。
 *
 * 原 Jinja2 写法（index.html#L61）：
 * {% set objectives = topic['objectives'].split('\n') %}
 * 那就是在模板里现场算，每次渲染都重算
 *
 * 这里是 JS 层计算好再给模板用。
 */
const objectivesList = computed(() => {
  // 把用 \n 分隔的 objectives 切成数组
  return props.topic.objectives.split('\n').filter(s => s.trim() !== '')
})
</script>

<!--
  scoped 的作用：
  Vue 会自动给这个组件的每个 HTML 元素加一个唯一属性
  比如 data-v-7ba5bd90，然后把 CSS 选择器改成：
    .topic-card[data-v-7ba5bd90] { ... }

  效果：这里的 .topic-card 只会匹配到这个组件里的元素，
  即使别的组件也有 class="topic-card" 也不会受影响。

  对比原来：style.css 里的 .topic-card 是全站全局的，
  你在 detail 页面误用同名类也会被影响。
-->
<style scoped>
/* ===== 原来 style.css#L179-L241 迁移过来 ===== */
.topic-card {
  background: #fff;
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  border-left: 4px solid #2d6a9f;
  transition: box-shadow 0.2s;
}
.topic-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.topic-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.topic-title {
  font-size: 1.05rem;
  font-weight: 600;
  flex: 1;
  margin: 0;
}

.btn-view-questions {
  font-size: 0.82rem;
  font-weight: 600;
  color: #2d6a9f !important;
  padding: 0.35rem 0.75rem;
  border: 1.5px solid #2d6a9f;
  border-radius: 6px;
  transition: all 0.15s;
  white-space: nowrap;
  text-decoration: none;
}
.btn-view-questions:hover {
  background: #2d6a9f;
  color: #fff !important;
  text-decoration: none;
}

.topic-objectives ul {
  list-style: disc;
  padding-left: 1.5rem;
  font-size: 0.9rem;
  color: #4b5563;
}
.topic-objectives ul li {
  margin-bottom: 0.2rem;
}
</style>
