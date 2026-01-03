// src/core/http/index.ts
export { httpClient } from './client';
export { authInterceptor } from './interceptors/auth';
export { errorInterceptor } from './interceptors/error';
export { transformInterceptor } from './interceptors/transform';

// ユーティリティ関数
export {
  apiRequest,
  createUploadConfig,
  downloadFile,
  retryRequest,
} from './utils';
export type {
  ApiError,
  ApiSuccessResponse,
  ApiErrorResponse,
  ApiResponse,
} from './utils';

// 後方互換性のためdefaultエクスポート
import { httpClient } from './client';
export default httpClient;
