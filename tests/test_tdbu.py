import asyncio, json, sys
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "custom_components", "automate"))
import aiopulse2
from aiopulse2 import MovingAction

def payload(mp1, mp2, is1=True, is2=True):
    return json.dumps({"result": {"reported": {
        "hubId": "1152828", "name": "1152828", "mac": "78:e3:6d:f4:18:4c",
        "mfi": {"model": "MT02-0401-067004"}, "firmware": {"version": "1.10.0"},
        "shades": {"RY1": {"ol": True, "mp1": mp1, "ls1": 1, "is1": is1, "mp2": mp2,
                           "ls2": 1, "is2": is2, "vo": "7.3T13", "rs": -78}}}}})

async def main():
    hub = aiopulse2.Hub("192.168.50.131")
    sent = []
    async def fake_send(p): sent.append(p)
    async def fake_serial(*a, **k):
        # Real order of events: the shade name arrives while the hub is still
        # processing the first payload, before the rail data has been read.
        for rid in list(hub.unknown_rollers):
            hub.handle_device_query_name_response(rid, "Shade")
    hub.send_payload = fake_send
    hub.runserial = fake_serial
    hub_notified = []
    hub.callback_subscribe(lambda h: hub_notified.append(h.rollers["RY1"].is_tdbu if "RY1" in h.rollers else None))
    hub.async_add_job = lambda cb, *a: cb(*a)
    await hub.wsconsumer(payload(68, 30))
    r = hub.rollers["RY1"]
    print("tdbu", r.is_tdbu, "rails", r.rail_closed_percent, "type", r.devicetype, "batt%", r.battery_percent, "coverage", r.coverage_percent)
    print("hub scans saw is_tdbu =", hub_notified)
    assert hub_notified and hub_notified[-1] is True, "a scan must happen after the shade is known to be TDBU"
    assert r.is_tdbu and r.rail_closed_percent == {1: 68, 2: 30} and r.devicetype == "Top down bottom up motor"
    # top rail moved from app
    await hub.wsconsumer(payload(68, 30, is2=False))
    await hub.wsconsumer(payload(68, 41, is2=False))
    print("app move top action:", r.rail_action[2])
    assert r.rail_action[2] == MovingAction.down
    await hub.wsconsumer(payload(68, 52))
    assert r.rail_action[2] == MovingAction.stopped and r.rail_closed_percent[2] == 52
    # commanded move
    await r.move_rail(2, 0)
    print("sent:", sent[-1]["args"]["desired"])
    assert sent[-1]["args"]["desired"] == {"shades": {"RY1": {"movePercent2": 0}}}
    assert r.rail_action[2] == MovingAction.up
    await r.move_rail(1, 100)
    assert sent[-1]["args"]["desired"] == {"shades": {"RY1": {"movePercent1": 100}}}
    # normal shade unaffected
    await hub.wsconsumer(json.dumps({"result": {"reported": {"hubId": "1152828", "shades": {"AB1": {"ol": True, "mp": 40, "is": True, "vo": "12.1D24", "rs": -70}}}}}))
    n = hub.rollers["AB1"]
    assert not n.is_tdbu and n.closed_percent == 40
    print("ALL TESTS PASSED")
asyncio.run(main())
