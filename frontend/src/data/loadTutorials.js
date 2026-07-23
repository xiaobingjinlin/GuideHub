import { load as loadYaml } from 'js-yaml'

const rawModules = import.meta.glob('../../../db/*.yaml', {
  query: '?raw',
  import: 'default',
  eager: true,
})

/**
 * 从 db/*.yaml 加载全部分类教程。
 * 新增分类：在 db/ 下加一个 yaml 文件即可。
 */
export function loadCategories() {
  return Object.entries(rawModules)
    .map(([path, raw]) => {
      const data = loadYaml(raw)
      const fileName = path.split('/').pop().replace(/\.yaml$/, '')
      return {
        id: data.category || fileName,
        label: data.label || fileName,
        examples: (data.examples || []).map((ex) => ({
          id: ex.id,
          title: ex.title,
          code: (ex.code || '').replace(/\n$/, ''),
          ui: ex.ui || null,
          notes: Array.isArray(ex.notes) ? ex.notes : [],
          kind: ex.kind || null,
          window: {
            width: ex.window?.width || 480,
            height: ex.window?.height || 720,
          },
          problem: ex.problem
            ? {
                link: ex.problem.link || '',
                statement: (ex.problem.statement || '').trim(),
                hints: Array.isArray(ex.problem.hints) ? ex.problem.hints : [],
                examples: Array.isArray(ex.problem.examples) ? ex.problem.examples : [],
              }
            : null,
        })),
      }
    })
    .sort((a, b) => a.label.localeCompare(b.label, 'zh-CN'))
}
