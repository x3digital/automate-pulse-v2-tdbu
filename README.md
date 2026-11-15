# Automate Pulse Hub v2, with Top Down Bottom Up support

This is a fork of [sillyfrog/Automate-Pulse-v2](https://github.com/sillyfrog/Automate-Pulse-v2) and its
[aiopulse2](https://github.com/sillyfrog/aiopulse2) library (both Apache 2.0). All credit for the original
work goes to Sillyfrog. This fork adds support for Rollease Acmeda top down bottom up (TDBU) shades that use a
single dual motor (they show up as `unknown T` in the original integration).

## What this fork changes

- The hub reports TDBU shades with two positions, `mp1` (bottom rail) and `mp2` (top rail), and accepts
  `movePercent1` / `movePercent2` commands. This fork reads and sends both.
- Each TDBU shade gets three cover entities on the same device:
  - **Name Top**: the top rail. 100 = at the top of the window, 0 = all the way down.
  - **Name Bottom**: the bottom rail. Same scale.
  - **Name** (the original entity): the whole window. Open stacks the fabric at the top, close covers the
    whole window, and a position works like a normal shade (top rail at the top, bottom rail sets the level).
- The motor type `T` is labelled "Top down bottom up motor", and its battery is reported.
- The aiopulse2 library is bundled inside the integration, so nothing extra is installed from PyPI.
- Regular single motor shades behave exactly as before.

The integration keeps the original `automate` domain, so it replaces the original in place and existing
config entries and entities carry over. Remove the original from HACS before installing this one.

Tests: `python3 tests/test_tdbu.py`

---

# Rollease Acmeda Automate Pulse Hub v2 integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

The Automate Pulse 2 Hub by Rollease Acmeda integration allows you to control and monitor covers via your Automate Pulse v2 Hub (see the [acmeda](/integrations/acmeda) integration for the v1 hub). The integration uses an [API](https://pypi.org/project/aiopulse2/) to directly communicate with hubs on the local network, rather than connecting via the cloud. [See this integration](https://www.home-assistant.io/integrations/acmeda/) if you have a v1 hub.

Devices are represented as a cover for monitoring and control as well as a sensor for monitoring battery level and signal strength.

Please keep an eye on the Automate Shades web site on the status of firmware updates here: https://www.automateshades.com/firmware-updates/

# Installation

This integration is designed to be added as a custom [HACS](https://hacs.xyz/) repository. Start with [installing HACS](https://hacs.xyz/docs/installation/prerequisites).

Once HACS is installed, go to HACS in the sidebar, in the top right click on the 3 dots, select Custom repositories, then enter `https://github.com/sillyfrog/Automate-Pulse-v2` for the repository URL, and select "Integration" for the Category, and click Add.

Close the window and then click "Explore & Add Repositories" in the bottom right.

Search for and select the "Rollease Acmeda Automate Pulse Hub v2" integration, then click "Install this repository in HACS" and click "Install".

Once installed, restart Home Assistant (not strictly required as this uses a Config Flow, but it's good practice).

Once HA is back up, go to Configuration > Integrations > Add integration, and select "Automate Pulse Hub v2".

This will prompt for the IP address of the hub and register the covers with Home Assistant. All devices are automatically discovered on the hub and you will have the opportunity to select the area each device is located.

Once registration is complete, you should see a `cover` and a `sensor` entity for the battery for each device. Additionally there is a disabled sensors for the signal strength. The integration automatically manages the addition/update/removal of any devices connected on the hub at startup, including device names unless manually specified in Home Assistant.

## Caveats

If the IP address for the hub changes, you will need to re-register it with Home Assistant again. To avoid this, set up a DHCP reservation on your router for your hub so that it always has the same IP address.

The integration has the following limitations:

- covers with position as well as tilt are not yet supported (I'm not sure if such a product exists).
- the integration doesn't make use of rooms and scenes configured in the hub, use the equivalent functionality in Home Assistant instead.
- when adding new covers, you may need to restart Home Assistant to see the full details _after_ updating the name in the *Pulse 2* app.

# Debugging

If you are having issues with the integration, please enable debug logging for the integration by adding the following to your Home Assistant `configuration.yaml` file:

```yaml
logger:
  default: warning
  logs:
    aiopulse2: debug
    automate: debug
    custom_components.automate: debug
```

Then restart Home Assistant and check the logs for any errors and/or provide for debugging.