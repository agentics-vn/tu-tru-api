interface BracketTextProps {
  children: React.ReactNode;
  className?: string;
}

export function BracketText({ children, className = "" }: BracketTextProps) {
  return (
    <div className={`flex flex-col items-center ${className}`}>
      <span className="text-accent text-2xl leading-none mb-1">{"\u300C"}</span>
      <div className="text-accent text-2xl font-medium leading-tight tracking-wide">
        {children}
      </div>
      <span className="text-accent text-2xl leading-none mt-1">{"\u300D"}</span>
    </div>
  );
}
