import asyncio
import time
import numpy as np
from LiveKitClient import LiveKitClient

async def lk_receiver():
    client = LiveKitClient("TEST RECEIVER", "NEW_ROOM")
    await client.isConnected.wait()
    print("Client connected")

    print("Waiting for messages...")
    while True:
        data = await client.receiveQueue.get()
        msg = np.frombuffer(data, dtype=np.double)
        current_time = time.perf_counter_ns()
        item, timestamp = int(msg[0]), int(msg[1])
        delay_ns = current_time - timestamp
        delay_ms = delay_ns / 1_000_000
        print(f"Item: {item}\t\tDelay: {delay_ms} ms")

async def main():
    await asyncio.create_task(lk_receiver())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Ctrl-C pressed. Exiting...") 