import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { API_BASE } from "../config";

const createComponents = (
  onImageClick?: (src: string, alt?: string) => void,
) => ({
  code({ className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || "");
    return match ? (
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={match[1]}
        PreTag="div"
        customStyle={{ margin: 0, borderRadius: "0.5rem", fontSize: "0.8rem" }}
      >
        {String(children).replace(/\n$/, "")}
      </SyntaxHighlighter>
    ) : (
      <code
        className="px-1.5 py-0.5 rounded text-xs font-mono"
        style={{ backgroundColor: "var(--code-bg)", color: "var(--code-text)" }}
        {...props}
      >
        {children}
      </code>
    );
  },
  p: ({ children }: any) => (
    <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
  ),
  h1: ({ children }: any) => (
    <h1 className="text-xl font-bold mb-2 mt-1">{children}</h1>
  ),
  h2: ({ children }: any) => (
    <h2 className="text-lg font-bold mb-2 mt-1">{children}</h2>
  ),
  h3: ({ children }: any) => (
    <h3 className="text-base font-bold mb-1 mt-1">{children}</h3>
  ),
  ul: ({ children }: any) => (
    <ul
      className="list-disc pl-4 mb-2 space-y-1"
      style={{ color: "var(--text-primary)" }}
    >
      {children}
    </ul>
  ),
  ol: ({ children }: any) => (
    <ol
      className="list-decimal pl-4 mb-2 space-y-1"
      style={{ color: "var(--text-primary)" }}
    >
      {children}
    </ol>
  ),
  li: ({ children }: any) => <li className="leading-relaxed">{children}</li>,
  a: ({ href, children }: any) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      style={{ color: "var(--accent-primary)" }}
      className="underline hover:opacity-80"
    >
      {children}
    </a>
  ),
  img: ({ src, alt, node }: any) => {
    // ReactMarkdown v9+ passes props differently; fall back to node.properties
    const imageSrc = src || node?.properties?.src || "";
    const imageAlt = alt || node?.properties?.alt || "";
    if (!imageSrc) return null;
    // Convert relative upload URLs to absolute URLs using the API server origin
    let imageUrl = imageSrc;
    if (imageSrc.startsWith("/uploads/")) {
      const apiUrl = new URL(API_BASE, window.location.href);
      imageUrl = `${apiUrl.origin}${imageSrc}`;
    }
    return (
      <img
        src={imageUrl}
        alt={imageAlt || "image"}
        className="max-w-full max-h-64 rounded-lg cursor-zoom-in hover:opacity-90 transition-opacity my-1 block"
        onClick={() => onImageClick?.(imageUrl, imageAlt)}
        onError={(e) => {
          const img = e.target as HTMLImageElement;
          img.style.display = "none";
        }}
      />
    );
  },
  blockquote: ({ children }: any) => (
    <blockquote
      className="border-l-2 pl-3 my-2 italic"
      style={{
        borderColor: "var(--accent-primary)",
        color: "var(--text-secondary)",
      }}
    >
      {children}
    </blockquote>
  ),
  hr: () => (
    <hr className="my-3" style={{ borderColor: "var(--border-color)" }} />
  ),
  table: ({ children }: any) => (
    <div className="overflow-x-auto my-2">
      <table
        className="w-full text-xs border-collapse"
        style={{ borderColor: "var(--table-border)" }}
      >
        {children}
      </table>
    </div>
  ),
  thead: ({ children }: any) => (
    <thead style={{ backgroundColor: "var(--table-head-bg)" }}>
      {children}
    </thead>
  ),
  th: ({ children }: any) => (
    <th
      className="px-2 py-1 text-left"
      style={{ border: "1px solid var(--table-border)" }}
    >
      {children}
    </th>
  ),
  td: ({ children }: any) => (
    <td
      className="px-2 py-1"
      style={{ border: "1px solid var(--table-border)" }}
    >
      {children}
    </td>
  ),
});

interface MemoizedMarkdownProps {
  content: string;
  onImageClick?: (src: string, alt?: string) => void;
}

// Encode spaces in Markdown image URLs so remark can parse them correctly.
// Handles nested parentheses in URLs by counting brace depth.
function encodeImageUrls(content: string): string {
  if (typeof content !== "string") return "";
  let result = "";
  let i = 0;
  while (i < content.length) {
    const start = content.indexOf("![", i);
    if (start === -1) {
      result += content.slice(i);
      break;
    }
    result += content.slice(i, start);
    const altEnd = content.indexOf("](", start + 2);
    if (altEnd === -1) {
      result += content.slice(start);
      break;
    }
    const alt = content.slice(start + 2, altEnd);
    const urlStart = altEnd + 2;
    let depth = 1;
    let urlEnd = urlStart;
    while (urlEnd < content.length && depth > 0) {
      if (content[urlEnd] === "(") depth++;
      else if (content[urlEnd] === ")") depth--;
      urlEnd++;
    }
    if (depth !== 0) {
      result += content.slice(start);
      break;
    }
    const url = content.slice(urlStart, urlEnd - 1).replace(/ /g, "%20");
    result += `![${alt}](${url})`;
    i = urlEnd;
  }
  return result;
}

export const MemoizedMarkdown = React.memo(
  ({ content, onImageClick }: MemoizedMarkdownProps) => {
    const processedContent = encodeImageUrls(content);
    return (
      <div className="markdown-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkBreaks]}
          components={createComponents(onImageClick)}
        >
          {processedContent}
        </ReactMarkdown>
      </div>
    );
  },
);
