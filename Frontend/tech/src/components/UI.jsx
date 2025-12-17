import React from 'react'

export const Card = ({ children, className = '', hover = false, gradient = false }) => {
  return (
    <div className={`
      bg-dark-800/50 backdrop-blur-sm rounded-2xl border border-dark-700/50
      ${gradient ? 'bg-gradient-to-br from-dark-800/50 to-dark-900/50' : ''}
      ${hover ? 'hover:border-primary-500/50 hover:shadow-xl hover:shadow-primary-500/10 transition-all duration-300 cursor-pointer' : ''}
      ${className}
    `}>
      {children}
    </div>
  )
}

export const CardHeader = ({ children, className = '' }) => {
  return (
    <div className={`px-6 py-4 border-b border-dark-700/50 ${className}`}>
      {children}
    </div>
  )
}

export const CardBody = ({ children, className = '' }) => {
  return (
    <div className={`p-6 ${className}`}>
      {children}
    </div>
  )
}

export const CardTitle = ({ children, className = '' }) => {
  return (
    <h3 className={`text-lg font-semibold text-white ${className}`}>
      {children}
    </h3>
  )
}

export const Badge = ({ children, variant = 'default', className = '' }) => {
  const variants = {
    default: 'bg-dark-700 text-dark-200',
    primary: 'bg-primary-500/20 text-primary-300 ring-1 ring-primary-500/30',
    success: 'bg-success-500/20 text-success-300 ring-1 ring-success-500/30',
    warning: 'bg-warning-500/20 text-warning-300 ring-1 ring-warning-500/30',
    danger: 'bg-danger-500/20 text-danger-300 ring-1 ring-danger-500/30',
    secondary: 'bg-secondary-500/20 text-secondary-300 ring-1 ring-secondary-500/30',
  }

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${variants[variant]} ${className}`}>
      {children}
    </span>
  )
}

export const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  className = '', 
  icon = null,
  loading = false,
  disabled = false,
  ...props 
}) => {
  const variants = {
    primary: 'bg-gradient-to-r from-primary-600 to-primary-500 hover:from-primary-500 hover:to-primary-400 text-white shadow-lg shadow-primary-500/30',
    secondary: 'bg-dark-700 hover:bg-dark-600 text-white border border-dark-600',
    success: 'bg-gradient-to-r from-success-600 to-success-500 hover:from-success-500 hover:to-success-400 text-white shadow-lg shadow-success-500/30',
    danger: 'bg-gradient-to-r from-danger-600 to-danger-500 hover:from-danger-500 hover:to-danger-400 text-white shadow-lg shadow-danger-500/30',
    ghost: 'bg-transparent hover:bg-dark-800/50 text-dark-300 hover:text-white',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  return (
    <button
      className={`
        inline-flex items-center justify-center gap-2 font-medium rounded-xl
        transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
        ${variants[variant]} ${sizes[size]} ${className}
      `}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      ) : icon}
      {children}
    </button>
  )
}

export const StatCard = ({ title, value, change, icon, trend = 'up', color = 'primary' }) => {
  const trendColors = {
    up: 'text-success-400',
    down: 'text-danger-400',
    neutral: 'text-dark-400',
  }

  const iconColors = {
    primary: 'from-primary-500 to-primary-600',
    success: 'from-success-500 to-success-600',
    warning: 'from-warning-500 to-warning-600',
    danger: 'from-danger-500 to-danger-600',
    secondary: 'from-secondary-500 to-secondary-600',
  }

  return (
    <Card hover gradient className="group">
      <CardBody>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-dark-400 text-sm font-medium mb-2">{title}</p>
            <p className="text-3xl font-bold text-white mb-2">{value}</p>
            {change && (
              <div className="flex items-center gap-2">
                <span className={`text-sm font-medium ${trendColors[trend]}`}>
                  {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {change}
                </span>
                <span className="text-dark-500 text-xs">vs last period</span>
              </div>
            )}
          </div>
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${iconColors[color]} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-200`}>
            {icon}
          </div>
        </div>
      </CardBody>
    </Card>
  )
}

export const PageHeader = ({ title, subtitle, action }) => {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">{title}</h1>
          {subtitle && <p className="text-dark-400">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>
    </div>
  )
}

export default { Card, CardHeader, CardBody, CardTitle, Badge, Button, StatCard, PageHeader }
