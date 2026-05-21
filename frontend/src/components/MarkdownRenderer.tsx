import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

const markdownComponents = {
  code({ className, children, ...props }: any) {
    const match = /language-(\w+)/.exec(className || '')
    return match ? (
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={match[1]}
        PreTag="div"
        customStyle={{ margin: 0, borderRadius: '0.5rem', fontSize: '0.8rem' }}
      >
        {String(children).replace(/\n$/, '')}
      </SyntaxHighlighter>
    ) : (
      <code className="px-1.5 py-0.5 rounded text-xs font-mono" style={{ backgroundColor: 'var(--code-bg)', color: 'var(--code-text)' }} {...props}>
        {children}
      </code>
    )
  },
  p: ({ children }: any) => <p className="mb-1 last:mb-0">{children}</p>,
  h1: ({ children }: any) => <h1 className="text-lg font-bold mb-1">{children}</h1>,
  h2: ({ children }: any) => <h2 className="text-base font-bold mb-1">{children}</h2>,
  h3: ({ children }: any) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
  ul: ({ children }: any) => <ul className="list-disc pl-4 mb-1">{children}</ul>,
  ol: ({ children }: any) => <ol className="list-decimal pl-4 mb-1">{children}</ol>,
  li: ({ children }: any) => <li className="mb-0.5">{children}</li>,
  a: ({ href, children }: any) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#00d4aa] underline hover:opacity-80">
      {children}
    </a>
  ),
  blockquote: ({ children }: any) => (
    <blockquote className="border-l-2 border-[#00d4aa] pl-3 my-1 italic" style={{ color: 'var(--text-secondary)' }}>{children}</blockquote>
  ),
  hr: () => <hr className="my-2" style={{ borderColor: 'var(--border-color)' }} />,
  table: ({ children }: any) => (
    <div className="overflow-x-auto my-1">
      <table className="w-full text-xs border-collapse" style={{ borderColor: 'var(--table-border)' }}>{children}</table>
    </div>
  ),
  thead: ({ children }: any) => <thead style={{ backgroundColor: 'var(--table-head-bg)' }}>{children}</thead>,
  th: ({ children }: any) => <th className="px-2 py-1 text-left" style={{ border: '1px solid var(--table-border)' }}>{children}</th>,
  td: ({ children }: any) => <td className="px-2 py-1" style={{ border: '1px solid var(--table-border)' }}>{children}</td>,
}

export const MemoizedMarkdown = React.memo(({ content }: { content: string }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
    {content}
  </ReactMarkdown>
))
