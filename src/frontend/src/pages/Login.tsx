import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { LogIn, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

/**
 * ログインフォームの型定義
 */
interface LoginForm {
  username: string
  password: string
}

/**
 * ログインページコンポーネント
 */
export default function Login() {
  const navigate = useNavigate()
  const location = useLocation()
  const [showPassword, setShowPassword] = useState(false)
  const { login, isLoading, error, clearError } = useAuthStore()

  // リダイレクト先（ログイン後に戻るページ）
  const from = (location.state as { from?: string })?.from || '/'

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    defaultValues: {
      username: '',
      password: '',
    },
  })

  /**
   * ログイン処理
   */
  const onSubmit = async (data: LoginForm) => {
    clearError()
    const success = await login(data)
    if (success) {
      navigate(from, { replace: true })
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-700 via-red-600 to-red-800 py-12 px-4 sm:px-6 lg:px-8">
      {/* 背景パターン */}
      <div className="absolute inset-0 opacity-10">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <div className="max-w-md w-full space-y-8 relative z-10">
        {/* ロゴ・タイトル */}
        <div className="text-center">
          <div className="mx-auto h-20 w-20 flex items-center justify-center rounded-full bg-white shadow-xl">
            <svg className="h-12 w-12 text-red-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
              <path d="M12 6c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" />
            </svg>
          </div>
          <h1 className="mt-4 text-3xl font-extrabold text-white">
            浦和カップ
          </h1>
          <p className="mt-2 text-red-100">
            トーナメント管理システム
          </p>
        </div>

        {/* ログインフォーム */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* エラーメッセージ */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}

            {/* ユーザー名 */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                ユーザー名
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                {...register('username', {
                  required: 'ユーザー名を入力してください',
                })}
                className={`
                  w-full px-4 py-3 rounded-lg border-2 transition-colors
                  focus:outline-none focus:ring-0
                  ${errors.username
                    ? 'border-red-300 focus:border-red-500'
                    : 'border-gray-200 focus:border-red-500'}
                `}
                placeholder="ユーザー名を入力"
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
              )}
            </div>

            {/* パスワード */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                パスワード
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  {...register('password', {
                    required: 'パスワードを入力してください',
                  })}
                  className={`
                    w-full px-4 py-3 rounded-lg border-2 transition-colors pr-12
                    focus:outline-none focus:ring-0
                    ${errors.password
                      ? 'border-red-300 focus:border-red-500'
                      : 'border-gray-200 focus:border-red-500'}
                  `}
                  placeholder="パスワードを入力"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
              )}
            </div>

            {/* ログインボタン */}
            <button
              type="submit"
              disabled={isLoading}
              className={`
                w-full flex items-center justify-center px-4 py-3 rounded-lg
                text-white font-medium transition-all duration-200
                ${isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-red-600 hover:bg-red-700 shadow-lg hover:shadow-xl'}
              `}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  ログイン中...
                </>
              ) : (
                <>
                  <LogIn className="h-5 w-5 mr-2" />
                  ログイン
                </>
              )}
            </button>
          </form>

          {/* 閲覧モードへのリンク */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              閲覧のみの場合は
              <button
                type="button"
                onClick={() => navigate('/')}
                className="text-red-600 hover:text-red-700 font-medium ml-1"
              >
                こちらからどうぞ
              </button>
            </p>
          </div>
        </div>

        {/* フッター */}
        <p className="text-center text-sm text-red-100">
          © 2024 浦和カップ実行委員会
        </p>
      </div>
    </div>
  )
}
