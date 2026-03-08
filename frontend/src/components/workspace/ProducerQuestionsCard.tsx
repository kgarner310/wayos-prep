interface ProducerQuestionsCardProps {
  questions: string[]
}

export function ProducerQuestionsCard({ questions }: ProducerQuestionsCardProps) {
  if (questions.length === 0) return null

  return (
    <div>
      <div className="text-[10px] font-medium text-slate-500 uppercase tracking-wider mb-2">Producer Questions</div>
      <div className="space-y-1.5">
        {questions.map((q, i) => (
          <div key={i} className="flex items-start gap-2 text-[11px]">
            <span className="flex-none w-4 h-4 rounded-full bg-blue-500/15 text-blue-400 text-[10px]
                           flex items-center justify-center font-mono font-medium">
              {i + 1}
            </span>
            <span className="text-slate-300">{q}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
