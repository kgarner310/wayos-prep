function SkeletonBlock({ className = '' }: { className?: string }) {
  return <div className={`bg-slate-800 rounded animate-pulse ${className}`} />
}

function SkeletonCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      {children}
    </div>
  )
}

export function WorkspaceSkeleton() {
  return (
    <div className="max-w-6xl mx-auto space-y-4 animate-in fade-in">
      {/* Account header skeleton */}
      <div className="mb-4">
        <SkeletonBlock className="h-5 w-64 mb-2" />
        <SkeletonBlock className="h-3 w-40" />
      </div>

      {/* Score cards row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <SkeletonCard key={i}>
            <SkeletonBlock className="h-2.5 w-20 mb-3" />
            <div className="flex items-center gap-4">
              <SkeletonBlock className="h-16 w-16 rounded-full flex-none" />
              <div className="flex-1 space-y-2">
                <SkeletonBlock className="h-2 w-full" />
                <SkeletonBlock className="h-2 w-3/4" />
                <SkeletonBlock className="h-2 w-5/6" />
              </div>
            </div>
          </SkeletonCard>
        ))}
      </div>

      {/* Two-column middle */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonCard>
          <SkeletonBlock className="h-2.5 w-24 mb-3" />
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="border border-slate-800 rounded-lg p-3">
                <SkeletonBlock className="h-3 w-32 mb-1.5" />
                <SkeletonBlock className="h-2 w-full" />
              </div>
            ))}
          </div>
        </SkeletonCard>

        <SkeletonCard>
          <SkeletonBlock className="h-2.5 w-28 mb-3" />
          <div className="space-y-1.5">
            {[1, 2, 3, 4, 5].map((i) => (
              <SkeletonBlock key={i} className="h-2.5 w-full" />
            ))}
          </div>
        </SkeletonCard>
      </div>

      {/* Narrative skeleton */}
      <SkeletonCard>
        <SkeletonBlock className="h-2.5 w-32 mb-3" />
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonBlock key={i} className="h-2.5 w-full" />
          ))}
          <SkeletonBlock className="h-2.5 w-2/3" />
        </div>
      </SkeletonCard>

      {/* Bottom two-column */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <SkeletonCard>
          <SkeletonBlock className="h-2.5 w-28 mb-3" />
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <SkeletonBlock key={i} className="h-3 w-full" />
            ))}
          </div>
        </SkeletonCard>
        <SkeletonCard>
          <SkeletonBlock className="h-2.5 w-32 mb-3" />
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <SkeletonBlock key={i} className="h-3 w-full" />
            ))}
          </div>
        </SkeletonCard>
      </div>
    </div>
  )
}
