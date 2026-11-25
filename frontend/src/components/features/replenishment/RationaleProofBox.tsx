import * as React from "react";

export interface RationaleProofBoxProps {
  rationale: string;
  roundingNote: string;
}

export function RationaleProofBox({
  rationale,
  roundingNote,
}: RationaleProofBoxProps): React.ReactElement {
  return (
    <div className="mt-2 rounded-control border border-hairline bg-canvas px-3 py-2 text-[12.5px] leading-[18px] text-ink-secondary">
      <p>{rationale}</p>
      <p className="mt-1 font-mono-tabular text-[12px] text-ink-muted">
        Pack constraint: {roundingNote}
      </p>
    </div>
  );
}
