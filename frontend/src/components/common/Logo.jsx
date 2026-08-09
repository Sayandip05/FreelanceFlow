import { Link } from 'react-router-dom'

export default function Logo({ size = 'md', showText = true, className = '', to = null }) {
  const sizeMap = {
    xs: 'w-6 h-6',
    sm: 'w-7 h-7',
    md: 'w-8 h-8',
    lg: 'w-10 h-10',
    xl: 'w-12 h-12',
  }

  const textMap = {
    xs: 'text-sm',
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-xl',
    xl: 'text-2xl',
  }

  const content = (
    <div className={`inline-flex items-center gap-2.5 ${className}`}>
      <img
        src="/logo.png"
        alt="FreelanceFlow Logo"
        className={`${sizeMap[size] || sizeMap.md} object-contain flex-shrink-0`}
      />
      {showText && (
        <span className={`font-black text-gray-900 tracking-tight ${textMap[size] || textMap.md}`}>
          Freelance<span className="text-indigo-600">Flow</span>
        </span>
      )}
    </div>
  )

  if (!to) return content

  return (
    <Link to={to} className="inline-flex items-center group">
      {content}
    </Link>
  )
}
