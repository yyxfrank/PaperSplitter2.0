<template>
  <!--
    题目图片卡片组件

    作用：在 Topic 详情页显示一道题的图片。
    点击图片可以放大（Lightbox），点击其他地方保持。

    为什么需要这个组件？
    详情页可能有很多题目（同一章节跨多张试卷），
    把"一道题"抽成独立组件，方便循环渲染，也方便以后其他地方复用。
  -->
  <div class="question-card">
    <div class="question-meta">
      <el-tag size="small" type="info">{{ question.paper_name }}</el-tag>
      <span class="question-number">Q{{ question.question_number }}</span>
    </div>

    <!--
      题目图片
      @click → 调全局 Lightbox 放大查看
      :src → getImageUrl() 拼出完整可访问路径
    -->
    <img
      :src="getImageUrl(question.image_path)"
      :alt="`${question.paper_name} - Question ${question.question_number}`"
      class="question-image"
      loading="lazy"
      @click="openPreview"
    />
  </div>
</template>

<script setup lang="ts">
import type { Question } from '@/types'
import { getImageUrl } from '@/utils'

defineProps<{
  question: Question
}>()

/** 点击图片 → 通过全局暴露的 openLightbox 放大查看 */
function openPreview(e: MouseEvent) {
  const src = (e.target as HTMLImageElement).src
  // window.openLightbox 在 DefaultLayout.vue 中定义并暴露给全局
  ;(window as any).openLightbox?.(src)
}
</script>

<style scoped>
.question-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  border: 1px solid #e5e7eb;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.question-number {
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
}

.question-image {
  width: 100%;
  display: block;
  cursor: zoom-in;
  transition: opacity 0.15s;
}
.question-image:hover {
  opacity: 0.9;
}
</style>
