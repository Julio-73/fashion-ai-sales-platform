export type ApiClientOptions = {
  accessToken?: string;
};

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function handleResponse<TResponse>(response: Response): Promise<TResponse> {
  if (!response.ok) {
    let code = "unknown_error";
    let message = `API request failed with status ${response.status}`;
    try {
      const body = await response.json() as { error?: { code?: string; message?: string } };
      if (body.error?.code) code = body.error.code;
      if (body.error?.message) message = body.error.message;
    } catch {
      // ignore parse errors, use defaults
    }
    throw new ApiError(code, message, response.status);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}

export async function apiGet<TResponse>(path: string, options: ApiClientOptions = {}): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: {
      "content-type": "application/json",
      ...(options.accessToken ? { authorization: `Bearer ${options.accessToken}` } : {})
    },
    cache: "no-store"
  });

  return handleResponse<TResponse>(response);
}

export async function apiPost<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  options: ApiClientOptions = {}
): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(options.accessToken ? { authorization: `Bearer ${options.accessToken}` } : {})
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  return handleResponse<TResponse>(response);
}

export async function apiPatch<TResponse, TPayload>(
  path: string,
  payload: TPayload,
  options: ApiClientOptions = {}
): Promise<TResponse> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "PATCH",
    headers: {
      "content-type": "application/json",
      ...(options.accessToken ? { authorization: `Bearer ${options.accessToken}` } : {})
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  return handleResponse<TResponse>(response);
}

export async function apiDelete(path: string, options: ApiClientOptions = {}): Promise<void> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: "DELETE",
    headers: {
      ...(options.accessToken ? { authorization: `Bearer ${options.accessToken}` } : {})
    },
    cache: "no-store"
  });

  await handleResponse<void>(response);
}
