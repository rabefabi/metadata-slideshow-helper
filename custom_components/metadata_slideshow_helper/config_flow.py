from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    CONF_CYCLE_INTERVAL,
    CONF_EXCLUDE_TAGS,
    CONF_INCLUDE_TAGS,
    CONF_MEDIA_DIR,
    CONF_MIN_RATING,
    CONF_REFRESH_INTERVAL,
    DEFAULT_CYCLE_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
    DOMAIN,
    TITLE,
)


class SlideshowHelperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    def _build_schema(self, defaults: dict[str, Any] | None = None) -> vol.Schema:
        values = defaults or {}
        return vol.Schema(
            {
                vol.Required(CONF_MEDIA_DIR, default=values.get(CONF_MEDIA_DIR, "")): str,
                vol.Optional(CONF_MIN_RATING, default=values.get(CONF_MIN_RATING, 0)): int,
                vol.Optional(CONF_INCLUDE_TAGS, default=values.get(CONF_INCLUDE_TAGS, "")): str,
                vol.Optional(CONF_EXCLUDE_TAGS, default=values.get(CONF_EXCLUDE_TAGS, "")): str,
                vol.Optional(
                    CONF_CYCLE_INTERVAL,
                    default=values.get(CONF_CYCLE_INTERVAL, DEFAULT_CYCLE_INTERVAL),
                ): int,
                vol.Optional(
                    CONF_REFRESH_INTERVAL,
                    default=values.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL),
                ): int,
            }
        )

    def _validate_intervals(self, user_input: dict[str, Any]) -> tuple[bool, int, int] | None:
        """Validate refresh > cycle intervals. Return (is_valid, cycle, refresh) or None if invalid."""
        cycle = int(user_input.get(CONF_CYCLE_INTERVAL, DEFAULT_CYCLE_INTERVAL))
        refresh = int(user_input.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL))
        if refresh <= cycle:
            return None
        return (True, cycle, refresh)

    def _show_interval_error(
        self, step_id: str, user_input: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Show form with interval validation error."""
        cycle = int(user_input.get(CONF_CYCLE_INTERVAL, DEFAULT_CYCLE_INTERVAL))
        refresh = int(user_input.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL))
        return self.async_show_form(
            step_id=step_id,
            data_schema=self._build_schema(user_input),
            errors={"base": "invalid_interval"},
            description_placeholders={
                "cycle": str(cycle),
                "refresh": str(refresh),
            },
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            if not self._validate_intervals(user_input):
                return self._show_interval_error("user", user_input)
            return self.async_create_entry(title=user_input.get(CONF_NAME, TITLE), data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._build_schema())

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        config_entry = self._get_reconfigure_entry()

        if user_input is not None:
            if not self._validate_intervals(user_input):
                return self._show_interval_error("reconfigure", user_input)
            return self.async_update_reload_and_abort(
                config_entry,
                data_updates=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._build_schema(dict(config_entry.data)),
        )
