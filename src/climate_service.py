import asyncio
import struct

from someipy import (
    ServerServiceInstance,
    MethodResult,
    MessageType,
    ReturnCode,
    connect_to_someipy_daemon,
)

from climate_interface import (
    CLIMATE_INSTANCE_ID,
    CABIN_TEMPERATURE_CHANGED_EVENT_ID,
    CABIN_TEMPERATURE_EVENTGROUP_ID,
    build_climate_service,
)


class ClimateECU:
    def __init__(self):
        self.cabin_temperature = 240
        self.target_temperature = 220

    def response(self, payload, code=ReturnCode.E_OK):
        result = MethodResult()
        result.message_type = MessageType.RESPONSE
        result.return_code = code
        result.payload = payload
        return result

    async def get_cabin_temperature(self, data, addr):
        print("[METHOD] GetCabinTemperature", flush=True)
        return self.response(
            struct.pack("!h", self.cabin_temperature)
        )

    async def set_target_temperature(self, data, addr):
        if len(data) != 2:
            print("[ERROR] Invalid request payload", flush=True)
            return self.response(
                b"", ReturnCode.E_MALFORMED_MESSAGE
            )

        requested = struct.unpack("!h", data)[0]
        print(
            f"[METHOD] SetTargetTemperature: {requested / 10:.1f} C",
            flush=True,
        )

        if 160 <= requested <= 300:
            self.target_temperature = requested
            print("[STATUS] ACCEPTED", flush=True)
            return self.response(struct.pack("!B", 0))

        print("[STATUS] INVALID_TEMPERATURE", flush=True)
        return self.response(struct.pack("!B", 1))


async def main():
    climate = ClimateECU()
    daemon = await connect_to_someipy_daemon()

    service = build_climate_service(
        climate.get_cabin_temperature,
        climate.set_target_temperature,
    )

    instance = ServerServiceInstance(
        daemon=daemon,
        service=service,
        instance_id=CLIMATE_INSTANCE_ID,
        endpoint_ip="127.0.0.1",
        endpoint_port=3002,
        ttl=5,
        cyclic_offer_delay_ms=2000,
    )

    await instance.start_offer()

    print("=" * 45, flush=True)
    print("CLIMATE ECU STARTED", flush=True)
    print("ClimateService ID: 0x2234", flush=True)
    print("Instance ID: 0x0001", flush=True)
    print("Initial Cabin Temperature: 24.0 C", flush=True)
    print("Target Temperature: 22.0 C", flush=True)
    print("=" * 45, flush=True)

    temperatures = [240, 245, 250, 255, 260, 255, 250]

    try:
        while True:
            for temperature in temperatures:
                await asyncio.sleep(4)

                if climate.cabin_temperature == temperature:
                    continue

                climate.cabin_temperature = temperature

                print(
                    f"[TEMP] Cabin: {temperature / 10:.1f} C",
                    flush=True,
                )

                instance.send_event(
                    CABIN_TEMPERATURE_EVENTGROUP_ID,
                    CABIN_TEMPERATURE_CHANGED_EVENT_ID,
                    struct.pack("!h", temperature),
                )

                print(
                    "[EVENT] CabinTemperatureChanged sent",
                    flush=True,
                )

    finally:
        await instance.stop_offer()
        await daemon.disconnect_from_daemon()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClimate ECU stopped")
