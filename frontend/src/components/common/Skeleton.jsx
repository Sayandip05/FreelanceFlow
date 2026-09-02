import React from 'react'

/**
 * Primitive skeleton pulsing box with smooth shimmer animation
 */
export function Skeleton({ className = '', ...props }) {
  return (
    <div
      className={`animate-pulse bg-gray-200/80 rounded-xl ${className}`}
      {...props}
    />
  )
}

/**
 * Skeleton for Dashboard / Overview pages
 * (Header, 4 metric cards, and 2 content sections)
 */
export function DashboardSkeleton() {
  return (
    <div className="space-y-8 animate-fade-in">
      {/* Top Banner / Welcome Skeleton */}
      <div className="bg-white rounded-3xl p-8 border border-gray-100 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="space-y-2">
            <Skeleton className="h-8 w-64 rounded-xl" />
            <Skeleton className="h-4 w-96 max-w-full rounded-lg" />
          </div>
          <Skeleton className="h-11 w-36 rounded-xl" />
        </div>
      </div>

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-xs space-y-3">
            <div className="flex justify-between items-center">
              <Skeleton className="h-3.5 w-24 rounded-md" />
              <Skeleton className="w-10 h-10 rounded-xl" />
            </div>
            <Skeleton className="h-8 w-32 rounded-lg" />
            <Skeleton className="h-3 w-20 rounded-md" />
          </div>
        ))}
      </div>

      {/* Main Grid / Tables Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 border border-gray-100 shadow-xs space-y-4">
          <div className="flex justify-between items-center pb-2">
            <Skeleton className="h-6 w-40 rounded-lg" />
            <Skeleton className="h-4 w-20 rounded-md" />
          </div>
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="p-4 rounded-2xl bg-gray-50/70 border border-gray-100 flex items-center justify-between gap-4">
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-4 w-3/4 rounded-md" />
                  <Skeleton className="h-3 w-1/2 rounded-md" />
                </div>
                <Skeleton className="h-8 w-24 rounded-xl" />
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-xs space-y-4">
          <Skeleton className="h-6 w-32 rounded-lg" />
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="p-3.5 rounded-2xl bg-gray-50/70 border border-gray-100 space-y-2">
                <Skeleton className="h-4 w-full rounded-md" />
                <Skeleton className="h-3 w-2/3 rounded-md" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Skeleton for Card Grid pages (Browse, Projects, Contracts, Bids)
 */
export function CardGridSkeleton({ count = 6 }) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header bar */}
      <div className="flex justify-between items-center">
        <div className="space-y-1.5">
          <Skeleton className="h-7 w-48 rounded-xl" />
          <Skeleton className="h-4 w-64 rounded-lg" />
        </div>
        <Skeleton className="h-10 w-32 rounded-xl" />
      </div>

      {/* Grid items */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {[...Array(count)].map((_, i) => (
          <div key={i} className="bg-white rounded-3xl p-6 border border-gray-100 shadow-xs space-y-4">
            <div className="flex justify-between items-start">
              <Skeleton className="h-5 w-40 rounded-lg" />
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
            <Skeleton className="h-12 w-full rounded-xl" />
            <div className="flex gap-2">
              <Skeleton className="h-5 w-16 rounded-md" />
              <Skeleton className="h-5 w-20 rounded-md" />
              <Skeleton className="h-5 w-14 rounded-md" />
            </div>
            <div className="pt-2 border-t border-gray-100 flex justify-between items-center">
              <Skeleton className="h-6 w-24 rounded-lg" />
              <Skeleton className="h-9 w-28 rounded-xl" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * Skeleton for Tables (Contracts, Milestones, Deliverables, Payments)
 */
export function TableSkeleton({ rows = 5, cols = 5 }) {
  return (
    <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-xs space-y-4 animate-fade-in">
      <div className="flex justify-between items-center pb-2">
        <div className="space-y-1.5">
          <Skeleton className="h-6 w-44 rounded-lg" />
          <Skeleton className="h-3.5 w-64 rounded-md" />
        </div>
        <Skeleton className="h-9 w-28 rounded-xl" />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-100">
              {[...Array(cols)].map((_, i) => (
                <th key={i} className="pb-3 px-4">
                  <Skeleton className="h-4 w-20 rounded-md" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {[...Array(rows)].map((_, r) => (
              <tr key={r}>
                {[...Array(cols)].map((_, c) => (
                  <td key={c} className="py-4 px-4">
                    <Skeleton className="h-4 w-full max-w-[120px] rounded-md" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/**
 * Skeleton for Contract / Project Detail Pages
 */
export function DetailPageSkeleton() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Back button & Title */}
      <div className="space-y-3">
        <Skeleton className="h-6 w-28 rounded-lg" />
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <Skeleton className="h-9 w-80 rounded-xl" />
          <div className="flex gap-2">
            <Skeleton className="h-10 w-28 rounded-xl" />
            <Skeleton className="h-10 w-28 rounded-xl" />
          </div>
        </div>
      </div>

      {/* Metric Cards Banner */}
      <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-xs space-y-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="p-4 rounded-2xl bg-gray-50 border border-gray-100 space-y-2">
              <Skeleton className="h-3 w-20 rounded-md" />
              <Skeleton className="h-6 w-28 rounded-lg" />
            </div>
          ))}
        </div>
        <Skeleton className="h-4 w-full rounded-full" />
      </div>

      {/* Main Section */}
      <div className="bg-white rounded-3xl p-6 border border-gray-100 shadow-xs space-y-4">
        <Skeleton className="h-6 w-48 rounded-lg" />
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="p-4 rounded-2xl bg-gray-50/70 border border-gray-100 flex justify-between items-center">
              <div className="space-y-2 flex-1 max-w-md">
                <Skeleton className="h-4 w-48 rounded-md" />
                <Skeleton className="h-3 w-32 rounded-md" />
              </div>
              <Skeleton className="h-5 w-20 rounded-md" />
              <Skeleton className="h-9 w-24 rounded-xl" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * Skeleton for AI Worklog / Workspace Page
 */
export function WorkPageSkeleton() {
  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col space-y-4 animate-fade-in">
      {/* Header Bar */}
      <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-xs flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Skeleton className="w-9 h-9 rounded-xl" />
          <div className="space-y-1.5">
            <Skeleton className="h-4 w-48 rounded-md" />
            <Skeleton className="h-3 w-28 rounded-md" />
          </div>
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-9 w-24 rounded-xl" />
          <Skeleton className="h-9 w-28 rounded-xl" />
        </div>
      </div>

      {/* 2-Pane Workspace */}
      <div className="flex-1 flex gap-4 overflow-hidden">
        {/* Left Chat / Form Pane */}
        <div className="flex-1 bg-white rounded-2xl border border-gray-100 shadow-xs p-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex gap-3">
              <Skeleton className="w-8 h-8 rounded-full" />
              <Skeleton className="h-16 w-3/4 rounded-2xl" />
            </div>
            <div className="flex justify-end gap-3">
              <Skeleton className="h-12 w-1/2 rounded-2xl" />
              <Skeleton className="w-8 h-8 rounded-full" />
            </div>
          </div>
          <Skeleton className="h-12 w-full rounded-xl mt-4" />
        </div>

        {/* Right Action Panel */}
        <div className="w-72 bg-white rounded-2xl border border-gray-100 shadow-xs p-5 space-y-4 hidden md:block">
          <Skeleton className="h-5 w-32 rounded-md" />
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 space-y-3">
            <Skeleton className="h-3 w-20 rounded-md" />
            <Skeleton className="h-6 w-28 rounded-md" />
            <Skeleton className="h-9 w-full rounded-xl" />
          </div>
        </div>
      </div>
    </div>
  )
}
