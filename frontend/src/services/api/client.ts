const API_BASE_PATH = '/api'

class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText
    try {
      const payload = (await response.json()) as { detail?: string }
      detail = payload.detail ?? detail
    } catch {
      // Ignore JSON parsing failures for non-JSON error payloads.
    }
    throw new ApiError(detail, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  })
  return parseJsonResponse<T>(response)
}

export async function postFormData<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    method: 'POST',
    body,
  })
  return parseJsonResponse<T>(response)
}

export async function postJson<TResponse, TRequest>(path: string, body?: TRequest): Promise<TResponse> {
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  return parseJsonResponse<TResponse>(response)
}

export async function putJson<TResponse, TRequest>(path: string, body: TRequest): Promise<TResponse> {
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    method: 'PUT',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
  return parseJsonResponse<TResponse>(response)
}

export async function deleteJson<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_PATH}${path}`, {
    method: 'DELETE',
    headers: {
      Accept: 'application/json',
    },
  })
  return parseJsonResponse<TResponse>(response)
}

export { API_BASE_PATH, ApiError }
