<template>
  <!--
    根组件 —— 整个应用的"入口"

    <DefaultLayout> 是布局外壳（导航栏 + 页面架子），
    <router-view /> 在里面，Vue Router 会根据当前 URL
    决定渲染 SyllabusView / TopicDetail / SearchResult 等页面。

    原来：每个请求 Flask 决定返回哪个模板
    现在：Vue Router 在前端决定显示哪个 .vue 组件
  -->
  <DefaultLayout />
</template>

<script setup lang="ts">
import DefaultLayout from '@/layouts/DefaultLayout.vue'
</script>
