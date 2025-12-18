'use client';

import { useEffect, useState } from 'react';

interface MarimoIframeProps {
  notebookName: string;
  marimoPort?: number;
}

export default function MarimoIframe({ notebookName, marimoPort = 8000 }: MarimoIframeProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  // Remove .py extension if present, and construct URL
  const notebookPath = notebookName.replace(/\.py$/, '');
  const marimoUrl = `http://localhost:${marimoPort}/${notebookPath}`;

  useEffect(() => {
    setIsLoading(true);
    setHasError(false);
  }, [notebookName]);

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    setIsLoading(false);
    setHasError(true);
  };

  return (
    <div className="h-full w-full relative bg-white">
      {isLoading && !hasError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-white z-10">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <div className="text-gray-500 font-medium">Loading notebook...</div>
        </div>
      )}
      {hasError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-white z-10 p-8">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="text-red-600 font-semibold text-lg mb-2">Failed to load notebook</div>
          <div className="text-gray-600 text-sm mb-6 text-center max-w-md">
            Make sure the marimo server is running on port {marimoPort}
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-left max-w-md w-full">
            <div className="text-xs font-semibold text-gray-500 mb-2">Expected URL:</div>
            <code className="text-xs text-gray-700 break-all">{marimoUrl}</code>
          </div>
          <div className="mt-6 text-gray-500 text-sm">
            Run: <code className="bg-gray-100 px-2 py-1 rounded text-xs">uv run python serve_notebooks.py</code> from the <code className="bg-gray-100 px-2 py-1 rounded text-xs">community/ddp</code> directory
          </div>
        </div>
      )}
      <iframe
        src={marimoUrl}
        className="w-full h-full border-0"
        onLoad={handleLoad}
        onError={handleError}
        title={notebookName}
      />
    </div>
  );
}
