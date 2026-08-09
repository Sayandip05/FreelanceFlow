import { useRef, useState, useEffect, useCallback } from 'react'
import { X, Shield, ChevronDown, FileText, Lock, Users, Cookie, AlertTriangle, RefreshCw, Info } from 'lucide-react'

const privacySections = [
  {
    icon: Info,
    title: 'Information Collection',
    content:
      'We collect information you provide directly (name, email, professional details) and data generated through platform usage such as project history, bids, messages, and payment transactions. This helps us operate the FreelanceFlow marketplace securely and effectively.',
  },
  {
    icon: FileText,
    title: 'Use of Data',
    content:
      'Your data is used to match freelancers with clients, process payments via Razorpay Escrow, generate AI-powered work reports, facilitate messaging, and improve platform recommendations. We do not use your data for purposes unrelated to FreelanceFlow services.',
  },
  {
    icon: Users,
    title: 'Third-Party Sharing',
    content:
      'We do not sell your personal information. We share data only with trusted service partners necessary to operate the platform: Razorpay for payment processing, Azure for cloud storage, and Google for OAuth authentication. All partners are bound by strict data protection agreements.',
  },
  {
    icon: Cookie,
    title: 'Cookies & Tracking',
    content:
      'We use localStorage and session tokens to maintain authentication and remember your preferences (e.g., sidebar state). No third-party advertising cookies are used. Analytics may collect anonymized usage patterns to improve the product.',
  },
  {
    icon: Shield,
    title: 'Security Measures',
    content:
      "All data is transmitted over HTTPS/TLS. Passwords are hashed using Django's PBKDF2 algorithm. JWT access tokens expire in 1 hour. Payment funds are held in Razorpay Escrow and only released upon your explicit approval. We regularly audit our security posture.",
  },
  {
    icon: Lock,
    title: 'Milestone & Payment Terms',
    content:
      'Clients and freelancers mutually agree on milestones within a contract — each milestone has a title, description, due date (deadline), and an equal share of the total project budget. The total budget is split equally across all milestones automatically. Clients may also set milestones on a monthly basis, in which case the budget is again divided equally per month. Milestone payments are funded into escrow before work begins on that milestone, and are only released to the freelancer once the client approves the submitted deliverable. FreelanceFlow deducts a platform fee from released milestone payments.',
  },
  {
    icon: Users,
    title: 'User Rights',
    content:
      'You may request access to, correction of, or deletion of your personal data at any time by contacting support@freelanceflow.com. Account deletion removes all personal profile data within 30 days, subject to legal retention requirements for financial records.',
  },
  {
    icon: AlertTriangle,
    title: 'Platform Conduct',
    content:
      'Users agree not to engage in fraud, misrepresentation, or harassment. Violations may result in immediate account suspension and legal action. All contracts formed on FreelanceFlow are legally binding agreements between the client and freelancer.',
  },
  {
    icon: RefreshCw,
    title: 'Policy Updates',
    content:
      'We may update this policy periodically. Significant changes will be communicated via email and an in-app notification. Your continued use of FreelanceFlow after policy updates constitutes your acceptance of the revised terms.',
  },
]

export default function PrivacyPolicyModal({ mode = 'view', onAccept, onDecline, onClose }) {
  const [scrollProgress, setScrollProgress] = useState(0)
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false)
  const contentRef = useRef(null)
  const isOnboarding = mode === 'onboarding'

  const handleScroll = useCallback(() => {
    const el = contentRef.current
    if (!el) return
    const scrollable = el.scrollHeight - el.clientHeight
    if (scrollable <= 0) {
      setScrollProgress(1)
      setHasScrolledToBottom(true)
      return
    }
    const progress = Math.min(1, el.scrollTop / scrollable)
    setScrollProgress(progress)
    if (progress >= 0.98) setHasScrolledToBottom(true)
  }, [])

  useEffect(() => {
    const el = contentRef.current
    if (el && el.scrollHeight <= el.clientHeight) {
      setScrollProgress(1)
      setHasScrolledToBottom(true)
    }
  }, [])

  const canAccept = !isOnboarding || hasScrolledToBottom

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[200] p-4"
      onClick={isOnboarding ? undefined : onClose}
    >
      <div
        className="bg-white rounded-2xl w-full max-w-lg shadow-2xl flex flex-col overflow-hidden"
        style={{ maxHeight: '88vh', animation: 'privacy-modal-in 0.2s ease' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3 flex-shrink-0">
          <img src="/logo.png" alt="FreelanceFlow" className="w-8 h-8 object-contain flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <h2 className="text-base font-bold text-gray-900">Privacy Policy</h2>
            <p className="text-xs text-gray-500">FreelanceFlow Platform · Last updated Aug 2026</p>
          </div>
          {!isOnboarding && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors flex-shrink-0"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {isOnboarding && (
          <div className="mx-6 mt-4 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2.5 flex-shrink-0">
            <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-800 font-medium">
              Please read our Privacy Policy carefully and scroll to the bottom before accepting.
              Acceptance is required to use the platform.
            </p>
          </div>
        )}

        {/* Scrollable content */}
        <div
          ref={contentRef}
          onScroll={handleScroll}
          className="overflow-y-auto flex-1 px-6 py-4 space-y-1"
        >
          {privacySections.map((section, idx) => {
            const Icon = section.icon
            return (
              <div key={idx}>
                <div className="flex items-start gap-3 p-3.5 rounded-xl hover:bg-gray-50 transition-colors">
                  <div className="w-7 h-7 bg-indigo-50 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Icon className="w-3.5 h-3.5 text-indigo-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 mb-1">{section.title}</p>
                    <p className="text-xs text-gray-500 leading-relaxed">{section.content}</p>
                  </div>
                </div>
                {idx < privacySections.length - 1 && (
                  <div className="border-b border-gray-50 mx-3" />
                )}
              </div>
            )
          })}
          <div className="h-2" />
        </div>

        {/* Scroll progress bar */}
        <div className="h-1 bg-gray-100 flex-shrink-0">
          <div
            className="h-full bg-indigo-500 transition-all duration-150"
            style={{ width: `${scrollProgress * 100}%` }}
          />
        </div>

        {/* Scroll hint */}
        {isOnboarding && !hasScrolledToBottom && (
          <div className="flex items-center justify-center gap-1.5 py-2 bg-gray-50 border-t border-gray-100 flex-shrink-0">
            <ChevronDown className="w-3.5 h-3.5 text-gray-400" style={{ animation: 'bounce 1s infinite' }} />
            <span className="text-xs text-gray-400 font-medium">Scroll to read all sections to enable Accept</span>
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex-shrink-0">
          {isOnboarding ? (
            <div className="flex flex-col gap-2">
              <button
                onClick={onAccept}
                disabled={!canAccept}
                className={`w-full py-2.5 text-sm font-bold rounded-xl transition-all duration-200 ${
                  canAccept
                    ? 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                {canAccept ? 'I Accept the Privacy Policy' : 'Read the full policy to continue'}
              </button>
              <button
                onClick={onDecline}
                className="w-full py-2 text-xs font-medium text-gray-500 hover:text-red-600 transition-colors"
              >
                Decline & Sign Out
              </button>
            </div>
          ) : (
            <button
              onClick={onClose}
              className="w-full py-2.5 text-sm font-bold rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
