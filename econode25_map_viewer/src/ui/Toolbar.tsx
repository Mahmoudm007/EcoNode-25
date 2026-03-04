interface ToolbarProps {
  onScreenshot: () => void;
  onDownload: () => void;
  onSaveView: () => void;
}

export function Toolbar({ onScreenshot, onDownload, onSaveView }: ToolbarProps) {
  return (
    <div className="panel toolbar-panel">
      <button onClick={onScreenshot}>Save Screenshot</button>
      <button onClick={onDownload}>Download Data Package</button>
      <button onClick={onSaveView}>Save View State</button>
    </div>
  );
}
