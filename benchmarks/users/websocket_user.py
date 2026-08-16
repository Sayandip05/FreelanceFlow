"""
WebSocket Chat & Read Receipt Benchmark User
Tests Daphne ASGI WebSocket handshake latency, message echo, and read receipt throughput.
"""
import time
import json
import logging
import websocket
import requests
from locust import User, task, between, events
from benchmarks.config import TEST_USERS

logger = logging.getLogger(__name__)


class WebSocketChatUser(User):
    """
    Simulates real-time WebSocket chat connections over Daphne ASGI.
    """
    weight = 2
    wait_time = between(2, 5)
    contract_id = 1
    token = ""

    def on_start(self):
        """
        Authenticate via HTTP REST, obtain JWT token, and discover an active contract.
        """
        target_host = self.host or "http://127.0.0.1:8001"
        try:
            res = requests.post(
                f"{target_host}/api/users/login/",
                json=TEST_USERS["freelancer"],
                timeout=5,
            )
            if res.status_code == 200:
                data = res.json()
                self.token = data.get("access_token") or data.get("tokens", {}).get("access", "")

                # Fetch contracts to get a valid contract ID
                headers = {"Authorization": f"Bearer {self.token}"}
                c_res = requests.get(f"{target_host}/api/bidding/contracts/", headers=headers, timeout=5)
                if c_res.status_code == 200:
                    c_data = c_res.json()
                    contracts = c_data.get("results", c_data if isinstance(c_data, list) else [])
                    if contracts:
                        self.contract_id = contracts[0]["id"]
        except Exception as e:
            logger.warning(f"WebSocketUser on_start init failed: {e}")

    @task(3)
    def test_websocket_chat_roundtrip(self):
        """
        Connect to Daphne ASGI WebSocket room, send a message frame, and measure round-trip latency.
        """
        if not self.token:
            return

        target_host = self.host or "http://127.0.0.1:8001"
        ws_base = target_host.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_base}/ws/chat/{self.contract_id}/?token={self.token}"
        start_time = time.perf_counter()

        try:
            ws = websocket.create_connection(ws_url, timeout=5)
            handshake_time = (time.perf_counter() - start_time) * 1000

            events.request.fire(
                request_type="WebSocket",
                name="[WS] Handshake /ws/chat/:contract_id/",
                response_time=handshake_time,
                response_length=0,
                exception=None,
            )

            # Send a chat message frame
            msg_payload = json.dumps({
                "type": "message",
                "content": f"Benchmark ping @ {time.time():.2f}"
            })
            send_start = time.perf_counter()
            ws.send(msg_payload)

            # Wait for response frame
            reply = ws.recv()
            roundtrip_time = (time.perf_counter() - send_start) * 1000

            events.request.fire(
                request_type="WebSocket",
                name="[WS] Send & Recv Chat Frame",
                response_time=roundtrip_time,
                response_length=len(reply) if reply else 0,
                exception=None,
            )

            ws.close()

        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            events.request.fire(
                request_type="WebSocket",
                name="[WS] Connection & Chat",
                response_time=elapsed,
                response_length=0,
                exception=e,
            )
