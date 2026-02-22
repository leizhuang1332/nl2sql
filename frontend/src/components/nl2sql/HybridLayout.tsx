'use client';

import React, { useState, useRef, useEffect } from 'react';

interface HybridLayoutProps {
  leftPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  defaultLeftWidth?: number;
  minLeftWidth?: number;
  minRightWidth?: number;
}

export const HybridLayout: React.FC<HybridLayoutProps> = ({
  leftPanel,
  rightPanel,
  defaultLeftWidth = 25,
  minLeftWidth = 20,
  minRightWidth = 40,
}) => {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;
      
      const containerRect = containerRef.current.getBoundingClientRect();
      const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
      
      if (newLeftWidth >= minLeftWidth && newLeftWidth <= (100 - minRightWidth)) {
        setLeftWidth(newLeftWidth);
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, minLeftWidth, minRightWidth]);

  return (
    <div ref={containerRef} className="flex h-full w-full">
      <div 
        style={{ width: `${leftWidth}%` }} 
        className="h-full bg-slate-900"
      >
        {leftPanel}
      </div>
      
      <div 
        onMouseDown={handleMouseDown}
        className={`w-1 bg-slate-700 hover:bg-green-500 transition-colors cursor-col-resize flex-shrink-0 ${isDragging ? 'bg-green-500' : ''}`}
      />
      
      <div 
        style={{ width: `${100 - leftWidth}%` }} 
        className="h-full bg-slate-900 flex-1"
      >
        {rightPanel}
      </div>
    </div>
  );
};

export default HybridLayout;
