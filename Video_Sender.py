import asyncio
import cv2
from livekit import rtc
from LiveKitClient import LiveKitClient

camera_index = 1
capture_fps = 30
# capture_resolution = (800, 600)
capture_resolution = (1280, 720)
# capture_resolution = (1920, 1080)
preview_resolution = (1920, 1080)

async def video_capture(captured_frames: asyncio.Queue, show_preview: bool = False, stop_event: asyncio.Event = None):
    print(f"Starting Capture {camera_index}...")
    cap = await asyncio.to_thread(cv2.VideoCapture, camera_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, capture_resolution[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, capture_resolution[1])
    cap.set(cv2.CAP_PROP_FPS, capture_fps)
    print(f"Capture {camera_index} started")

    windowName = 'Stereoscopic Preview'
    fullscreen = False
    if show_preview:
        cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
    while not stop_event.is_set():
        await asyncio.sleep(0)
        ret, frame = await asyncio.to_thread(cap.read)
        if not ret:
            break
        if not captured_frames.empty():
            try:
                captured_frames.get_nowait()  # Discard the old frame
            except:
                pass
        await captured_frames.put(frame)

        if show_preview:
            display_frame = cv2.resize(frame, preview_resolution)
            cv2.imshow(windowName, display_frame)
        
            key = cv2.waitKey(1) & 0xFF
            if key == ord('f'):
                fullscreen = not fullscreen
            elif key == ord('q'):
                break

            if cv2.getWindowProperty(windowName, cv2.WND_PROP_VISIBLE) < 1:
                break

            if fullscreen:
                cv2.setWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"Capture {camera_index} stopped")

    stop_event.set()


async def lk_video_sender(captured_framed: asyncio.Queue, stop_event: asyncio.Event):
    client = LiveKitClient("VIDEO_SENDER", "NEW_ROOM")
    await client.isConnected.wait()
    print("Connected to LiveKit Server")
    source = rtc.VideoSource(capture_resolution[0], capture_resolution[1])
    track = rtc.LocalVideoTrack.create_video_track("hue", source)
    options = rtc.TrackPublishOptions()
    options.source = rtc.TrackSource.SOURCE_CAMERA
    await client.room.local_participant.publish_track(track, options)
    print(f"Published Track: {track.sid}")
    while not stop_event.is_set():
        frame = await captured_framed.get()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        lk_frame = rtc.VideoFrame(frame.shape[1], frame.shape[0], rtc.VideoBufferType.RGBA, frame.tobytes())
        source.capture_frame(lk_frame)
        # print(await track.get_stats())
        # print("_______________")
        
    await client.close()
    print("LiveKit Video Sender Stopped")


async def main():
    stop_event = asyncio.Event()
    captured_frames = asyncio.Queue(maxsize=2)

    video_capture_task = asyncio.create_task(video_capture(captured_frames, show_preview = True, stop_event = stop_event))
    lk_video_sender_task = asyncio.create_task(lk_video_sender(captured_frames, stop_event))

    await video_capture_task
    await lk_video_sender_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Ctrl-C Pressed, Exiting...")