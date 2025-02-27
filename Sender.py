import asyncio
import time
import random
import numpy as np
from LiveKitClient import LiveKitClient

async def lk_sender():
    client = LiveKitClient("TEST SENDER", "NEW_ROOM")
    await client.isConnected.wait()
    await asyncio.sleep(2)
    for i in range(1000):
        item = float(i)
        timestamp = time.perf_counter_ns()
        motion_data = [item, timestamp] + [random.random() for _ in range(15)]
        data = np.array(motion_data, dtype=np.double).tobytes()
        await client.send_message(data)
        # print("Sent message: ", motion_data)

    # await asyncio.sleep(1)
    await client.close()
    print("Client Closed")

async def main():
    await asyncio.create_task(lk_sender())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Ctrl-C pressed. Exiting...") 
    