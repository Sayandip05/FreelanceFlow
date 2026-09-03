import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  X,
  Bell,
} from 'lucide-react'

const ModalToastContext = createContext(null)

export function ModalToastProvider({ children }) {
  // ── Toasts State ──────────────────────────────────────────────────────────
  const [toasts, setToasts] = useState([])

  const addToast = useCallback(({ type = 'info', title, message, duration = 4500, onClick = null }) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6)
    setToasts((prev) => [...prev, { id, type, title, message, onClick }])

    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      }, duration)
    }
  }, [])

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = {
    success: (message, title = 'Success') => addToast({ type: 'success', title, message }),
    error: (message, title = 'Error') => addToast({ type: 'error', title, message }),
    warning: (message, title = 'Attention') => addToast({ type: 'warning', title, message }),
    info: (message, title = 'Information') => addToast({ type: 'info', title, message }),
    notification: (message, title = 'New Notification', onClick = null) =>
      addToast({ type: 'notification', title, message, onClick, duration: 6000 }),
  }

  // ── Confirm Modal State ───────────────────────────────────────────────────
  const [confirmState, setConfirmState] = useState({
    isOpen: false,
    title: 'Are you sure?',
    message: '',
    confirmText: 'Confirm',
    cancelText: 'Cancel',
    type: 'primary', // 'primary' | 'danger' | 'warning'
    resolve: null,
  })

  const confirm = useCallback(
    ({
      title = 'Are you sure?',
      message = '',
      confirmText = 'Confirm',
      cancelText = 'Cancel',
      type = 'primary',
    }) => {
      return new Promise((resolve) => {
        setConfirmState({
          isOpen: true,
          title,
          message,
          confirmText,
          cancelText,
          type,
          resolve,
        })
      })
    },
    []
  )

  const handleConfirm = () => {
    if (confirmState.resolve) confirmState.resolve(true)
    setConfirmState((prev) => ({ ...prev, isOpen: false, resolve: null }))
  }

  const handleCancel = () => {
    if (confirmState.resolve) confirmState.resolve(false)
    setConfirmState((prev) => ({ ...prev, isOpen: false, resolve: null }))
  }

  // Close confirm modal on Escape key
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === 'Escape' && confirmState.isOpen) {
        handleCancel()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [confirmState.isOpen])

  return (
    <ModalToastContext.Provider value={{ toast, confirm }}>
      {children}

      {/* ── Global Floating Toasts Container ───────────────────────────────── */}
      <div className="fixed top-5 right-5 z-[9999] flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-4 sm:px-0">
        {toasts.map((t) => {
          const isSuccess = t.type === 'success'
          const isError = t.type === 'error'
          const isWarning = t.type === 'warning'
          const isNotif = t.type === 'notification'

          let borderClass = 'border-blue-200 bg-white shadow-xl shadow-blue-500/5'
          let IconComponent = Info
          let iconColor = 'text-blue-600 bg-blue-50'

          if (isSuccess) {
            borderClass = 'border-emerald-200 bg-white shadow-xl shadow-emerald-500/5'
            IconComponent = CheckCircle2
            iconColor = 'text-emerald-600 bg-emerald-50'
          } else if (isError) {
            borderClass = 'border-rose-200 bg-white shadow-xl shadow-rose-500/5'
            IconComponent = AlertCircle
            iconColor = 'text-rose-600 bg-rose-50'
          } else if (isWarning) {
            borderClass = 'border-amber-200 bg-white shadow-xl shadow-amber-500/5'
            IconComponent = AlertTriangle
            iconColor = 'text-amber-600 bg-amber-50'
          } else if (isNotif) {
            borderClass = 'border-indigo-200 bg-white shadow-xl shadow-indigo-500/5'
            IconComponent = Bell
            iconColor = 'text-indigo-600 bg-indigo-50'
          }

          return (
            <div
              key={t.id}
              onClick={() => {
                if (t.onClick) {
                  t.onClick()
                  removeToast(t.id)
                }
              }}
              className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-2xl border ${borderClass} transition-all transform animate-in fade-in slide-in-from-top-4 duration-200 ${
                t.onClick ? 'cursor-pointer hover:scale-[1.01]' : ''
              }`}
            >
              <div className={`p-2 rounded-xl flex-shrink-0 ${iconColor}`}>
                <IconComponent className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0 pr-1">
                {t.title && (
                  <p className="text-xs font-bold text-gray-900 leading-tight">
                    {t.title}
                  </p>
                )}
                <p className="text-xs text-gray-600 mt-0.5 leading-relaxed break-words">
                  {t.message}
                </p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  removeToast(t.id)
                }}
                className="text-gray-400 hover:text-gray-600 p-1 rounded-lg transition-colors flex-shrink-0"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )
        })}
      </div>

      {/* ── Global In-App Confirmation Modal ───────────────────────────────── */}
      {confirmState.isOpen && (
        <div className="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div
            className="bg-white rounded-3xl w-full max-w-md p-6 shadow-2xl space-y-5 relative animate-in zoom-in-95 duration-150 border border-gray-100"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-4">
              <div
                className={`w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0 ${
                  confirmState.type === 'danger'
                    ? 'bg-rose-50 text-rose-600'
                    : confirmState.type === 'warning'
                    ? 'bg-amber-50 text-amber-600'
                    : 'bg-indigo-50 text-indigo-600'
                }`}
              >
                {confirmState.type === 'danger' ? (
                  <AlertCircle className="w-5 h-5" />
                ) : confirmState.type === 'warning' ? (
                  <AlertTriangle className="w-5 h-5" />
                ) : (
                  <Info className="w-5 h-5" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-bold text-gray-900 leading-snug">
                  {confirmState.title}
                </h3>
                <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
                  {confirmState.message}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-1">
              <button
                type="button"
                onClick={handleCancel}
                className="px-4 py-2.5 text-xs font-semibold text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-all"
              >
                {confirmState.cancelText}
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                className={`px-5 py-2.5 text-xs font-bold text-white rounded-xl shadow-sm transition-all ${
                  confirmState.type === 'danger'
                    ? 'bg-rose-600 hover:bg-rose-700'
                    : confirmState.type === 'warning'
                    ? 'bg-amber-600 hover:bg-amber-700'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                {confirmState.confirmText}
              </button>
            </div>
          </div>
        </div>
      )}
    </ModalToastContext.Provider>
  )
}

export function useModalToast() {
  const context = useContext(ModalToastContext)
  if (!context) {
    throw new Error('useModalToast must be used within a ModalToastProvider')
  }
  return context
}

export function useToast() {
  return useModalToast().toast
}

export function useConfirm() {
  return useModalToast().confirm
}
