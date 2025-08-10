import React from 'react';
import './DrawingToolbar.css';

export type DrawingMode = 'none' | 'rectangle' | 'circle' | 'polygon';

interface DrawingToolbarProps {
  mode: DrawingMode;
  onModeChange: (mode: DrawingMode) => void;
  onClear: () => void;
}

const DrawingToolbar: React.FC<DrawingToolbarProps> = ({ mode, onModeChange, onClear }) => {
  return (
    <div className="drawing-toolbar">
      <button
        className={`toolbar-btn ${mode === 'rectangle' ? 'active' : ''}`}
        onClick={() => onModeChange(mode === 'rectangle' ? 'none' : 'rectangle')}
        title="Draw Rectangle"
      >
        <svg width="20" height="20" viewBox="0 0 20 20">
          <rect x="3" y="5" width="14" height="10" fill="none" stroke="currentColor" strokeWidth="2"/>
        </svg>
      </button>
      
      <button
        className={`toolbar-btn ${mode === 'circle' ? 'active' : ''}`}
        onClick={() => onModeChange(mode === 'circle' ? 'none' : 'circle')}
        title="Draw Circle"
      >
        <svg width="20" height="20" viewBox="0 0 20 20">
          <circle cx="10" cy="10" r="7" fill="none" stroke="currentColor" strokeWidth="2"/>
        </svg>
      </button>
      
      <button
        className={`toolbar-btn ${mode === 'polygon' ? 'active' : ''}`}
        onClick={() => onModeChange(mode === 'polygon' ? 'none' : 'polygon')}
        title="Draw Polygon"
      >
        <svg width="20" height="20" viewBox="0 0 20 20">
          <polygon points="10,3 17,8 15,16 5,16 3,8" fill="none" stroke="currentColor" strokeWidth="2"/>
        </svg>
      </button>
      
      <div className="toolbar-separator"></div>
      
      <button
        className="toolbar-btn clear-btn"
        onClick={onClear}
        title="Clear Drawings"
      >
        <svg width="20" height="20" viewBox="0 0 20 20">
          <line x1="5" y1="5" x2="15" y2="15" stroke="currentColor" strokeWidth="2"/>
          <line x1="15" y1="5" x2="5" y2="15" stroke="currentColor" strokeWidth="2"/>
        </svg>
      </button>
    </div>
  );
};

export default DrawingToolbar;