import httpx
from loguru import logger
from core.config import get_settings

settings = get_settings()


class BackendClient:
    """HTTP-клиент для взаимодействия бота с Backend API."""

    def __init__(self):
        self.base_url = settings.BACKEND_URL
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ─── Chats ────────────────────────────────────────────────────────────────

    async def register_chat(self, telegram_chat_id: int, title: str, username: str | None,
                            member_count: int, telegram_user_id: int) -> dict | None:
        try:
            c = await self.get_client()
            r = await c.post(
                "/api/v1/chats/register",
                json={"telegram_chat_id": telegram_chat_id, "title": title,
                      "username": username, "member_count": member_count},
                params={"telegram_user_id": telegram_user_id},
            )
            return r.json() if r.is_success else None
        except Exception as e:
            logger.error(f"register_chat error: {e}")
            return None

    async def get_chat_by_tg_id(self, telegram_chat_id: int) -> dict | None:
        try:
            c = await self.get_client()
            r = await c.get(f"/api/v1/chats/", params={"telegram_chat_id": telegram_chat_id})
            return r.json() if r.is_success else None
        except Exception as e:
            logger.error(f"get_chat error: {e}")
            return None

    async def get_settings(self, chat_id: int) -> dict | None:
        try:
            c = await self.get_client()
            r = await c.get(f"/api/v1/settings/{chat_id}")
            return r.json() if r.is_success else None
        except Exception as e:
            logger.error(f"get_settings error: {e}")
            return None

    async def update_activity(self, chat_id: int):
        try:
            c = await self.get_client()
            await c.patch(f"/api/v1/chats/{chat_id}/activity")
        except Exception as e:
            logger.error(f"update_activity error: {e}")

    # ─── Moderation ───────────────────────────────────────────────────────────

    async def punish(self, chat_id: int, telegram_user_id: int,
                     issued_by: int | None, ptype: str,
                     reason: str | None = None, duration: int | None = None) -> dict | None:
        try:
            c = await self.get_client()
            r = await c.post("/api/v1/moderation/punish", json={
                "chat_id": chat_id,
                "telegram_user_id": telegram_user_id,
                "issued_by_telegram_user_id": issued_by,
                "type": ptype,
                "reason": reason,
                "duration_seconds": duration,
            })
            return r.json() if r.is_success else None
        except Exception as e:
            logger.error(f"punish error: {e}")
            return None

    async def warn(self, chat_id: int, telegram_user_id: int,
                   issued_by: int | None, reason: str | None = None) -> dict | None:
        try:
            c = await self.get_client()
            r = await c.post("/api/v1/moderation/warn", json={
                "chat_id": chat_id,
                "telegram_user_id": telegram_user_id,
                "issued_by_telegram_user_id": issued_by,
                "reason": reason,
            })
            return r.json() if r.is_success else None
        except Exception as e:
            logger.error(f"warn error: {e}")
            return None

    async def get_warns(self, chat_id: int, telegram_user_id: int) -> dict:
        try:
            c = await self.get_client()
            r = await c.get(f"/api/v1/moderation/warns/{chat_id}/{telegram_user_id}")
            return r.json() if r.is_success else {"count": 0, "warnings": []}
        except Exception as e:
            logger.error(f"get_warns error: {e}")
            return {"count": 0, "warnings": []}

    async def revoke_warn(self, warning_id: int):
        try:
            c = await self.get_client()
            await c.patch(f"/api/v1/moderation/warn/{warning_id}/revoke")
        except Exception as e:
            logger.error(f"revoke_warn error: {e}")

    # ─── Triggers ─────────────────────────────────────────────────────────────

    async def get_triggers(self, chat_id: int) -> list[dict]:
        try:
            c = await self.get_client()
            r = await c.get(f"/api/v1/triggers/{chat_id}")
            return r.json() if r.is_success else []
        except Exception as e:
            logger.error(f"get_triggers error: {e}")
            return []

    # ─── Logs ─────────────────────────────────────────────────────────────────

    async def log_event(self, chat_id: int, action_type: str,
                        actor_tg_id: int | None = None,
                        target_tg_id: int | None = None,
                        payload: dict | None = None):
        try:
            c = await self.get_client()
            await c.post("/api/v1/logs/", json={
                "chat_id": chat_id,
                "action_type": action_type,
                "actor_telegram_user_id": actor_tg_id,
                "target_telegram_user_id": target_tg_id,
                "payload": payload,
            })
        except Exception as e:
            logger.error(f"log_event error: {e}")

    async def log_system(self, level: str, service: str, event_type: str, payload: dict | None = None):
        try:
            c = await self.get_client()
            await c.post("/api/v1/logs/system", json={
                "level": level,
                "service": service,
                "event_type": event_type,
                "payload": payload,
            })
        except Exception as e:
            logger.error(f"log_system error: {e}")

    # ─── Analytics ────────────────────────────────────────────────────────────

    async def increment_metric(self, chat_id: int, field: str):
        try:
            c = await self.get_client()
            await c.post(f"/api/v1/analytics/{chat_id}/increment", params={"field": field})
        except Exception as e:
            logger.error(f"increment_metric error: {e}")


backend = BackendClient()
