import asyncio
import json
import sys
import websockets

class GatewayClient:
    """Manages the raw connection to the Discord Gateway using WebSockets."""
    def __init__(self, token, callback):
        self.token = token
        self.callback = callback
        self.ws = None
        self.heartbeat_interval = None
        self.seq = None
        self.session_id = None
        self.heartbeat_task = None
        self.acknowledged = True

    async def send_json(self, data):
        if self.ws:
            await self.ws.send(json.dumps(data))

    async def heartbeat(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval / 1000.0)
            if not self.acknowledged:
                print("Heartbeat ACK missed, connection is dead. Forcing reconnect...", file=sys.stderr)
                await self.ws.close(1008)
                break
            
            self.acknowledged = False
            # print(f"Sending heartbeat: seq {self.seq}")
            await self.send_json({"op": 1, "d": self.seq})

    async def identify(self):
        payload = {
            "op": 2,
            "d": {
                "token": self.token,
                # 33280 represents GUILD_MESSAGES (512) | MESSAGE_CONTENT (32768)
                "intents": 33280,
                "properties": {
                    "os": "windows",
                    "browser": "discord_responder",
                    "device": "discord_responder"
                }
            }
        }
        await self.send_json(payload)

    async def resume(self):
        payload = {
            "op": 6,
            "d": {
                "token": self.token,
                "session_id": self.session_id,
                "seq": self.seq
            }
        }
        await self.send_json(payload)

    async def run(self):
        uri = "wss://gateway.discord.gg/?v=10&encoding=json"
        
        while True:
            try:
                async with websockets.connect(uri, max_size=10_000_000) as ws:
                    self.ws = ws
                    self.acknowledged = True
                    
                    async for message in ws:
                        data = json.loads(message)
                        op = data.get("op")
                        t = data.get("t")
                        s = data.get("s")
                        d = data.get("d")

                        if s is not None:
                            self.seq = s

                        if op == 10:  # Hello
                            self.heartbeat_interval = d["heartbeat_interval"]
                            if self.heartbeat_task:
                                self.heartbeat_task.cancel()
                            self.heartbeat_task = asyncio.create_task(self.heartbeat())

                            if self.session_id and self.seq:
                                await self.resume()
                            else:
                                await self.identify()

                        elif op == 11:  # Heartbeat ACK
                            self.acknowledged = True

                        elif op == 9:  # Invalid Session
                            # FIXME: we should check if d is true to resume, but simple clear is safer
                            self.session_id = None
                            self.seq = None
                            await asyncio.sleep(5)
                            await self.identify()

                        elif op == 7:  # Reconnect
                            await ws.close()

                        elif op == 0:  # Dispatch
                            if t == "READY":
                                self.session_id = d["session_id"]
                                print(f"Connected to Discord Gateway as {d['user']['username']}#{d['user']['discriminator']}")
                            elif t == "RESUMED":
                                print("Successfully resumed gateway session")
                            elif t == "MESSAGE_CREATE":
                                asyncio.create_task(self.callback(d))

            except websockets.exceptions.ConnectionClosed:
                print("Gateway connection closed. Reconnecting in 5 seconds...", file=sys.stderr)
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Gateway connection error: {e}. Retrying in 5 seconds...", file=sys.stderr)
                await asyncio.sleep(5)
