"""Support for Automate Roller Blinds."""

from . import aiopulse2
from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .base import AutomateBase
from .const import AUTOMATE_HUB_UPDATE, DOMAIN
from .helpers import async_add_automate_entities


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Automate Rollers from a config entry."""
    hub = hass.data[DOMAIN][config_entry.entry_id]

    current = set()

    current_top = set()
    current_bottom = set()

    @callback
    def async_add_automate_covers():
        async_add_automate_entities(
            hass, AutomateCover, config_entry, current, async_add_entities
        )
        async_add_automate_entities(
            hass, AutomateTopRail, config_entry, current_top, async_add_entities
        )
        async_add_automate_entities(
            hass, AutomateBottomRail, config_entry, current_bottom, async_add_entities
        )

    hub.cleanup_callbacks.append(
        async_dispatcher_connect(
            hass,
            AUTOMATE_HUB_UPDATE.format(config_entry.entry_id),
            async_add_automate_covers,
        )
    )


class AutomateCover(AutomateBase, CoverEntity):
    """Representation of a Automate cover device."""

    _attr_device_class = CoverDeviceClass.SHADE

    @property
    def current_cover_position(self):
        """Return the current position of the roller blind.

        None is unknown, 0 is closed, 100 is fully open.
        """
        if self.roller.is_tdbu:
            # Whole window: 100 = fabric fully stacked up, 0 = window fully covered
            coverage = self.roller.coverage_percent
            return None if coverage is None else 100 - coverage
        position = None
        if self.roller.closed_percent is not None:
            position = 100 - self.roller.closed_percent
        return position

    @property
    def current_cover_tilt_position(self):
        """Return the current tilt of the roller blind.

        None is unknown, 0 is closed, 100 is fully open.
        """
        return None

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = 0
        if self.current_cover_position is not None:
            supported_features |= (
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION
            )
        if self.current_cover_tilt_position is not None:
            supported_features |= (
                CoverEntityFeature.OPEN_TILT
                | CoverEntityFeature.CLOSE_TILT
                | CoverEntityFeature.STOP_TILT
                | CoverEntityFeature.SET_TILT_POSITION
            )

        return supported_features

    @property
    def device_info(self):
        """Return the device info."""
        attrs = super().device_info
        attrs["manufacturer"] = "Automate"
        attrs["model"] = self.roller.devicetype
        attrs["sw_version"] = self.roller.version
        attrs["via_device"] = (DOMAIN, self.roller.hub.id)
        attrs["name"] = self.name
        return attrs

    @property
    def is_opening(self):
        """Is cover opening/moving up."""
        if self.roller.is_tdbu:
            return self.roller.rail_action[1] == aiopulse2.MovingAction.up
        return self.roller.action == aiopulse2.MovingAction.up

    @property
    def is_closing(self):
        """Is cover closing/moving down."""
        if self.roller.is_tdbu:
            return self.roller.rail_action[1] == aiopulse2.MovingAction.down
        return self.roller.action == aiopulse2.MovingAction.down

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.roller.is_tdbu:
            return self.roller.coverage_percent == 100
        return self.roller.closed_percent == 100

    async def async_close_cover(self, **kwargs):
        """Close the roller."""
        if self.roller.is_tdbu:
            # Cover the whole window: top rail to the top, bottom rail to the bottom
            await self.roller.move_rail(2, 0)
            await self.roller.move_rail(1, 100)
            return
        await self.roller.move_down()

    async def async_open_cover(self, **kwargs):
        """Open the roller."""
        if self.roller.is_tdbu:
            # Clear the whole window: both rails to the top
            await self.roller.move_rail(2, 0)
            await self.roller.move_rail(1, 0)
            return
        await self.roller.move_up()

    async def async_stop_cover(self, **kwargs):
        """Stop the roller."""
        await self.roller.move_stop()

    async def async_set_cover_position(self, **kwargs):
        """Move the roller shutter to a specific position."""
        if self.roller.is_tdbu:
            # Act like a normal shade: top rail at the top, bottom rail sets the level
            await self.roller.move_rail(2, 0)
            await self.roller.move_rail(1, 100 - kwargs[ATTR_POSITION])
            return
        await self.roller.move_to(100 - kwargs[ATTR_POSITION])

    async def async_close_cover_tilt(self, **kwargs):
        """Close the roller."""
        await self.roller.move_down()

    async def async_open_cover_tilt(self, **kwargs):
        """Open the roller."""
        await self.roller.move_up()

    async def async_stop_cover_tilt(self, **kwargs):
        """Stop the roller."""
        await self.roller.move_stop()

    async def async_set_cover_tilt(self, **kwargs):
        """Tilt the roller shutter to a specific position."""
        await self.roller.move_to(100 - kwargs[ATTR_POSITION])


class AutomateRail(AutomateCover):
    """One rail of a top down bottom up shade.

    Position is how high the rail sits: 100 = top of the window, 0 = bottom.
    So the up arrow always moves the rail up and the down arrow moves it down.
    """

    RAIL = 1
    LABEL = "Rail"

    def include_entity(self) -> bool:
        """Only create rail entities for TDBU shades."""
        return self.roller.is_tdbu

    @property
    def unique_id(self):
        """Return a unique ID for this rail."""
        return f"{self.roller.id}_{self.LABEL.lower()}"

    @property
    def name(self):
        """Return the rail name."""
        return f"{self.roller.name} {self.LABEL}"

    @property
    def device_info(self):
        """Attach the rail to the same device as the shade."""
        return {"identifiers": {(DOMAIN, self.roller.id)}}

    @property
    def current_cover_position(self):
        """Return how high the rail is (100 = top)."""
        pos = self.roller.rail_closed_percent.get(self.RAIL)
        return None if pos is None else 100 - pos

    @property
    def is_opening(self):
        """Rail moving up."""
        return self.roller.rail_action[self.RAIL] == aiopulse2.MovingAction.up

    @property
    def is_closing(self):
        """Rail moving down."""
        return self.roller.rail_action[self.RAIL] == aiopulse2.MovingAction.down

    @property
    def is_closed(self):
        """Rail is all the way down."""
        return self.roller.rail_closed_percent.get(self.RAIL) == 100

    async def async_open_cover(self, **kwargs):
        """Move the rail all the way up."""
        await self.roller.move_rail(self.RAIL, 0)

    async def async_close_cover(self, **kwargs):
        """Move the rail all the way down."""
        await self.roller.move_rail(self.RAIL, 100)

    async def async_set_cover_position(self, **kwargs):
        """Move the rail to a height (100 = top)."""
        await self.roller.move_rail(self.RAIL, 100 - kwargs[ATTR_POSITION])


class AutomateTopRail(AutomateRail):
    """Top rail of a TDBU shade."""

    RAIL = 2
    LABEL = "Top"


class AutomateBottomRail(AutomateRail):
    """Bottom rail of a TDBU shade."""

    RAIL = 1
    LABEL = "Bottom"
