import json
import threading
import time
from typing import Any, Optional

import paho.mqtt.client as mqtt
from fastapi import HTTPException, status

from app.core.config import settings


class MqttPublisher:
    def __init__(self) -> None:
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._lock = threading.Lock()

    def _on_connect(self, _: mqtt.Client, __: Any, ___: Any, rc: int, ____: Any = None):
        self._connected = rc == 0

    def _on_disconnect(self, _: mqtt.Client, __: Any, ___: int, ____: Any = None):
        self._connected = False

    def _build_client(self) -> mqtt.Client:
        client = mqtt.Client(client_id=settings.mqtt_client_id, protocol=mqtt.MQTTv311)
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect

        if settings.mqtt_username:
            client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        return client

    def _ensure_config(self) -> None:
        if not settings.mqtt_host:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MQTT_HOST is not configured",
            )

    def _wait_until_connected(self, timeout_seconds: int = 5) -> bool:
        end = time.time() + timeout_seconds
        while time.time() < end:
            if self._connected:
                return True
            time.sleep(0.1)
        return False

    def ensure_connected(self) -> None:
        self._ensure_config()

        with self._lock:
            if self._client is None:
                self._client = self._build_client()

            if self._connected:
                return

            try:
                self._client.connect(
                    settings.mqtt_host, settings.mqtt_port, settings.mqtt_keepalive
                )
                self._client.loop_start()
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"MQTT connect failed: {exc}",
                )

            if not self._wait_until_connected():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="MQTT broker connection timeout",
                )

    def publish(self, topic: str, payload: dict) -> None:
        self.ensure_connected()
        assert self._client is not None

        message = json.dumps(payload)
        result = self._client.publish(topic, message, qos=settings.mqtt_qos)
        result.wait_for_publish(timeout=5)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            self._connected = False
            self.ensure_connected()
            retry_result = self._client.publish(topic, message, qos=settings.mqtt_qos)
            retry_result.wait_for_publish(timeout=5)
            if retry_result.rc != mqtt.MQTT_ERR_SUCCESS:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"MQTT publish failed with code {retry_result.rc}",
                )


mqtt_publisher = MqttPublisher()
