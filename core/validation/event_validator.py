from shared.models.event import Event


class EventValidationError(Exception):
    pass


class EventValidator:

    @staticmethod
    def validate(event: Event) -> None:

        if not event.source:
            raise EventValidationError("Missing event source")

        if not event.target:
            raise EventValidationError("Missing event target")

        if not event.event_type:
            raise EventValidationError("Missing event type")
