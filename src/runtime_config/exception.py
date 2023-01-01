class ServiceInstanceNotFound(Exception):
    default_msg: str = (
        "Failed to find service instance {service_name}, " "initialize service before attempting to get an instance."
    )

    def __init__(self, service_name: str, msg: str = default_msg) -> None:
        super().__init__(msg.format(service_name=service_name))
