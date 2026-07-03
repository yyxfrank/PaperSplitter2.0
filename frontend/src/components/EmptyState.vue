<template>
  <!--
    通用空状态组件

    原来 Jinja2 写法（index.html#L37-L46）：
    {% if grouped is none %}
      <div class="empty-state">
        <h2>No Database Found</h2>
        <p>...</p>
      </div>
    {% endif %}

    原来每个空状态要在每个模板里单独写一遍，
    现在用 <EmptyState> 一个组件到处复用。
  -->
  <div class="empty-state">
    <!-- 图标插槽：允许调用方替换图标 -->
    <slot name="icon">
      <el-empty :description="title" />
    </slot>

    <!-- 标题：必须传 -->
    <h2>{{ title }}</h2>

    <!-- 描述：可选 -->
    <p v-if="description">{{ description }}</p>

    <!-- 操作步骤列表：可选 -->
    <ol v-if="steps && steps.length" class="setup-steps">
      <li v-for="(step, idx) in steps" :key="idx">{{ step }}</li>
    </ol>

    <!-- 额外操作插槽（比如放个按钮"重试"） -->
    <div v-if="$slots.action" class="empty-action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  steps?: string[]
}>()
</script>

<style scoped>
/* ===== 原来 style.css#L415-L443 =====
   原来的 .empty-state 是全局样式。
   加了 scoped 后，这些 CSS 只影响这个组件内的元素，
   不会污染其他组件里同名的类名。
========================================== */
.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}
.empty-state h2 {
  margin-bottom: 0.75rem;
}
.empty-state p {
  color: #6b7280;
  margin-bottom: 1rem;
}
.setup-steps {
  text-align: left;
  display: inline-block;
  color: #4b5563;
  font-size: 0.9rem;
}
.setup-steps li {
  margin-bottom: 0.3rem;
}
.empty-action {
  margin-top: 1rem;
}
</style>
