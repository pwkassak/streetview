import React, { useEffect, useCallback, useRef } from 'react';
import { 
  Play, 
  Pause, 
  SkipForward, 
  SkipBack, 
  FastForward,
  Rewind,
  RotateCcw
} from 'lucide-react';
import './RoutePlayer.css';

interface RoutePlayerProps {
  totalSegments: number;
  currentSegment: number;
  isPlaying: boolean;
  playbackSpeed: number;
  onSegmentChange: (segment: number) => void;
  onPlayPause: () => void;
  onSpeedChange: (speed: number) => void;
  onReset: () => void;
  maxTraversals?: number;
}

const RoutePlayer: React.FC<RoutePlayerProps> = ({
  totalSegments,
  currentSegment,
  isPlaying,
  playbackSpeed,
  onSegmentChange,
  onPlayPause,
  onSpeedChange,
  onReset,
  maxTraversals = 1
}) => {
  const intervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Auto-advance when playing
  useEffect(() => {
    if (isPlaying && currentSegment < totalSegments - 1) {
      const delay = 500 / playbackSpeed; // Base delay of 500ms
      intervalRef.current = setTimeout(() => {
        onSegmentChange(currentSegment + 1);
      }, delay);
    } else if (isPlaying && currentSegment >= totalSegments - 1) {
      // Stop at the end
      onPlayPause();
    }

    return () => {
      if (intervalRef.current) {
        clearTimeout(intervalRef.current);
      }
    };
  }, [isPlaying, currentSegment, totalSegments, playbackSpeed, onSegmentChange, onPlayPause]);

  const handleStepForward = useCallback(() => {
    if (currentSegment < totalSegments - 1) {
      onSegmentChange(currentSegment + 1);
    }
  }, [currentSegment, totalSegments, onSegmentChange]);

  const handleStepBackward = useCallback(() => {
    if (currentSegment > 0) {
      onSegmentChange(currentSegment - 1);
    }
  }, [currentSegment, onSegmentChange]);

  const handleJumpForward = useCallback(() => {
    const newSegment = Math.min(currentSegment + 10, totalSegments - 1);
    onSegmentChange(newSegment);
  }, [currentSegment, totalSegments, onSegmentChange]);

  const handleJumpBackward = useCallback(() => {
    const newSegment = Math.max(currentSegment - 10, 0);
    onSegmentChange(newSegment);
  }, [currentSegment, onSegmentChange]);

  const handleSliderChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const segment = parseInt(e.target.value);
    onSegmentChange(segment);
  }, [onSegmentChange]);

  const speedOptions = [0.5, 1, 2, 4, 8];

  return (
    <div className="route-player">
      <div className="player-container">
        <h3 className="player-title">Route Player</h3>
        
        {/* Progress Info */}
        <div className="progress-info">
          <span className="segment-counter">
            Segment {currentSegment + 1} of {totalSegments}
          </span>
          <span className="speed-indicator">
            Speed: {playbackSpeed}x
          </span>
        </div>

        {/* Progress Slider */}
        <div className="progress-slider">
          <input
            type="range"
            min="0"
            max={totalSegments - 1}
            value={currentSegment}
            onChange={handleSliderChange}
            className="slider"
          />
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${((currentSegment + 1) / totalSegments) * 100}%` }}
            />
          </div>
        </div>

        {/* Control Buttons */}
        <div className="control-buttons">
          <button
            onClick={handleJumpBackward}
            disabled={currentSegment === 0}
            className="control-btn"
            title="Jump 10 segments backward"
          >
            <Rewind size={20} />
          </button>
          
          <button
            onClick={handleStepBackward}
            disabled={currentSegment === 0}
            className="control-btn"
            title="Previous segment"
          >
            <SkipBack size={20} />
          </button>
          
          <button
            onClick={onPlayPause}
            className="control-btn play-btn"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause size={24} /> : <Play size={24} />}
          </button>
          
          <button
            onClick={handleStepForward}
            disabled={currentSegment >= totalSegments - 1}
            className="control-btn"
            title="Next segment"
          >
            <SkipForward size={20} />
          </button>
          
          <button
            onClick={handleJumpForward}
            disabled={currentSegment >= totalSegments - 1}
            className="control-btn"
            title="Jump 10 segments forward"
          >
            <FastForward size={20} />
          </button>
          
          <button
            onClick={onReset}
            className="control-btn"
            title="Reset to beginning"
          >
            <RotateCcw size={20} />
          </button>
        </div>

        {/* Speed Controls */}
        <div className="speed-controls">
          <label>Playback Speed:</label>
          <div className="speed-buttons">
            {speedOptions.map(speed => (
              <button
                key={speed}
                onClick={() => onSpeedChange(speed)}
                className={`speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
              >
                {speed}x
              </button>
            ))}
          </div>
        </div>

        {/* Legend */}
        {maxTraversals > 1 && (
          <div className="traversal-legend">
            <h4>Traversal Legend</h4>
            <div className="legend-items">
              <div className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#0066CC' }}></span>
                <span>First Pass</span>
              </div>
              <div className="legend-item">
                <span className="legend-color" style={{ backgroundColor: '#FF9500' }}></span>
                <span>Second Pass</span>
              </div>
              {maxTraversals > 2 && (
                <div className="legend-item">
                  <span className="legend-color" style={{ backgroundColor: '#FF3B30' }}></span>
                  <span>Third+ Pass</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

    </div>
  );
};

export default RoutePlayer;