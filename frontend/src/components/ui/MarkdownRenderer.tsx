"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/utils";
import katex from "katex";
import "katex/dist/katex.min.css";

/* ────────────────────────────────────────────────────────
   KaTeX math rendering
   ──────────────────────────────────────────────────────── */

function renderLatex(tex: string, displayMode: boolean): string | null {
  try {
    return katex.renderToString(tex.trim(), {
      displayMode,
      throwOnError: false,
      trust: false,
      strict: false,
    });
  } catch {
    return null;
  }
}

function MathBlock({ tex, display }: { tex: string; display: boolean }) {
  const html = renderLatex(tex, display);
  if (!html) return <code className="text-xs font-mono text-loss/80">{tex}</code>;
  return (
    <span
      className={cn(display && "block my-2.5 overflow-x-auto text-center")}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

/* ────────────────────────────────────────────────────────
   Inline markdown → React nodes
   Handles: **bold**, *italic*, `code`, [link](url),
            \(...\) inline math, $price, +%gain, -%loss
   ──────────────────────────────────────────────────────── */

export function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const re =
    /(\\\((.+?)\\\)|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[(.+?)\]\((.+?)\))/g;
  let last = 0;
  let m: RegExpExecArray | null;

  while ((m = re.exec(text)) !== null) {
    if (m.index > last) nodes.push(highlightFinancial(text.slice(last, m.index), last));
    const k = m.index;
    if (m[2]) {
      nodes.push(<MathBlock key={k} tex={m[2]} display={false} />);
    } else if (m[3]) {
      nodes.push(<strong key={k} className="font-semibold text-white">{m[3]}</strong>);
    } else if (m[4]) {
      nodes.push(<em key={k} className="italic text-muted-foreground">{m[4]}</em>);
    } else if (m[5]) {
      nodes.push(<code key={k} className="bg-white/[0.06] text-cyan/90 text-[13px] px-1.5 py-0.5 rounded font-mono">{m[5]}</code>);
    } else if (m[6] && m[7]) {
      nodes.push(<a key={k} href={m[7]} target="_blank" rel="noopener noreferrer" className="text-accent underline underline-offset-2 decoration-accent/40 hover:decoration-accent">{m[6]}</a>);
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) nodes.push(highlightFinancial(text.slice(last), last));
  return nodes.length ? nodes : [text];
}

/** Highlight $prices and +/-% values inline */
function highlightFinancial(text: string, keyBase: number): ReactNode {
  const re = /(\$[\d,]+(?:\.\d+)?)|([+-]\d+(?:\.\d+)?%)/g;
  const parts: ReactNode[] = [];
  let last = 0;
  let m: RegExpExecArray | null;

  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    const k = keyBase + m.index;
    if (m[1]) {
      parts.push(<span key={k} className="text-white font-medium tabular-nums">{m[1]}</span>);
    } else if (m[2]) {
      const isPos = m[2].startsWith("+");
      parts.push(
        <span key={k} className={cn("font-medium tabular-nums", isPos ? "text-profit" : "text-loss")}>
          {m[2]}
        </span>
      );
    }
    last = m.index + m[0].length;
  }
  if (parts.length === 0) return text;
  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}

/* ────────────────────────────────────────────────────────
   Block-level markdown renderer
   Handles: headings, bullets, numbered lists, blockquotes,
            code blocks, display math, horizontal rules, paragraphs
   ──────────────────────────────────────────────────────── */

interface BlockLine { type: string; content: string; lang?: string; items?: string[] }

function parseBlocks(text: string): BlockLine[] {
  const lines = text.split("\n");
  const blocks: BlockLine[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trimStart();

    if (trimmed.startsWith("\\[")) {
      const mathLines: string[] = [trimmed.slice(2)];
      i++;
      while (i < lines.length && !lines[i].includes("\\]")) {
        mathLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) {
        const closingLine = lines[i];
        const closingIdx = closingLine.indexOf("\\]");
        mathLines.push(closingLine.slice(0, closingIdx));
        i++;
      }
      blocks.push({ type: "math_display", content: mathLines.join("\n").trim() });
      continue;
    }

    if (trimmed.startsWith("$$") && !trimmed.startsWith("$$$")) {
      const rest = trimmed.slice(2);
      const closeIdx = rest.indexOf("$$");
      if (closeIdx >= 0) {
        blocks.push({ type: "math_display", content: rest.slice(0, closeIdx).trim() });
        i++;
        continue;
      }
      const mathLines: string[] = [rest];
      i++;
      while (i < lines.length && !lines[i].includes("$$")) {
        mathLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) {
        const closingLine = lines[i];
        const ci = closingLine.indexOf("$$");
        mathLines.push(closingLine.slice(0, ci));
        i++;
      }
      blocks.push({ type: "math_display", content: mathLines.join("\n").trim() });
      continue;
    }

    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trimStart().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      blocks.push({ type: "code_block", content: codeLines.join("\n"), lang });
      i++;
      continue;
    }

    if (/^[-*_]{3,}\s*$/.test(trimmed)) {
      blocks.push({ type: "hr", content: "" });
      i++;
      continue;
    }

    if (trimmed.startsWith("### ")) { blocks.push({ type: "h3", content: trimmed.slice(4) }); i++; continue; }
    if (trimmed.startsWith("## "))  { blocks.push({ type: "h2", content: trimmed.slice(3) }); i++; continue; }
    if (trimmed.startsWith("# "))   { blocks.push({ type: "h1", content: trimmed.slice(2) }); i++; continue; }

    if (trimmed.startsWith("> ")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trimStart().startsWith("> ")) {
        quoteLines.push(lines[i].trimStart().slice(2));
        i++;
      }
      blocks.push({ type: "blockquote", content: quoteLines.join("\n") });
      continue;
    }

    if (/^[-*]\s/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s/.test(lines[i].trimStart())) {
        items.push(lines[i].trimStart().slice(2));
        i++;
      }
      blocks.push({ type: "ul", content: "", items });
      continue;
    }

    if (/^\d+\.\s/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trimStart())) {
        const numM = lines[i].trimStart().match(/^\d+\.\s/);
        items.push(lines[i].trimStart().slice(numM![0].length));
        i++;
      }
      blocks.push({ type: "ol", content: "", items });
      continue;
    }

    if (!trimmed) { blocks.push({ type: "empty", content: "" }); i++; continue; }

    blocks.push({ type: "p", content: line });
    i++;
  }

  return blocks;
}

export function renderBlocks(text: string): ReactNode[] {
  const blocks = parseBlocks(text);
  return blocks.map((b, i) => {
    switch (b.type) {
      case "math_display":
        return (
          <div key={i} className="my-3 py-3 px-4 bg-white/[0.02] border border-white/[0.05] rounded-lg overflow-x-auto">
            <MathBlock tex={b.content} display />
          </div>
        );
      case "h1":
        return (
          <div key={i} className="mt-4 mb-2 first:mt-0">
            <h3 className="text-[15px] font-bold text-white tracking-wide">{renderInline(b.content)}</h3>
            <div className="h-px bg-gradient-to-r from-profit/30 to-transparent mt-1.5" />
          </div>
        );
      case "h2":
        return (
          <div key={i} className="mt-3.5 mb-1.5 first:mt-0">
            <h4 className="text-sm font-semibold text-white tracking-wide">{renderInline(b.content)}</h4>
          </div>
        );
      case "h3":
        return (
          <div key={i} className="mt-3 mb-1 first:mt-0">
            <h5 className="text-[13px] font-semibold text-white/90">{renderInline(b.content)}</h5>
          </div>
        );
      case "ul":
        return (
          <ul key={i} className="mt-1.5 mb-1 space-y-1">
            {b.items!.map((item, j) => (
              <li key={j} className="flex gap-2 text-sm leading-relaxed">
                <span className="text-profit/60 mt-[3px] shrink-0">&#x2022;</span>
                <span>{renderInline(item)}</span>
              </li>
            ))}
          </ul>
        );
      case "ol":
        return (
          <ol key={i} className="mt-1.5 mb-1 space-y-1">
            {b.items!.map((item, j) => (
              <li key={j} className="flex gap-2 text-sm leading-relaxed">
                <span className="text-muted-foreground/70 font-medium tabular-nums shrink-0 min-w-[1.2em] text-right">{j + 1}.</span>
                <span>{renderInline(item)}</span>
              </li>
            ))}
          </ol>
        );
      case "blockquote":
        return (
          <div key={i} className="border-l-2 border-accent/40 pl-3 my-2 text-sm text-muted-foreground italic">
            {b.content.split("\n").map((l, j) => <p key={j}>{renderInline(l)}</p>)}
          </div>
        );
      case "code_block":
        return (
          <div key={i} className="my-2 rounded-md overflow-hidden">
            {b.lang && (
              <div className="bg-white/[0.04] px-3 py-1 text-[10px] text-muted-foreground tracking-wider uppercase font-mono">{b.lang}</div>
            )}
            <pre className="bg-white/[0.03] border border-white/[0.06] rounded-md px-3 py-2.5 text-[13px] leading-relaxed overflow-x-auto">
              <code className="font-mono text-cyan/80">{b.content}</code>
            </pre>
          </div>
        );
      case "hr":
        return <div key={i} className="my-3 h-px bg-gradient-to-r from-border via-border/50 to-transparent" />;
      case "empty":
        return <div key={i} className="h-2" />;
      default: {
        const isDisclaimer = /not financial advice/i.test(b.content);
        if (isDisclaimer) {
          return (
            <p key={i} className="mt-3 pt-2 border-t border-border/50 text-[11px] text-muted-foreground/50 italic">
              {b.content}
            </p>
          );
        }
        return <p key={i} className="mt-1.5 first:mt-0 text-sm leading-[1.7]">{renderInline(b.content)}</p>;
      }
    }
  });
}

/* ────────────────────────────────────────────────────────
   MarkdownRenderer component — drop-in replacement for
   plain-text analysis output
   ──────────────────────────────────────────────────────── */

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export default function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  if (!content) return null;
  return (
    <div className={cn("text-muted leading-relaxed", className)}>
      {renderBlocks(content)}
    </div>
  );
}
