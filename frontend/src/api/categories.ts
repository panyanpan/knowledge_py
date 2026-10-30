import http from './http'

export interface CategoryNode {
  id: number
  parent_id: number
  name: string
  level: number
  path: string
  sort_order: number
  created_at: string
  children: CategoryNode[]
}

export interface CategoryPayload {
  name: string
  parent_id: number
  sort_order: number
}

export function getCategories(): Promise<CategoryNode[]> {
  return http.get('/categories')
}

export function createCategory(data: CategoryPayload): Promise<{ id: number }> {
  return http.post('/categories', data)
}

export function updateCategory(id: number, data: Partial<CategoryPayload>): Promise<unknown> {
  return http.put(`/categories/${id}`, data)
}

export function deleteCategory(id: number): Promise<unknown> {
  return http.delete(`/categories/${id}`)
}
