<template>
  <!--
    搜索页面

    三种状态：
    1. 没输入关键词 → 提示"请输入关键字搜索"
    2. 有输入但没结果 → 提示"没有匹配到 XXX"
    3. 有结果 → 显示匹配列表

    原来 search.html 用 Jinja2 的 {% if %} {% elif %} {% else %} 控制，
    Vue 用 v-if / v-else-if / v-else。
  -->
  <div class="search-page">

    <!--
      el-skeleton：Element Plus 的骨架屏组件
      loading=true → 显示灰色方块占位（告诉用户"正在加载"）
      loading=false → 显示 #default 插槽里的真实内容
    -->
    <el-skeleton :loading="loading" animated>
      <template #default>

        <!-- ========== 场景 1：没输入关键词 ========== -->
        <!--
          v-if="!keyword" — 如果 keyword 为空字符串，条件为 true
          因为 keyword 初始值是 ''，所以首次进入页面时这里会显示
        -->
        <template v-if="!keyword">
          <!--
            复用 EmptyState 组件
            title：标题
            description：描述文字
            插槽 action 里放了一个 router-link 按钮，跳回首页
          -->
          <EmptyState
            title="请输入关键字搜索"
            description="在顶部搜索栏输入你想找的章节关键字即可。"
          >
            <template #action>
              <router-link to="/" class="btn-back">← 返回大纲首页</router-link>
            </template>
          </EmptyState>
        </template>

        <!-- ========== 场景 2：有输入但没结果 ========== -->
        <!--
          v-else-if — 相当于 else if
          results.length === 0 → 搜索完成但没有匹配项
        -->
        <template v-else-if="results.length === 0">
          <EmptyState
            title="没有匹配结果"
            :description="`未找到与“${keyword}”相关的内容。`"
            :steps="[
              '检查关键词是否拼写正确',
              '尝试使用更宽泛的关键词',
              '浏览大纲首页查找目标章节'
            ]"
          >
            <template #action>
              <router-link to="/" class="btn-back">← 返回大纲首页</router-link>
            </template>
          </EmptyState>
        </template>

        <!-- ========== 场景 3：有结果 ========== -->
        <!--
          v-else — 以上条件都不满足，到这里
          显示匹配数量和结果列表
        -->
        <template v-else>
          <h1 class="search-title">
            搜索结果：{{ keyword }}
            <span class="search-count">（共 {{ results.length }} 个匹配）</span>
          </h1>

          <div class="search-results">
            <!--
              v-for="topic in results" — 遍历 results 数组
              :key="topic.topic_id" — Vue 通过 key 追踪每个元素
              如果在列表中间插入/删除，有 key 可以只移动那个元素，不用重新渲染整个列表

              直接复用 TopicCard 组件
              用 :topic="topic" 把当前遍历的 topic 传给组件
              原来 search.html 里自己写了一遍卡片 HTML（L33-L44），
              现在复用 TopicCard，首页搜索页用同一套卡片样式，
              改一个文件两处都生效。
            -->
            <TopicCard
              v-for="topic in results"
              :key="topic.topic_id"
              :topic="topic"
              :subject="currentSubject"
            />
          </div>
        </template>

      </template>
    </el-skeleton>
  </div>
</template>

<script setup lang="ts">
/* ================================================================
   script setup — 组合式 API 语法糖

   对比选项式 API（Vue2 写法）：
     export default {
       data() { return { keyword: '' } },
       computed: { ... },
       methods: { ... },
       mounted() { ... }
     }

   组合式 API 的好处：同一段逻辑的代码聚在一起，不用分散在不同"选项"里
   ================================================================ */

// ---------- 导入 ----------

import { ref, onMounted } from 'vue'
// ref — 创建响应式数据
// onMounted — 生命周期钩子：组件挂载到 DOM 后执行

import { useRoute } from 'vue-router'
// useRoute — 获取当前路由信息（URL 参数、路径等）
// 对比原来：Flask 后端通过 request.args.get("q") 获取搜索词
// Vue 前端通过 useRoute().query.q 获取

import { searchTopics } from '@/api/search'
// 导入 API 函数
// @/api/search → 映射到 src/api/search.ts
// 对比原来：Flask 在路由里直接调 search_topics(keyword)
// Vue 通过 HTTP 请求调后端 API

import TopicCard from '@/components/TopicCard.vue'
// 导入可复用的 TopicCard 组件
// 好处：首页和搜索页共用同一个卡片组件，样式和逻辑统一

import EmptyState from '@/components/EmptyState.vue'
// 导入可复用的空状态组件

import { useMathJax } from '@/composables/useMathJax'
// 导入 MathJax 组合式函数
// 因为搜索结果的 objectives 可能包含 LaTeX 公式

import type { Topic, Subject } from '@/types'
// 导入类型约束（仅开发阶段用，编译后不存在）

// ---------- 响应式数据 ----------

/**
 * ref() — 创建响应式变量
 *
 * 通俗理解：
 *   普通变量（let keyword = ''）改了，模板不会重新渲染。
 *   响应式变量（ref('')）改了，Vue 会自动更新页面上用到它的地方。
 *
 * 原来 Jinja2 模板：渲染时一次性传值，页面生成后不会变。
 * Vue 模板：数据变了，页面自动跟着变（数据驱动视图）。
 */

// 当前搜索关键词，从 URL 参数读取
const keyword = ref('')

// 当前搜索学科，从 URL 参数读取（默认 physics）
const currentSubject = ref<Subject>('physics')

// 搜索结果数组
const results = ref<Topic[]>([])

// 加载状态
const loading = ref(true)

// ---------- 数据获取 ----------

/**
 * onMounted() — 组件挂载后的生命周期钩子
 *
 * 通俗理解：
 *   Vue 把组件渲染成 DOM 放到页面上后，会执行 onMounted 里的代码。
 *   适合做"页面加载后去拿数据"这件事。
 *
 * 对比原来：
 *   原来 Flask 在 route 函数里查完数据库再 render_template，
 *   后端已经把数据填进 HTML 了，页面渲染时数据就在那里。
 *
 *   Vue 模式：页面先渲染"空的壳子"，
 *   onMounted 里调 API 拿数据，拿到后再更新页面。
 */

onMounted(async () => {
  try {
    // useRoute() 获取当前路由信息
    const route = useRoute()

    // route.query.q — 读取 URL 参数 ?q=xxx
    // 对比原来 Flask：request.args.get("q", "").strip()
    // 这里 as string 是 TypeScript 类型断言："告诉 TS 这肯定是字符串"
    keyword.value = (route.query.q as string) || ''

    // route.query.subject — 读取 URL 参数 ?subject=math
    // 默认为 physics
    const subjectParam = route.query.subject as string | undefined
    if (subjectParam === 'math' || subjectParam === 'physics') {
      currentSubject.value = subjectParam
    }

    // 没输入关键词就不调用 API
    if (!keyword.value) return

    // 调 API 拿搜索结果（按学科搜索对应的 syllabus 表）
    // await — 等待异步操作完成（等后端返回数据）
    results.value = await searchTopics(keyword.value, currentSubject.value)

    // 数据加载完成后重新渲染 MathJax 公式
    // 因为 objectives 里可能有 LaTeX
    const { renderMath } = useMathJax()
    await renderMath()

  } catch (e: any) {
    // 错误处理：网络问题、服务器宕机等
    console.error('搜索失败:', e)
  } finally {
    // finally — 不管成功还是失败，最后都会执行
    loading.value = false
  }
})
</script>

<style scoped>
/* ===== 搜索页面样式（原来 style.css 没有专门的搜索页样式，仅迁移 search.html 的 inline style） ===== */

.search-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.search-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  color: #1a1a2e;
}

.search-count {
  font-size: 1rem;
  font-weight: 400;
  color: #6b7280;
}

.search-results {
  margin-top: 1rem;
}

.btn-back {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.5rem 1.2rem;
  background: #2d6a9f;
  color: #fff !important;
  border-radius: 6px;
  font-size: 0.9rem;
  text-decoration: none;
  transition: background 0.15s;
}
.btn-back:hover {
  background: #1d4f7a;
  text-decoration: none;
}
</style>
