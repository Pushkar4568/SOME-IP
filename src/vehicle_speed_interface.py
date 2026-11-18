from someipy import (
    ServiceBuilder,
    Method,
    Event,
    EventGroup,
    TransportLayerProtocol,
)

SERVICE_ID = 0x1234
INSTANCE_ID = 0x5678

GET_SPEED_METHOD_ID = 0x0001
GET_VEHICLE_STATE_METHOD_ID = 0x0002

SPEED_CHANGED_EVENT_ID = 0x8001
OVERSPEED_WARNING_EVENT_ID = 0x8002

SPEED_EVENTGROUP_ID = 0x0001
OVERSPEED_EVENTGROUP_ID = 0x0002


def build_vehicle_speed_service(
    get_speed_handler=None,
    get_state_handler=None,
):
    service = (
        ServiceBuilder()
        .with_service_id(SERVICE_ID)
        .with_major_version(1)
    )

    service.with_method(
        Method(
            id=GET_SPEED_METHOD_ID,
            protocol=TransportLayerProtocol.UDP,
            method_handler=get_speed_handler,
        )
    )

    service.with_method(
        Method(
            id=GET_VEHICLE_STATE_METHOD_ID,
            protocol=TransportLayerProtocol.UDP,
            method_handler=get_state_handler,
        )
    )

    service.with_eventgroup(
        EventGroup(
            id=SPEED_EVENTGROUP_ID,
            events=[
                Event(
                    id=SPEED_CHANGED_EVENT_ID,
                    protocol=TransportLayerProtocol.UDP,
                )
            ],
        )
    )

    service.with_eventgroup(
        EventGroup(
            id=OVERSPEED_EVENTGROUP_ID,
            events=[
                Event(
                    id=OVERSPEED_WARNING_EVENT_ID,
                    protocol=TransportLayerProtocol.UDP,
                )
            ],
        )
    )

    return service.build()
