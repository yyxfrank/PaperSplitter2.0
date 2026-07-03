<template>
  <!--
    顶部导航栏组件

    原来代码在 base.html#L22-L38，
    现在抽成独立组件，所有页面共用同一个导航栏。
    改导航栏样式只需改这一个文件。
  -->
  <header class="top-bar">
    <div class="top-bar-inner">
      <!--
        router-link 替代 <a href="{{ url_for('syllabus') }}">
        好处：前端路由跳转不刷新页面，体验更流畅
      -->
      <router-link to="/" class="logo">PaperSplitter</router-link>

      <nav class="nav-links">
        <router-link to="/">Syllabus</router-link>
      </nav>

      <!--
        搜索表单 — Vue 方式

        原来 base.html 用 <form method="get" action="{{ url_for('search') }}">
        是"表单提交"→ 浏览器原生跳转（会刷新页面）

        现在用 router-link + el-input，跳转由 Vue Router 控制 → 无刷新
      -->
      <div class="search-area">
        <el-input
          v-model="keyword"
          placeholder="搜索章节..."
          size="small"
          class="search-input"
          clearable
          @keyup.enter="doSearch"
        />
        <el-button type="primary" size="small" @click="doSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const keyword = ref('')

/** 点击搜索或按回车时跳转到搜索页 */
function doSearch() {
  const q = keyword.value.trim()
  if (q) {
    router.push({ name: 'search', query: { q } })
  }
}
</script>

<style scoped>
/* ===== 原来 style.css#L30-L64 迁移 ===== */
.top-bar {
  background: #1a1a2e;
  color: #fff;
  padding: 0 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.top-bar-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  height: 56px;
  gap: 2rem;
}

.logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff !important;
  letter-spacing: 0.5px;
  text-decoration: none;
}

.nav-links a {
  color: #b0b8c8 !important;
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
}
.nav-links a:hover {
  color: #fff !important;
}

.search-area {
  margin-left: auto;
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.search-input {
  width: 200px;
}

/* 覆盖 Element Plus 默认样式让搜索框在深色背景上看得清 */
.search-input :deep(.el-input__wrapper) {
  background: #2a2a3e;
  box-shadow: 0 0 0 1px #444 inset;
}
.search-input :deep(.el-input__inner) {
  color: #fff;
}
</style>
