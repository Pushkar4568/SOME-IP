import asyncio
import struct

from someipy import (
    ServerServiceInstance,
    MethodResult,
    MessageType,
    ReturnCode,
    connect_to_someipy_daemon,
)

from vehicle_speed_interface import (
    INSTANCE_ID,
    SPEED_EVENTGROUP_ID,
    OVERSPEED_EVENTGROUP_ID,
    SPEED_CHANGED_EVENT_ID,
    OVERSPEED_WARNING_EVENT_ID,
    build_vehicle_speed_service,
)


class VehicleECU:
    def __init__(self):
        self.current_speed_kmph = 0

    async def get_speed(self, data, addr):
        print(f"[METHOD] GetSpeed from {addr}", flush=True)

        result = MethodResult()
        result.message_type = MessageType.RESPONSE
        result.return_code = ReturnCode.E_OK
        result.payload = struct.pack(
            "!H", self.current_speed_kmph
        )
        return result

    async def get_vehicle_state(self, data, addr):
        print(
            f"[METHOD] GetVehicleState from {addr}",
            flush=True,
        )

        state = 1 if self.current_speed_kmph > 0 else 0

        result = MethodResult()
        result.message_type = MessageType.RESPONSE
        result.return_code = ReturnCode.E_OK
        result.payload = struct.pack("!B", state)
        return result


async def main():
    vehicle = VehicleECU()

    daemon = await connect_to_someipy_daemon()

    service = build_vehicle_speed_service(
        vehicle.get_speed,
        vehicle.get_vehicle_state,
    )

    instance = ServerServiceInstance(
        daemon=daemon,
        service=service,
        instance_id=INSTANCE_ID,
        endpoint_ip="127.0.0.1",
        endpoint_port=3000,
        ttl=5,
        cyclic_offer_delay_ms=2000,
    )

    await instance.start_offer()

    print("=" * 45, flush=True)
    print("VEHICLE ECU STARTED", flush=True)
    print("VehicleSpeedService ID: 0x1234", flush=True)
    print("Instance ID: 0x5678", flush=True)
    print("=" * 45, flush=True)

    speeds = [0, 30, 50, 70, 80, 90, 100, 60, 0]

    try:
        while True:
            for speed in speeds:
                await asyncio.sleep(3)

                vehicle.current_speed_kmph = speed

                print(
                    f"[SPEED] {speed} km/h",
                    flush=True,
                )

                payload = struct.pack("!H", speed)

                instance.send_event(
                    SPEED_EVENTGROUP_ID,
                    SPEED_CHANGED_EVENT_ID,
                    payload,
                )

                print(
                    "[EVENT] SpeedChanged sent",
                    flush=True,
                )

                if speed > 80:
                    instance.send_event(
                        OVERSPEED_EVENTGROUP_ID,
                        OVERSPEED_WARNING_EVENT_ID,
                        payload,
                    )

                    print(
                        f"[WARNING] OVERSPEED: {speed} km/h",
                        flush=True,
                    )

    finally:
        await instance.stop_offer()
        await daemon.disconnect_from_daemon()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nVehicle ECU stopped")
