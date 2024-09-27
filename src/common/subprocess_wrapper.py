# Refactored out from src.video_slicer.v2.scene_utils
import subprocess
import resource
import src.config as config

from typing import List, Tuple

from src.common.logger.logger import get_logger


logger = get_logger(__name__)

def limit_virtual_memory():
    # NOTE: DON'T PRINT HERE AS IT WILL GO INTO ANY CMD LINE OUTPUTS AND BREAKS TERMINAL OUTPUT PARSING IN FFMPEG
    resource.setrlimit(resource.RLIMIT_AS, (config.MAX_VIRTUAL_MEMORY, config.MAX_VIRTUAL_MEMORY))

def __format_return_messages(output: bytes, error: bytes) -> Tuple[str, str]:
    try:
        output = output.decode('utf-8', 'ignore')

    except Exception as e:
        logger.debug(e, exc_info=True)

        try:
            output = str(output)

        except Exception as e:
            logger.debug(e, exc_info=True)
            output = ''

    try:
        error = error.decode('utf-8', 'ignore')

    except Exception as e:
        logger.debug(e, exc_info=True)

        try:
            error = str(error)

        except Exception as e:
            logger.debug(e, exc_info=True)
            error = ''

    return output, error


def run_subprocess_wrapper(cmd: List[str]) -> Tuple[str, str, int]:
    p = subprocess.Popen(cmd,
                         preexec_fn=limit_virtual_memory,
                         close_fds=True,
                         shell=False,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         universal_newlines=False)

    output, errors = p.communicate()
    output, errors = __format_return_messages(output, errors)

    return_code = p.returncode

    return output, errors, return_code
