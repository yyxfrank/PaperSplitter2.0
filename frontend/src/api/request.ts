/* ==============================================================
 * Axios 拦截器封装
 *
 * 通俗理解：这是整个前端"发请求"的统一出入口。
 * 就像快递站：所有寄出去的包裹（请求）统一贴标签，
 * 所有收到的包裹（响应）统一拆包检查。
 * ============================================================== */

import axios from 'axios'
import { ElMessage } from 'element-plus'

/** 创建 Axios 实例 —— 一个预先配好默认设置的请求工具 */
const service = axios.create({
  baseURL: '/api',           // 所有请求前面自动加 /api
  timeout: 15000,            // 超过 15 秒没响应就报超时
  headers: { 'Content-Type': 'application/json' }
})

/* ---------- 请求拦截器：请求发出去之前 ---------------------------------- */
service.interceptors.request.use(
  (config) => {
    // 这里可以做：给每个请求加 Token、加时间戳防缓存等
    return config
  },
  (error) => {
    console.error('[请求发送失败]', error)
    return Promise.reject(error)
  }
)

/* ---------- 响应拦截器：收到响应之后，到你的代码之前 ---------------------- */
service.interceptors.response.use(
  (response) => {
    // response.data 就是后端返回的 JSON 体（ApiResponse 结构）
    const res = response.data

    // 业务码不为 0 → 说明后端处理失败
    if (res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }

    // 成功：直接返回 data，调用方拿到手的就是干净的数据
    return res.data
  },
  (error) => {
    // HTTP 层面的错误（网络断开、404、500 等）
    if (error.response) {
      switch (error.response.status) {
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        case 502:
        case 503:
          ElMessage.error('服务器暂不可用，请稍后重试')
          break
        default:
          ElMessage.error(`请求失败 (${error.response.status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络')
    } else {
      ElMessage.error('网络异常，请检查连接')
    }
    return Promise.reject(error)
  }
)

export default service
