interface ScoreBadgeProps {
  score: number;
  grade: "A" | "B" | "C" | "D";
  size?: "sm" | "md" | "lg";
}

const GRADE_COLORS = {
  A: "text-good",
  B: "text-accent",
  C: "text-fg-muted",
  D: "text-bad",
};

export function ScoreBadge({ score, grade, size = "md" }: ScoreBadgeProps) {
  const textSize =
    size === "lg" ? "text-4xl" : size === "md" ? "text-2xl" : "text-lg";
  const labelSize = size === "lg" ? "text-sm" : "text-[0.6rem]";

  return (
    <div className="flex items-baseline gap-2">
      <span
        className={`heading-display ${textSize} ${GRADE_COLORS[grade]}`}
      >
        {score}
      </span>
      <span className={`mono-label ${labelSize}`}>/100</span>
      <span
        className={`
          mono-label ${labelSize} px-1.5 py-0.5 border
          ${grade === "A" ? "border-good text-good" : grade === "B" ? "border-accent text-accent" : grade === "D" ? "border-bad text-bad" : "border-fg-muted text-fg-muted"}
        `}
      >
        Hang {grade}
      </span>
    </div>
  );
}
