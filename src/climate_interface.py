from someipy import (
    ServiceBuilder,
    Method,
    Event,
    EventGroup,
    TransportLayerProtocol,
)

CLIMATE_SERVICE_ID = 0x2234
CLIMATE_INSTANCE_ID = 0x0001

GET_CABIN_TEMPERATURE_METHOD_ID = 0x0001
SET_TARGET_TEMPERATURE_METHOD_ID = 0x0002

CABIN_TEMPERATURE_CHANGED_EVENT_ID = 0x8001
CABIN_TEMPERATURE_EVENTGROUP_ID = 0x0001


def build_climate_service(
    get_temperature_handler=None,
    set_temperature_handler=None,
):
    return (
        ServiceBuilder()
        .with_service_id(CLIMATE_SERVICE_ID)
        .with_major_version(1)
        .with_method(
            Method(
                id=GET_CABIN_TEMPERATURE_METHOD_ID,
                protocol=TransportLayerProtocol.UDP,
                method_handler=get_temperature_handler,
            )
        )
        .with_method(
            Method(
                id=SET_TARGET_TEMPERATURE_METHOD_ID,
                protocol=TransportLayerProtocol.UDP,
                method_handler=set_temperature_handler,
            )
        )
        .with_eventgroup(
            EventGroup(
                id=CABIN_TEMPERATURE_EVENTGROUP_ID,
                events=[
                    Event(
                        id=CABIN_TEMPERATURE_CHANGED_EVENT_ID,
                        protocol=TransportLayerProtocol.UDP,
                    )
                ],
            )
        )
        .build()
    )
