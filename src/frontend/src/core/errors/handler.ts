// src/core/errors/handler.ts
// グローバルエラーハンドラ
import type { AppError, ErrorCode } from './types';
import { isAppError } from './types';

type ErrorCallback = (error: AppError) => void;

class ErrorHandler {
  private static instance: ErrorHandler;
  private callbacks: Map<ErrorCode | 'all', ErrorCallback[]> = new Map();

  private constructor() {}

  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  // エラーハンドラを登録
  on(code: ErrorCode | 'all', callback: ErrorCallback): () => void {
    const callbacks = this.callbacks.get(code) || [];
    callbacks.push(callback);
    this.callbacks.set(code, callbacks);

    // クリーンアップ関数を返す
    return () => {
      const current = this.callbacks.get(code) || [];
      this.callbacks.set(
        code,
        current.filter((cb) => cb !== callback)
      );
    };
  }

  // エラーを処理
  handle(error: unknown): void {
    const appError = this.normalize(error);

    // 特定コードのハンドラを実行
    const codeCallbacks = this.callbacks.get(appError.code) || [];
    codeCallbacks.forEach((cb) => cb(appError));

    // 全体ハンドラを実行
    const allCallbacks = this.callbacks.get('all') || [];
    allCallbacks.forEach((cb) => cb(appError));
  }

  // エラーを正規化
  private normalize(error: unknown): AppError {
    if (isAppError(error)) {
      return error;
    }

    if (error instanceof Error) {
      return {
        code: 'UNKNOWN',
        message: error.message,
        status: 0,
        retryable: false,
      };
    }

    return {
      code: 'UNKNOWN',
      message: '予期しないエラーが発生しました',
      status: 0,
      retryable: false,
    };
  }
}

export const errorHandler = ErrorHandler.getInstance();
