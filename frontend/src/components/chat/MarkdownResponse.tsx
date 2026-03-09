"use client";

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

const heading = "font-bold text-white tracking-tight";
const link = "text-accent-red no-underline hover:underline";

const components = {
  h1: ({ children }) => <h1 className={`${heading} text-2xl mt-6 mb-3 first:mt-0`}>{children}</h1>,
  h2: ({ children }) => <h2 className={`${heading} text-xl mt-5 mb-2 first:mt-0`}>{children}</h2>,
  h3: ({ children }) => <h3 className={`${heading} text-lg mt-4 mb-2 first:mt-0`}>{children}</h3>,
  p: ({ children }) => <p className="my-3 text-gray-200 leading-relaxed first:mt-0 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="my-3 list-disc pl-6 space-y-1 text-gray-200">{children}</ul>,
  ol: ({ children }) => <ol className="my-3 list-decimal pl-6 space-y-1 text-gray-200">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
  a: ({ href, children }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className={link}>
      {children}
    </a>
  ),
  code: ({ className, children }) => {
    const isBlock = className?.includes("language-");
    if (isBlock) {
      return <code className="block text-gray-200 font-mono">{children}</code>;
    }
    return (
      <code className="bg-surface-700 text-gray-200 px-1.5 py-0.5 rounded text-sm font-mono">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-lg bg-surface-800 border border-surface-600 p-4 text-sm text-gray-200">
      {children}
    </pre>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-accent-red pl-4 my-3 italic text-gray-300">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <div className="my-4 overflow-x-auto rounded-lg border border-surface-600">
      <table className="min-w-full text-left text-sm text-gray-200">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-surface-800">{children}</thead>,
  th: ({ children }) => (
    <th className="px-4 py-2 font-semibold text-white border-b border-surface-600">{children}</th>
  ),
  tbody: ({ children }) => <tbody>{children}</tbody>,
  tr: ({ children }) => <tr className="border-b border-surface-700 last:border-0">{children}</tr>,
  td: ({ children }) => <td className="px-4 py-2">{children}</td>,
};

interface MarkdownResponseProps {
  content: string;
  className?: string;
}

/**
 * Renders AI response as markdown with dark-theme styling.
 * Supports GFM: headings, lists, bold, links, code, blockquotes, tables.
 */
export function MarkdownResponse({ content, className = "" }: MarkdownResponseProps) {
  return (
    <div className={`text-gray-200 leading-relaxed ${className}`.trim()}>
      <Markdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </Markdown>
    </div>
  );
}
