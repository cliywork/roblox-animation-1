import subprocess, json, time, os, sys, base64
from PIL import Image
import io

MCP_PATH = os.path.expandvars(r'%LOCALAPPDATA%\Roblox\Versions\version-7aaa6838d36c4448\StudioMCP.exe')
FFMPEG_PATH = 'ffmpeg'  # must be on PATH
FRAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frames')
OUT_VIDEO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'roblox_titan_battle_animation_24fps.mp4')

FPS = 24
TOTAL_DURATION = 82.593  # Total scene duration in seconds
TOTAL_FRAMES = int(round(TOTAL_DURATION * FPS)) + 1  # 1983 frames
DELAY_SEC = 0.5  # 0.5s quality delay requested by user

os.makedirs(FRAMES_DIR, exist_ok=True)

class McpClient:
    def __init__(self):
        self.proc = None
        self.msg_id = 0
        self.studio_id = None
        self.start()

    def start(self):
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.proc = subprocess.Popen(
            [MCP_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.msg_id = 0
        self.call("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "studio_animation_renderer", "version": "1.0"},
            "capabilities": {}
        })
        self.resolve_studio()

    def resolve_studio(self):
        res = self.call("tools/call", {
            "name": "list_roblox_studios",
            "arguments": {}
        })
        if res and 'result' in res:
            content = res['result'].get('content', [])
            for c in content:
                if c.get('type') == 'text':
                    data = json.loads(c.get('text', '{}'))
                    studios = data.get('studios', [])
                    if studios:
                        self.studio_id = studios[0]['id']
                        print(f"Connected to Studio ID: {self.studio_id} ({studios[0].get('name')})")
                        return
        print("Warning: Could not resolve studio_id automatically.")

    def call(self, method, params=None):
        self.msg_id += 1
        req = {"jsonrpc": "2.0", "id": self.msg_id, "method": method}
        if params:
            req["params"] = params
        try:
            self.proc.stdin.write(json.dumps(req) + '\n')
            self.proc.stdin.flush()
            line = self.proc.stdout.readline()
            if line:
                return json.loads(line)
        except Exception as e:
            print(f"MCP Call error: {e}, restarting MCP process...")
            self.start()
        return None

    def close(self):
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass

mcp = McpClient()

# Count already completed frames
existing_frames = sorted([f for f in os.listdir(FRAMES_DIR) if f.endswith('.png')])
start_from = len(existing_frames) + 1
if existing_frames:
    last_frame_num = int(existing_frames[-1].replace('.png', ''))
    start_from = last_frame_num + 1

print(f"=== ROBLOX STUDIO ANIMATION RESUME RENDERER ===")
print(f"Total target frames: {TOTAL_FRAMES} ({TOTAL_DURATION:.2f}s @ {FPS} fps)")
print(f"Existing frames:     {len(existing_frames)} (last: {existing_frames[-1] if existing_frames else 'none'})")
print(f"Resuming from frame: {start_from:05d}")
print(f"Delay per image:     {DELAY_SEC}s")
print(f"Output frames dir:   {FRAMES_DIR}")
print(f"Final video path:    {OUT_VIDEO}")
print("================================================\n")

start_time = time.time()
captured_count = 0

for frame_idx in range(1, TOTAL_FRAMES + 1):
    out_file = os.path.join(FRAMES_DIR, f"{frame_idx:05d}.png")

    # Resumable check
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
        continue

    movie_frame = frame_idx - 1
    movie_sec = movie_frame / FPS

    # 1. Scrub to exact frame
    scrub_code = f'game.ReplicatedStorage:SetAttribute("ScrubFrame", {movie_frame})\nreturn true'
    mcp.call("tools/call", {
        "name": "execute_luau",
        "arguments": {
            "studio_id": mcp.studio_id,
            "datamodel_type": "Server",
            "code": scrub_code
        }
    })

    # 2. Quality settle delay
    time.sleep(DELAY_SEC)

    # 3. Screen capture
    cap_res = mcp.call("tools/call", {
        "name": "screen_capture",
        "arguments": {
            "studio_id": mcp.studio_id,
            "capture_id": f"render_{frame_idx}"
        }
    })

    # 4. Save PNG
    saved = False
    if cap_res and 'result' in cap_res:
        content = cap_res['result'].get('content', [])
        for item in content:
            if item.get('type') == 'image':
                img_data = base64.b64decode(item['data'])
                img = Image.open(io.BytesIO(img_data))
                img.save(out_file, "PNG")
                saved = True
                break

    if not saved:
        print(f"Warning: Failed to capture frame {frame_idx:05d}, retrying once...")
        time.sleep(1.0)
        cap_res = mcp.call("tools/call", {
            "name": "screen_capture",
            "arguments": {
                "studio_id": mcp.studio_id,
                "capture_id": f"retry_{frame_idx}"
            }
        })
        if cap_res and 'result' in cap_res:
            content = cap_res['result'].get('content', [])
            for item in content:
                if item.get('type') == 'image':
                    img_data = base64.b64decode(item['data'])
                    img = Image.open(io.BytesIO(img_data))
                    img.save(out_file, "PNG")
                    saved = True
                    break

    captured_count += 1

    # Progress log every 24 frames (1 second of animation)
    if frame_idx % 24 == 0 or frame_idx == TOTAL_FRAMES:
        elapsed = time.time() - start_time
        fps_actual = captured_count / max(1, elapsed)
        remaining = TOTAL_FRAMES - frame_idx
        eta_sec = remaining / max(0.01, fps_actual)
        print(f"[{frame_idx:04d}/{TOTAL_FRAMES}] {movie_sec:5.2f}s / {TOTAL_DURATION:5.2f}s | "
              f"Batch: {captured_count} | Elapsed: {elapsed/60:4.1f}m | ETA: {eta_sec/60:4.1f}m")

# Clean up ScrubFrame in Studio
mcp.call("tools/call", {
    "name": "execute_luau",
    "arguments": {
        "studio_id": mcp.studio_id,
        "datamodel_type": "Server",
        "code": 'game.ReplicatedStorage:SetAttribute("ScrubFrame", nil)\nreturn true'
    }
})
mcp.close()

print("\nAll frames captured successfully!")
print(f"Session capture time: {(time.time() - start_time)/60:.2f} minutes")

# 5. Combine into single video with FFmpeg
print("\nCombining frames into high quality 24 fps video with FFmpeg...")
ffmpeg_cmd = [
    FFMPEG_PATH, '-y',
    '-framerate', '24',
    '-i', os.path.join(FRAMES_DIR, '%05d.png'),
    '-c:v', 'libx264',
    '-crf', '17',
    '-preset', 'slow',
    '-pix_fmt', 'yuv420p',
    OUT_VIDEO
]
subprocess.run(ffmpeg_cmd, check=True)
print(f"\nFinal Video Generated: {OUT_VIDEO}")

# Verify output video
probe_cmd = [FFMPEG_PATH, '-i', OUT_VIDEO]
res = subprocess.run(probe_cmd, capture_output=True, text=True)
for line in res.stderr.splitlines():
    if 'Duration:' in line or 'Stream #0:0' in line:
        print(line.strip())

print("\nRender pipeline complete!")
