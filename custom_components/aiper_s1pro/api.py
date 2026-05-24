"""Aiper cloud API client for Scuba S1 Pro."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Aiper cloud API base URL (captured from app traffic via mitmproxy)
# App bundle: com.aiper.develop
API_BASE = "https://api.aiper.com"

# Known endpoints (reverse-engineered from Aiper app v2.x)
ENDPOINT_LOGIN       = "/app/user/login"
ENDPOINT_DEVICES     = "/app/device/list"
ENDPOINT_DEVICE_INFO = "/app/device/info"
ENDPOINT_COMMAND     = "/app/device/command"
ENDPOINT_STATUS      = "/app/device/status"

# S1 Pro device type identifier
DEVICE_TYPE_S1_PRO = "SCUBA_S1_PRO"

# Cleaning modes supported by S1 Pro
CLEANING_MODES = {
    "auto":      "AUTO",       # Full clean: floor + walls + waterline
    "floor":     "FLOOR",      # Floor only
    "wall":      "WALL",       # Walls only
    "waterline": "WATERLINE",  # Waterline only
    "floor_wall":"FLOOR_WALL", # Floor + walls
}

# Device commands
CMD_START   = "START"
CMD_STOP    = "STOP"
CMD_PAUSE   = "PAUSE"
CMD_RETURN  = "RETURN_DOCK"
CMD_LOCATE  = "LOCATE"

# Device states returned by the API
STATE_CLEANING  = "CLEANING"
STATE_DOCKED    = "DOCKED"
STATE_IDLE      = "IDLE"
STATE_PAUSED    = "PAUSED"
STATE_RETURNING = "RETURNING"
STATE_ERROR     = "ERROR"
STATE_CHARGING  = "CHARGING"


class AiperAuthError(Exception):
    """Raised when authentication fails."""


class AiperConnectionError(Exception):
    """Raised when unable to reach the Aiper cloud."""


class AiperCommandError(Exception):
    """Raised when a device command fails."""


class AiperApiClient:
    """Async client for the Aiper cloud API."""

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._token: str | None = None
        self._user_id: str | None = None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def async_login(self) -> bool:
        """Authenticate and store the access token."""
        payload = {
            "email":    self._email,
            "password": self._password,
            "appType":  "APP",
        }
        try:
            data = await self._post(ENDPOINT_LOGIN, payload, auth=False)
        except AiperConnectionError:
            raise
        except Exception as exc:
            raise AiperAuthError(f"Login failed: {exc}") from exc

        if not data.get("token"):
            raise AiperAuthError("No token in login response")

        self._token   = data["token"]
        self._user_id = data.get("userId")
        _LOGGER.debug("Aiper login successful, user_id=%s", self._user_id)
        return True

    # ------------------------------------------------------------------
    # Device discovery
    # ------------------------------------------------------------------

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return a list of devices linked to the account."""
        data = await self._get(ENDPOINT_DEVICES)
        return data.get("devices", [])

    async def async_get_device_status(self, device_id: str) -> dict[str, Any]:
        """Return full status for a specific device."""
        data = await self._get(ENDPOINT_STATUS, params={"deviceId": device_id})
        return data.get("device", {})

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_start_cleaning(
        self,
        device_id: str,
        mode: str = "auto",
    ) -> bool:
        """Start a cleaning cycle."""
        api_mode = CLEANING_MODES.get(mode, CLEANING_MODES["auto"])
        payload = {
            "deviceId": device_id,
            "command":  CMD_START,
            "params": {"cleaningMode": api_mode},
        }
        await self._post(ENDPOINT_COMMAND, payload)
        return True

    async def async_stop_cleaning(self, device_id: str) -> bool:
        """Stop the current cleaning cycle."""
        payload = {"deviceId": device_id, "command": CMD_STOP}
        await self._post(ENDPOINT_COMMAND, payload)
        return True

    async def async_pause_cleaning(self, device_id: str) -> bool:
        """Pause the current cleaning cycle."""
        payload = {"deviceId": device_id, "command": CMD_PAUSE}
        await self._post(ENDPOINT_COMMAND, payload)
        return True

    async def async_return_to_dock(self, device_id: str) -> bool:
        """Send the robot back to the dock/pick-up position."""
        payload = {"deviceId": device_id, "command": CMD_RETURN}
        await self._post(ENDPOINT_COMMAND, payload)
        return True

    async def async_locate(self, device_id: str) -> bool:
        """Trigger the locate/beep function."""
        payload = {"deviceId": device_id, "command": CMD_LOCATE}
        await self._post(ENDPOINT_COMMAND, payload)
        return True

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    def _headers(self, auth: bool = True) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept":       "application/json",
            "User-Agent":   "AiperApp/2.2 (Android)",
        }
        if auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> dict[str, Any]:
        url = f"{API_BASE}{endpoint}"
        try:
            async with self._session.get(
                url, params=params, headers=self._headers()
            ) as resp:
                return await self._handle_response(resp)
        except aiohttp.ClientError as exc:
            raise AiperConnectionError(f"GET {endpoint} failed: {exc}") from exc

    async def _post(
        self,
        endpoint: str,
        payload: dict,
        auth: bool = True,
    ) -> dict[str, Any]:
        url = f"{API_BASE}{endpoint}"
        try:
            async with self._session.post(
                url, json=payload, headers=self._headers(auth=auth)
            ) as resp:
                return await self._handle_response(resp)
        except aiohttp.ClientError as exc:
            raise AiperConnectionError(f"POST {endpoint} failed: {exc}") from exc

    @staticmethod
    async def _handle_response(resp: aiohttp.ClientResponse) -> dict[str, Any]:
        if resp.status == 401:
            raise AiperAuthError("Token expired or invalid")
        if resp.status != 200:
            text = await resp.text()
            raise AiperConnectionError(
                f"HTTP {resp.status}: {text[:200]}"
            )
        body: dict = await resp.json()
        # Aiper API wraps responses: {"code": 0, "msg": "ok", "data": {...}}
        if body.get("code", 0) != 0:
            raise AiperCommandError(
                f"API error {body.get('code')}: {body.get('msg')}"
            )
        return body.get("data", body)
