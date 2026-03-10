import mss
import mss.tools
from pathlib import Path

def capture_screen(output_path: str | Path = "screenshot.png") -> Path:
    """
    Captures the primary monitor and saves it to the specified path.
    """
    with mss.mss() as sct:
        # monitor 1 is usually the primary monitor
        monitor = sct.monitors[1]
        
        # Grab the data
        sct_img = sct.grab(monitor)

        # Save to the picture file
        output_file = Path(output_path)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(output_file))
        return output_file

if __name__ == "__main__":
    path = capture_screen("test_capture.png")
    print(f"Captured screenshot to: {path}")
