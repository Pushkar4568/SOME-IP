import asyncio
import struct

from someipy import (
    ClientServiceInstance,
    Event,
    EventGroup,
    TransportLayerProtocol,
    connect_to_someipy_daemon,
)

from vehicle_speed_interface import (
    INSTANCE_ID,
    GET_SPEED_METHOD_ID,
    GET_VEHICLE_STATE_METHOD_ID,
    SPEED_CHANGED_EVENT_ID,
    OVERSPEED_WARNING_EVENT_ID,
    SPEED_EVENTGROUP_ID,
    OVERSPEED_EVENTGROUP_ID,
    build_vehicle_speed_service,
)


def event_callback(event_id, payload):
    if len(payload) < 2:
        print("[ERROR] Invalid event payload", flush=True)
        return

    speed = struct.unpack("!H", payload[:2])[0]

    if event_id == SPEED_CHANGED_EVENT_ID:
        print(f"[EVENT] SpeedChanged: {speed} km/h", flush=True)

    elif event_id == OVERSPEED_WARNING_EVENT_ID:
        print(
            f"[WARNING] OVERSPEED: {speed} km/h",
            flush=True,
        )


async def main():
    daemon = await connect_to_someipy_daemon()

    service = build_vehicle_speed_service()

    cluster = ClientServiceInstance(
        daemon=daemon,
        service=service,
        instance_id=INSTANCE_ID,
        endpoint_ip="127.0.0.1",
        endpoint_port=3001,
        client_id=0x0001,
    )

    cluster.register_callback(event_callback)

    speed_group = EventGroup(
        id=SPEED_EVENTGROUP_ID,
        events=[
            Event(
                id=SPEED_CHANGED_EVENT_ID,
                protocol=TransportLayerProtocol.UDP,
            )
        ],
    )

    overspeed_group = EventGroup(
        id=OVERSPEED_EVENTGROUP_ID,
        events=[
            Event(
                id=OVERSPEED_WARNING_EVENT_ID,
                protocol=TransportLayerProtocol.UDP,
            )
        ],
    )

    cluster.subscribe_eventgroup(speed_group, 10)
    cluster.subscribe_eventgroup(overspeed_group, 10)

    print("=" * 45, flush=True)
    print("INSTRUMENT CLUSTER ECU STARTED", flush=True)
    print("Waiting for VehicleSpeedService...", flush=True)
    print("=" * 45, flush=True)

    try:
        while True:
            if await cluster.is_available():
                print(
                    "\nVehicleSpeedService: AVAILABLE",
                    flush=True,
                )

                try:
                    speed_result = await cluster.call_method(
                        GET_SPEED_METHOD_ID, b""
                    )

                    speed = struct.unpack(
                        "!H", speed_result.payload
                    )[0]

                    state_result = await cluster.call_method(
                        GET_VEHICLE_STATE_METHOD_ID, b""
                    )

                    state = struct.unpack(
                        "!B", state_result.payload
                    )[0]

                    state_text = "MOVING" if state else "STOPPED"

                    print(
                        f"Vehicle Speed: {speed} km/h",
                        flush=True,
                    )
                    print(
                        f"Vehicle State: {state_text}",
                        flush=True,
                    )

                except Exception as error:
                    print(
                        f"[METHOD ERROR] {error}",
                        flush=True,
                    )
            else:
                print(
                    "VehicleSpeedService: NOT AVAILABLE",
                    flush=True,
                )

            await asyncio.sleep(3)

    finally:
        await daemon.disconnect_from_daemon()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInstrument Cluster stopped")
