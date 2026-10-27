import type { ReactNode } from 'react';

// Minimal, safe renderer for the model's light markdown (bold, bullets, numbered steps).
// Builds React elements only: no HTML injection, no dangerouslySetInnerHTML.
function inline(s: string, k: string): ReactNode[] {
  let offset = 0; // key by character offset in the source line: stable and unique, not an array index
  return s.split(/(\*\*[^*]+\*\*)/g).map((part) => {
    const key = `${k}@${offset}`;
    offset += part.length;
    return part.startsWith('**') && part.endsWith('**') && part.length > 4 ? (
      <strong key={key}>{part.slice(2, -2)}</strong>
    ) : (
      part
    );
  });
}

interface Item {
  line: number;
  text: string;
}

export function RichText({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  let bullets: Item[] = [];
  let steps: Item[] = [];
  const flush = (at: number) => {
    if (bullets.length)
      blocks.push(
        <ul key={`ul${at}`} className="list-disc space-y-1 pl-5">
          {bullets.map((b) => (
            <li key={b.line}>{inline(b.text, `b${b.line}`)}</li>
          ))}
        </ul>
      );
    if (steps.length)
      blocks.push(
        <ol key={`ol${at}`} className="list-decimal space-y-1 pl-5">
          {steps.map((b) => (
            <li key={b.line}>{inline(b.text, `s${b.line}`)}</li>
          ))}
        </ol>
      );
    bullets = [];
    steps = [];
  };
  text.split('\n').forEach((raw, line) => {
    const t = raw.trim();
    const bullet = /^[-*]\s+(.*)/.exec(t);
    const step = /^\d+[.)]\s+(.*)/.exec(t);
    if (bullet) {
      if (steps.length) flush(line);
      bullets.push({ line, text: bullet[1] });
    } else if (step) {
      if (bullets.length) flush(line);
      steps.push({ line, text: step[1] });
    } else {
      flush(line);
      // eslint-disable-next-line react/no-array-index-key -- the source line number is stable for a given answer
      if (t) blocks.push(<p key={`p${line}`}>{inline(t, `p${line}`)}</p>);
    }
  });
  flush(-1);
  return <div className="space-y-2">{blocks}</div>;
}
