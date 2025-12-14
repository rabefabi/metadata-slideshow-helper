from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

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
)


class SlideshowHelperConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input.get(CONF_NAME, "Slideshow Helper"), data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_MEDIA_DIR): str,
            vol.Optional(CONF_MIN_RATING, default=0): int,
            vol.Optional(CONF_INCLUDE_TAGS, default=""): str,
            vol.Optional(CONF_EXCLUDE_TAGS, default=""): str,
            vol.Optional(CONF_CYCLE_INTERVAL, default=DEFAULT_CYCLE_INTERVAL): int,
            vol.Optional(CONF_REFRESH_INTERVAL, default=DEFAULT_REFRESH_INTERVAL): int,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()

class OptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        return await self.async_step_options(user_input)

    async def async_step_options(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Options", data=user_input)

        options_schema = vol.Schema({
            vol.Optional(CONF_MIN_RATING, default=self.config_entry.options.get(CONF_MIN_RATING, 0)): int,
            vol.Optional(CONF_INCLUDE_TAGS, default=self.config_entry.options.get(CONF_INCLUDE_TAGS, "")): str,
            vol.Optional(CONF_EXCLUDE_TAGS, default=self.config_entry.options.get(CONF_EXCLUDE_TAGS, "")): str,
            vol.Optional(CONF_REFRESH_INTERVAL, default=self.config_entry.options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)): int,
            vol.Optional(CONF_CYCLE_INTERVAL, default=self.config_entry.options.get(CONF_CYCLE_INTERVAL, DEFAULT_CYCLE_INTERVAL)): int,
        })
        return self.async_show_form(step_id="options", data_schema=options_schema)
