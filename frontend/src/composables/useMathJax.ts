/* ==============================================================
 * MathJax 组合式函数
 *
 * 组合式函数（Composable）= 带状态的 Vue 工具函数。
 * 通俗理解：把某段"带生命周期的逻辑"抽成独立函数，
 * 任何组件调用它就能获得对应能力。
 *
 * 原来 main.js 里有一段代码"等页面加载完调 MathJax"，
 * 但它是全局的，一次性执行。现在每个页面组件需要时自己调用。
 * ============================================================== */

import { nextTick } from 'vue'

/**
 * 让 MathJax 重新渲染当前页面的 LaTeX 公式
 *
 * 为什么需要这个？
 * 原来 Jinja2 模式：后端返回的 HTML 已经包含完整内容，
 * MathJax 在页面加载时一次性全部渲染完。
 *
 * Vue 模式：数据是异步加载的，页面先渲染"空的"，
 * 等到 API 数据返回后，Vue 才填充真实内容。
 * MathJax 看不到后面新增的内容，所以需要手动通知它"有新公式要渲染"。
 */
export function useMathJax() {
  /**
   * 触发 MathJax 重新排版
   * 在数据加载完成后调用
   */
  async function renderMath() {
    await nextTick()  // 等 Vue 把 DOM 更新完

    // MathJax 3 内部启动也是异步的（做初始化排版等），
    // 用 MathJax.startup.promise 确保它启动完毕再通知它重新排版
    const mj = (window as any).MathJax
    console.log('[MathJax] 状态:', { 
      exists: !!mj, 
      hasTypeset: !!mj?.typesetPromise,
      startupDone: !!mj?.startup?.promise
    })

    if (mj?.startup?.promise) {
      await mj.startup.promise
      console.log('[MathJax] 启动完成，开始排版')
    }

    if (mj?.typesetPromise) {
      try {
        await mj.typesetPromise()
        console.log('[MathJax] 排版完成')
      } catch (e) {
        console.warn('[MathJax] 排版失败:', e)
      }
    } else {
      console.warn('[MathJax] typesetPromise 不可用')
    }
  }

  return { renderMath }
}
