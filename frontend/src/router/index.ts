/* ==============================================================
 * 路由配置 —— 整个前端的"导航地图"
 *
 * 通俗理解：用户访问不同 URL 时，Vue 该显示哪个页面。
 * 这相当于原来 Flask 里 @app.route() 那几行。
 * ============================================================== */

import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  // createWebHistory → 生成干净的 URL（没有 #），如 /topic/P1.1
  // 如果你的部署环境不支持 history 模式，改 createWebHashHistory()
  history: createWebHistory(),

  routes: [
    {
      path: '/',
      name: 'syllabus',
      component: () => import('@/views/SyllabusView.vue')
    },
    {
      path: '/topic/:topicId',
      name: 'topic-detail',
      component: () => import('@/views/topic/TopicDetail.vue'),
      // props: true → 把 URL 参数 :topicId 作为 props 传给组件
      // 组件里直接 defineProps(['topicId']) 就能拿到
      props: true
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/search/SearchResult.vue')
    },
    {
      // 所有未匹配路径 → 404 页面
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/error/NotFound.vue')
    }
  ]
})

/* ==============================================================
 * 路由守卫 —— 页面跳转的"门卫"
 *
 * 通俗理解：每次用户点击跳转时，守卫可以：
 * 1. 放行（next()）
 * 2. 拦住并重定向到别的页面（next('/login')）
 * 3. 拦住并报错（next(error)）
 *
 * 这个项目暂时不需要守卫（因为没有登录系统），
 * 但先写好框架，以后加"某些页面必须登录才能看"时直接往里填逻辑。
 * ============================================================== */
router.beforeEach((to, from, next) => {
  // 举例：如果将来需要登录
  // if (to.name !== 'login' && !isLoggedIn) {
  //   next({ name: 'login' })
  //   return
  // }
  next()  // 放行
})

export default router
