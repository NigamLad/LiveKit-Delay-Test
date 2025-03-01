import os
import asyncio
from livekit import api, rtc
from typing import Union
from uuid import uuid4
import numpy as np
from dotenv import load_dotenv
load_dotenv(override=True)


class LiveKitClient():
    def __init__(self, user, room, key=os.environ["LIVEKIT_API_KEY"], secret=os.environ["LIVEKIT_API_SECRET"]) -> None:
        self.room = room
        self.user = user
        self.key = key
        self.secret = secret
        self.token = self.generateToken()
        self.room = rtc.Room()
        self.isConnected = asyncio.Event()
        self.exit = asyncio.Event()
        self.receiveQueue = asyncio.Queue(maxsize=2)
        self.frameQueue = asyncio.Queue(maxsize=2)

        asyncio.create_task(self.mainEventLoop())

    async def close(self):
        try:
            print("Closing LiveKitClient")
            await self.room.disconnect()
            self.exit.set()
        except Exception as e:
            pass


    def generateToken(self):
        return (
            api.AccessToken(self.key, self.secret)
            .with_identity(str(uuid4()))
            .with_name(self.user)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=self.room,
                )
            )
            .to_jwt()
        )
    
    async def send_message(self, msg):
        await self.room.local_participant.publish_data(msg, reliable=False)

    async def mainEventLoop(self):
        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant) -> None:
            print(f"[{participant.sid}] - {participant.name} connected", participant.sid, participant.name)

        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            print(f"[{participant.sid}] - {participant.name} disconnected", participant.sid, participant.name)

        # @self.room.on("local_track_published")
        # def on_local_track_published(
        #     publication: rtc.LocalTrackPublication,
        #     track: Union[rtc.LocalAudioTrack, rtc.LocalVideoTrack],
        # ):
        #     print(f"local track published: {publication.sid}")

        # @self.room.on("active_speakers_changed")
        # def on_active_speakers_changed(speakers: list[rtc.Participant]):
        #     print(f"active speakers changed: {speakers}")

        # @self.room.on("local_track_unpublished")
        # def on_local_track_unpublished(publication: rtc.LocalTrackPublication):
        #     print(f"local track unpublished: {publication.name}")

        # @self.room.on("track_published")
        # def on_track_published(
        #     publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
        # ):
        #     print(f"track published: {publication.sid} from participant {participant.sid} ({participant.name})")

        # @self.room.on("track_unpublished")
        # def on_track_unpublished(
        #     publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
        # ):
        #     print(f"track unpublished: {publication.sid}")

        @self.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            print(f"track subscribed: {publication.sid}")
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                _video_stream = rtc.VideoStream(track)
                # video_stream is an async iterator that yields VideoFrame
                print(f"track subscribed: {publication.sid}")
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                _video_stream = rtc.VideoStream(track, format=rtc.VideoBufferType.RGBA)
                # video_stream is an async iterator that yields VideoFrame
                
                async def get_frames(_video_stream):
                    async for frame_event in _video_stream:
                        buffer = frame_event.frame
                        print(buffer)
                        arr = np.frombuffer(buffer.data, dtype=np.uint8)
                        arr = arr.reshape((buffer.height, buffer.width, 4))
                        try:
                            self.frameQueue.put_nowait(arr)
                        except asyncio.QueueFull:
                            self.frameQueue.get_nowait()
                            self.frameQueue.put_nowait(arr)

                asyncio.create_task(get_frames(_video_stream))
            elif track.kind == rtc.TrackKind.KIND_AUDIO:
                print("Subscribed to an Audio Track")
                _audio_stream = rtc.AudioStream(track)
                # audio_stream is an async iterator that yields AudioFrame

        # @self.room.on("track_unsubscribed")
        # def on_track_unsubscribed(
        #     track: rtc.Track,
        #     publication: rtc.RemoteTrackPublication,
        #     participant: rtc.RemoteParticipant,
        # ):
        #     print(f"track unsubscribed: {publication.sid}")

        # @self.room.on("track_muted")
        # def on_track_muted(
        #     publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
        # ):
        #     print(f"track muted: {publication.sid}")

        # @self.room.on("track_unmuted")
        # def on_track_unmuted(
        #     publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
        # ):
        #     print(f"track unmuted: {publication.sid}")

        @self.room.on("data_received")
        def on_data_received(data: rtc.DataPacket):
            msg = data.data
            try:
                self.receiveQueue.put_nowait(msg)
            except asyncio.QueueFull:
                self.receiveQueue.get_nowait()
                self.receiveQueue.put_nowait(msg)
                
        @self.room.on("connection_quality_changed")
        def on_connection_quality_changed(
            participant: rtc.Participant, quality: rtc.ConnectionQuality
        ):
            print(f"connection quality changed for {participant.name} - {rtc.ConnectionQuality.Name(quality)}")

        @self.room.on("track_subscription_failed")
        def on_track_subscription_failed(
            participant: rtc.RemoteParticipant, track_sid: str, error: str
        ):
            print(f"track subscription failed: {participant.name} {error}")

        @self.room.on("connection_state_changed")
        def on_connection_state_changed(state: rtc.ConnectionState):
            print(f"connection state changed: {rtc.ConnectionState.Name(state)}")
            if state == rtc.ConnectionState.CONN_CONNECTED:
                self.isConnected.set()
            else:
                self.isConnected.clear()

        # @self.room.on("connected")
        # def on_connected() -> None:
        #     print("connected")
        #     self.isConnected.set()

        # @self.room.on("disconnected")
        # def on_disconnected() -> None:
        #     print("disconnected")
        #     self.isConnected.clear()

        # @self.room.on("reconnecting")
        # def on_reconnecting() -> None:
        #     print("reconnecting...")

        # @self.room.on("reconnected")
        # def on_reconnected() -> None:
        #     print("reconnected")

        print("Connecting to server...")
        await self.room.connect(os.getenv("LIVEKIT_URL"), self.token)
        print(f"connected to room {self.room.name}")
        print(f"participants: {self.room.remote_participants}")

        await self.exit.wait()

        

