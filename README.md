# Live Kit Delay Test
This repo contains two python programs that are designed to test the delay of sending data through LiveKit. The Sender and Receiver can be run on the same computer, or different computers.

`Sender.py` will create an array or 17 values, where the first value is just an index, the second is a timestamp integer in nanoseconds, and the rest are random floats between 0 and 1. The array is encoded as a byte array of doubles. By default the sender will connect to the room, send 1000 messages, then disconnect. The amount ofmessages can be modified as needed.

`Receiver.py` will connect to the room and wait for messages, upon receiving a message, it will decode the whole array, and extract the first two indices to display the index, and a calculated delay by using the timestamp.

*NOTE: The calculation for delay may not be 100% accurate since the `time.perf_counter_ns()` function will return different values, especially when `Sender.py` and `Receiver.py` are run on different computers, but it will be close enough*

# Setup

## Set credentials for LiveKit
Fill in the environment variables in `.env`

## Create Python environment
The latest version of python is recommended. This was developped using 3.9.12

### Creating the environment
```
python -m venv .venv
```
### Activating the environment
For Windows:
```
.\.venv\Scripts\activate
```

For Linux
```
source .venv\bin\activate
```

### Run the Receiver
```
python .\Receiver.py
```

### Run the Receiver
```
python .\Sender.py  
```