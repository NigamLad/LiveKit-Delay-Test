from livekit import rtc
import cv2
import asyncio
import os
from LiveKitClient import LiveKitClient
import numpy as np

def display_frames(frame_queue, stop_event):
    fullscreen = False
    windowName = 'Stereoscopic Stream'
    cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
    prev_timestamp = None
    while not stop_event.is_set():
        if not frame_queue.empty():
            frame_event = frame_queue.get()
            if frame_event is None:
                break

            buffer = frame_event.frame
            arr = np.frombuffer(buffer.data, dtype=np.uint8)
            arr = arr.reshape((buffer.height, buffer.width, 4))
            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

            try:
                # Calculate fps
                current_timestamp = frame_event.timestamp_us
                if prev_timestamp is not None:
                    fps = 1 / ((current_timestamp - prev_timestamp) / 1000000)
                    cv2.putText(arr, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 1)
                prev_timestamp = current_timestamp
            except:
                pass

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord('f'):
                fullscreen = not fullscreen

            if cv2.getWindowProperty(windowName, cv2.WND_PROP_VISIBLE) < 1:
                break

            if fullscreen:
                cv2.setWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

            cv2.imshow(windowName, arr)

    cv2.destroyAllWindows()

async def lk_video_receiver():
    client = LiveKitClient("VIDEO_RECEIVER", "NEW_ROOM")
    await client.isConnected.wait()
    print("Connected to LiveKit Server")

    fullscreen = False
    windowName = 'Stereoscopic Stream'
    cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
    while True:
        frame = await client.frameQueue.get()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord('f'):
            fullscreen = not fullscreen

        if cv2.getWindowProperty(windowName, cv2.WND_PROP_VISIBLE) < 1:
            break

        if fullscreen:
            cv2.setWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty(windowName, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)

        cv2.imshow(windowName, frame)


async def main():
    lk_video_receiver_task = asyncio.create_task(lk_video_receiver())
    await lk_video_receiver_task

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Ctrl-C Pressed, Exiting...")