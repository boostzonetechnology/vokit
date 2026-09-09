"""Vokit self-hosted Pipecat voice peer."""

__all__ = ["app"]


def __getattr__(name: str):
    if name == "app":
        from vokit_pipecat_voice.app import app

        return app
    raise AttributeError(name)
