<template>
  <!--
    公共布局组件

    作用：整个应用的"外壳"，所有页面共享的框架。
    对应原来 base.html 的角色——提供导航栏、面包屑、页面架子。

    原来 base.html：
    <header class="top-bar">...</header>
    <main class="main-content">{% block content %}{% endblock %}</main>

    Vue 方式：
    <AppTopNav /> + <main class="main-content"><router-view /></main>
    <router-view /> 就是原来 {% block content %} 那块"插槽"。
  -->
  <div class="app-wrapper">
    <AppTopNav />

    <main class="main-content">
      <router-view />
    </main>

    <!-- 全局 Lightbox（题目图片放大，详情页会用） -->
    <div
      v-show="lightboxVisible"
      class="lightbox"
      @click="closeLightbox"
    >
      <span class="lightbox-close">&times;</span>
      <img :src="lightboxSrc" class="lightbox-content" alt="放大图片" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import AppTopNav from '@/components/AppTopNav.vue'

/* ----- Lightbox 状态（全局共享） ----- */
const lightboxVisible = ref(false)
const lightboxSrc = ref('')

/**
 * 打开 Lightbox
 * 通过 window 暴露给所有页面组件使用
 */
function openLightbox(src: string) {
  lightboxSrc.value = src
  lightboxVisible.value = true
  document.body.style.overflow = 'hidden'
}

function closeLightbox() {
  lightboxVisible.value = false
  document.body.style.overflow = ''
}

// 暴露给全局，所有页面组件都可以调用
;(window as any).openLightbox = openLightbox

// Escape 键关闭
function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') closeLightbox()
}
onMounted(() => document.addEventListener('keydown', onKeyDown))
onUnmounted(() => document.removeEventListener('keydown', onKeyDown))
</script>

<style scoped>
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

/* Lightbox 样式 */
.lightbox {
  position: fixed;
  z-index: 999;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.lightbox-content {
  max-width: 92%;
  max-height: 92%;
  border-radius: 6px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4);
}

.lightbox-close {
  position: absolute;
  top: 20px;
  right: 32px;
  font-size: 2.5rem;
  color: #fff;
  cursor: pointer;
  font-weight: 300;
  line-height: 1;
}
</style>
