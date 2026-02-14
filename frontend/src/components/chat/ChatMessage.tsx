"use client";

import { useEffect, useState, useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/lib/api";
import katex from "katex";
import "katex/dist/katex.min.css";

/* ────────────────────────────────────────────────────────
   KaTeX math rendering
   ──────────────────────────────────────────────────────── */

/** Render a LaTeX string to HTML via KaTeX. Returns null on parse failure. */
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

function renderInline(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  // Inline math \(...\) must come before markdown to avoid conflict with \*
  // Also match inline $..$ math (single $, not $$) — but only when it looks
  // like LaTeX (contains backslash or common math tokens), so plain $100
  // prices aren't accidentally caught.
  const re =
    /(\\\((.+?)\\\)|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[(.+?)\]\((.+?)\))/g;
  let last = 0;
  let m: RegExpExecArray | null;

  while ((m = re.exec(text)) !== null) {
    if (m.index > last) nodes.push(highlightFinancial(text.slice(last, m.index), last));
    const k = m.index;
    if (m[2]) {
      // \( inline math \)
      nodes.push(<MathBlock key={k} tex={m[2]} display={false} />);
    } else if (m[3]) {
      // **bold**
      nodes.push(<strong key={k} className="font-semibold text-white">{m[3]}</strong>);
    } else if (m[4]) {
      // *italic*
      nodes.push(<em key={k} className="italic text-muted-foreground">{m[4]}</em>);
    } else if (m[5]) {
      // `code`
      nodes.push(<code key={k} className="bg-white/[0.06] text-cyan/90 text-[13px] px-1.5 py-0.5 rounded font-mono">{m[5]}</code>);
    } else if (m[6] && m[7]) {
      // [text](url)
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

    // Display math block: \[ ... \] (may span multiple lines)
    if (trimmed.startsWith("\\[")) {
      const mathLines: string[] = [trimmed.slice(2)]; // rest of opening line
      i++;
      while (i < lines.length && !lines[i].includes("\\]")) {
        mathLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) {
        // closing line — take content before \]
        const closingLine = lines[i];
        const closingIdx = closingLine.indexOf("\\]");
        mathLines.push(closingLine.slice(0, closingIdx));
        i++;
      }
      blocks.push({ type: "math_display", content: mathLines.join("\n").trim() });
      continue;
    }

    // Display math block: $$ ... $$ (may span multiple lines)
    if (trimmed.startsWith("$$") && !trimmed.startsWith("$$$")) {
      const rest = trimmed.slice(2);
      // Check if closed on same line: $$ ... $$
      const closeIdx = rest.indexOf("$$");
      if (closeIdx >= 0) {
        blocks.push({ type: "math_display", content: rest.slice(0, closeIdx).trim() });
        i++;
        continue;
      }
      // Multi-line $$
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

    // Code block ```
    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trimStart().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      blocks.push({ type: "code_block", content: codeLines.join("\n"), lang });
      i++; // skip closing ```
      continue;
    }

    // Horizontal rule
    if (/^[-*_]{3,}\s*$/.test(trimmed)) {
      blocks.push({ type: "hr", content: "" });
      i++;
      continue;
    }

    // Headings
    if (trimmed.startsWith("### ")) { blocks.push({ type: "h3", content: trimmed.slice(4) }); i++; continue; }
    if (trimmed.startsWith("## "))  { blocks.push({ type: "h2", content: trimmed.slice(3) }); i++; continue; }
    if (trimmed.startsWith("# "))   { blocks.push({ type: "h1", content: trimmed.slice(2) }); i++; continue; }

    // Blockquote
    if (trimmed.startsWith("> ")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trimStart().startsWith("> ")) {
        quoteLines.push(lines[i].trimStart().slice(2));
        i++;
      }
      blocks.push({ type: "blockquote", content: quoteLines.join("\n") });
      continue;
    }

    // Bullet list (group consecutive)
    if (/^[-*]\s/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s/.test(lines[i].trimStart())) {
        items.push(lines[i].trimStart().slice(2));
        i++;
      }
      blocks.push({ type: "ul", content: "", items });
      continue;
    }

    // Numbered list (group consecutive)
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

    // Empty line
    if (!trimmed) { blocks.push({ type: "empty", content: "" }); i++; continue; }

    // Regular paragraph
    blocks.push({ type: "p", content: line });
    i++;
  }

  return blocks;
}

function renderBlocks(text: string): ReactNode[] {
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
   ChatMessage component
   ──────────────────────────────────────────────────────── */

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
  streamingContent?: string;
}

export default function ChatMessage({
  message,
  isStreaming = false,
  streamingContent,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isNudge = message.type === "nudge";
  const isDisclaimer = message.type === "disclaimer";

  /* ── typewriter state ── */
  const [displayedText, setDisplayedText] = useState("");
  const [showCursor, setShowCursor] = useState(false);
  const hasAnimatedRef = useRef(false);
  const isAssistant = !isUser && !isNudge && !isDisclaimer;

  useEffect(() => {
    if (message.skipAnimation) {
      setDisplayedText(message.content);
      hasAnimatedRef.current = true;
      return;
    }
    if (!isAssistant || hasAnimatedRef.current || isStreaming) {
      if (!hasAnimatedRef.current && !isStreaming) setDisplayedText(message.content);
      return;
    }
    hasAnimatedRef.current = true;
    setShowCursor(true);
    const text = message.content;
    let idx = 0;
    const interval = setInterval(() => {
      idx = Math.min(idx + 3, text.length);
      setDisplayedText(text.slice(0, idx));
      if (idx >= text.length) { clearInterval(interval); setShowCursor(false); }
    }, 12);
    return () => clearInterval(interval);
  }, [message.content, isAssistant, isStreaming, message.skipAnimation]);

  useEffect(() => {
    if (!isAssistant) setDisplayedText(message.content);
  }, [isAssistant, message.content]);

  /* ── disclaimer type ── */
  if (isDisclaimer) {
    return (
      <div className="px-5 py-2.5">
        <p className="text-[11px] text-muted-foreground/40 mono-data leading-relaxed text-center italic">
          {message.content}
        </p>
      </div>
    );
  }

  const textToRender = isStreaming ? (streamingContent || "") : displayedText;
  const cursorVisible = isStreaming || showCursor;

  /* ── user message ── */
  if (isUser) {
    return (
      <div className="px-5 py-4 animate-fade-in">
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-lg bg-accent/15 border border-accent/20 flex items-center justify-center shrink-0 mt-0.5">
            <span className="text-[10px] text-accent font-bold">U</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-semibold tracking-wider text-accent/80 mono-data">YOU</span>
              {message.timestamp && (
                <span className="text-[10px] text-muted-foreground/50 mono-data">{message.timestamp}</span>
              )}
            </div>
            <p className="text-[14px] text-white leading-relaxed">{textToRender}</p>
          </div>
        </div>
      </div>
    );
  }

  /* ── nudge message ── */
  if (isNudge) {
    return (
      <div className="px-5 py-4 animate-fade-in">
        <div className="rounded-lg border border-warning/20 bg-warning/[0.04] p-3.5">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-5 h-5 rounded bg-warning/20 flex items-center justify-center">
              <span className="text-[9px] text-warning font-bold">!</span>
            </div>
            <span className="text-[11px] font-semibold tracking-wider text-warning/80 mono-data">BEHAVIORAL NUDGE</span>
          </div>
          <div className="text-sm text-warning/70 leading-relaxed pl-7">
            {renderBlocks(textToRender)}
          </div>
        </div>
      </div>
    );
  }

  /* ── AI assistant message ── */
  return (
    <div className={cn("px-5 py-4 animate-fade-in", isStreaming && "bg-cyan/[0.02]")}>
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className={cn(
          "w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 border",
          isStreaming
            ? "bg-cyan/15 border-cyan/25"
            : "bg-profit/10 border-profit/20"
        )}>
          <span className={cn(
            "text-[9px] font-bold mono-data",
            isStreaming ? "text-cyan" : "text-profit"
          )}>AI</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className={cn(
              "text-[11px] font-semibold tracking-wider mono-data",
              isStreaming ? "text-cyan/80" : "text-profit/80"
            )}>TRADEIQ</span>
            {message.timestamp && (
              <span className="text-[10px] text-muted-foreground/50 mono-data">{message.timestamp}</span>
            )}
            {isStreaming && (
              <span className="flex items-center gap-1.5 ml-1">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan animate-pulse" />
                <span className="text-[10px] text-cyan/60 mono-data">LIVE</span>
              </span>
            )}
          </div>

          {/* Rich body */}
          <div className="text-muted leading-relaxed">
            {renderBlocks(textToRender)}
            {cursorVisible && (
              <span className="inline-block w-[2px] h-[14px] bg-cyan animate-pulse ml-0.5 -mb-[2px] rounded-full" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
