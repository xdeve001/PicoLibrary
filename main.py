"""
main.py
Main entrypoint for the Satisfaction Kiosk.
"""

from Log import *
from FeedbackController import FeedbackController


def main():
    Log.i("Starting Satisfaction Kiosk...")

    controller = FeedbackController(
        satisfaction_threshold=30.0,
        debug=True
    )

    try:
        controller.run()
    except KeyboardInterrupt:
        Log.i("Kiosk interrupted.")
    finally:
        controller.stop()
        Log.i("Satisfaction Kiosk stopped.")


if __name__ == "__main__":
    main()