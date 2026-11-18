import asyncio
import struct

from someipy import (
    ClientServiceInstance,
    Event,
    EventGroup,
    TransportLayerProtocol,
    MessageType,
    ReturnCode,
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

from climate_interface import (
    CLIMATE_INSTANCE_ID,
    GET_CABIN_TEMPERATURE_METHOD_ID,
    SET_TARGET_TEMPERATURE_METHOD_ID,
    CABIN_TEMPERATURE_CHANGED_EVENT_ID,
    CABIN_TEMPERATURE_EVENTGROUP_ID,
    build_climate_service,
)


def vehicle_event_callback(event_id, payload):
    if len(payload) != 2:
        return

    speed = struct.unpack("!H", payload)[0]

    if event_id == SPEED_CHANGED_EVENT_ID:
        print(
            f"[VEHICLE EVENT] SpeedChanged: {speed} km/h",
            flush=True,
        )
    elif event_id == OVERSPEED_WARNING_EVENT_ID:
        print(
            f"[WARNING] OVERSPEED: {speed} km/h!",
            flush=True,
        )


def climate_event_callback(event_id, payload):
    if len(payload) != 2:
        return

    temperature = struct.unpack("!h", payload)[0]

    if event_id == CABIN_TEMPERATURE_CHANGED_EVENT_ID:
        print(
            f"[CLIMATE EVENT] Cabin: {temperature / 10:.1f} C",
            flush=True,
        )


def make_eventgroup(group_id, event_id):
    return EventGroup(
        id=group_id,
        events=[
            Event(
                id=event_id,
                protocol=TransportLayerProtocol.UDP,
            )
        ],
    )


async def read_vehicle(vehicle):
    speed_result = await vehicle.call_method(
        GET_SPEED_METHOD_ID, b""
    )
    state_result = await vehicle.call_method(
        GET_VEHICLE_STATE_METHOD_ID, b""
    )

    if (
        speed_result.return_code != ReturnCode.E_OK
        or state_result.return_code != ReturnCode.E_OK
        or len(speed_result.payload) != 2
        or len(state_result.payload) != 1
    ):
        raise ValueError("Invalid vehicle method response")

    speed = struct.unpack("!H", speed_result.payload)[0]
    state = struct.unpack("!B", state_result.payload)[0]

    print(f"Vehicle Speed : {speed} km/h", flush=True)
    print(
        f"Vehicle State : {'MOVING' if state else 'STOPPED'}",
        flush=True,
    )


async def read_climate(climate):
    result = await climate.call_method(
        GET_CABIN_TEMPERATURE_METHOD_ID, b""
    )

    if result.return_code != ReturnCode.E_OK:
        raise ValueError("Temperature request failed")

    temperature = struct.unpack("!h", result.payload)[0]

    print(
        f"Cabin Temperature : {temperature / 10:.1f} C",
        flush=True,
    )


async def set_temperature(climate, value):
    payload = struct.pack("!h", value)

    result = await climate.call_method(
        SET_TARGET_TEMPERATURE_METHOD_ID,
        payload,
    )

    if (
        result.message_type != MessageType.RESPONSE
        or result.return_code != ReturnCode.E_OK
        or len(result.payload) != 1
    ):
        raise ValueError("Invalid SetTargetTemperature response")

    status = struct.unpack("!B", result.payload)[0]

    status_text = {
        0: "ACCEPTED",
        1: "INVALID_TEMPERATURE",
    }.get(status, "UNKNOWN_STATUS")

    print(
        f"[SET TARGET] {value / 10:.1f} C -> {status_text}",
        flush=True,
    )


async def main():
    daemon = await connect_to_someipy_daemon()

    vehicle = ClientServiceInstance(
        daemon=daemon,
        service=build_vehicle_speed_service(),
        instance_id=INSTANCE_ID,
        endpoint_ip="127.0.0.1",
        endpoint_port=3003,
        client_id=0x0002,
    )

    climate = ClientServiceInstance(
        daemon=daemon,
        service=build_climate_service(),
        instance_id=CLIMATE_INSTANCE_ID,
        endpoint_ip="127.0.0.1",
        endpoint_port=3004,
        client_id=0x0002,
    )

    vehicle.register_callback(vehicle_event_callback)
    climate.register_callback(climate_event_callback)

    vehicle.subscribe_eventgroup(
        make_eventgroup(
            SPEED_EVENTGROUP_ID,
            SPEED_CHANGED_EVENT_ID,
        ),
        30,
    )

    vehicle.subscribe_eventgroup(
        make_eventgroup(
            OVERSPEED_EVENTGROUP_ID,
            OVERSPEED_WARNING_EVENT_ID,
        ),
        30,
    )

    climate.subscribe_eventgroup(
        make_eventgroup(
            CABIN_TEMPERATURE_EVENTGROUP_ID,
            CABIN_TEMPERATURE_CHANGED_EVENT_ID,
        ),
        30,
    )

    print("=" * 50, flush=True)
    print("CENTRAL VEHICLE DISPLAY STARTED", flush=True)
    print("Monitoring two independent SOME/IP services", flush=True)
    print("=" * 50, flush=True)

    test_values = [220, 160, 300, 100, 350]
    test_index = 0
    previous_vehicle = None
    previous_climate = None
    last_test_time = 0

    loop = asyncio.get_running_loop()

    try:
        while True:
            vehicle_available = await vehicle.is_available()
            climate_available = await climate.is_available()

            if vehicle_available != previous_vehicle:
                print(
                    "VehicleSpeedService : "
                    + ("AVAILABLE" if vehicle_available
                       else "NOT AVAILABLE"),
                    flush=True,
                )
                previous_vehicle = vehicle_available

            if climate_available != previous_climate:
                print(
                    "ClimateService      : "
                    + ("AVAILABLE" if climate_available
                       else "NOT AVAILABLE"),
                    flush=True,
                )
                previous_climate = climate_available

            if vehicle_available:
                try:
                    await read_vehicle(vehicle)
                except Exception as error:
                    print(
                        f"[VEHICLE ERROR] {error}",
                        flush=True,
                    )

            if climate_available:
                try:
                    await read_climate(climate)

                    now = loop.time()

                    if now - last_test_time >= 6:
                        requested = test_values[
                            test_index % len(test_values)
                        ]
                        await set_temperature(climate, requested)
                        test_index += 1
                        last_test_time = now

                except Exception as error:
                    print(
                        f"[CLIMATE ERROR] {error}",
                        flush=True,
                    )

            print("-" * 50, flush=True)
            await asyncio.sleep(3)

    finally:
        await daemon.disconnect_from_daemon()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCentral Display stopped")
