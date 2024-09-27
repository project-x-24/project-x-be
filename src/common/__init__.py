import signal
from src.common.utils import ThreadTerminateEvent
from src.config import DEV_STREAMLIT

if DEV_STREAMLIT is False:
    # Need to init this here to ensure signal is declared on first src import which is supposed to be where main thread is
    ThreadTerminateEvent()

    signal.signal(signal.SIGINT, ThreadTerminateEvent().signal_handler)
    signal.signal(signal.SIGTERM, ThreadTerminateEvent().signal_handler)
