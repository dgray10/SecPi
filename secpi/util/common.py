import datetime
import functools
import importlib
import logging
import logging.config
import pathlib
import random
import string
import sys
import tempfile
import threading
import time
import typing as t
from collections import OrderedDict
from concurrent.futures import Future, ThreadPoolExecutor
from copy import copy

import dateutil.parser
import netifaces
from dataclass_wizard import DumpMeta, JSONSerializable

# import pytz


logger = logging.getLogger(__name__)


def filter_fields(fields, filter):
    filtered_data = OrderedDict()

    for k, v in fields.items():
        if filter in v["visible"]:
            filtered_data[k] = v

    return filtered_data


def str_to_value(val):
    # print("checking %s: %s\n"%(val, type(val)))
    if isinstance(val, (str, bytes)):

        if val == "None":
            return None
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                try:
                    dat = dateutil.parser.parse(val)
                    return dat.replace(tzinfo=None)  # pytz.UTC.localize(dat)
                except Exception:
                    return val

    return val


def check_late_arrival(date_message):
    date_now = datetime.datetime.now()

    if (date_now - date_message) < datetime.timedelta(0, 30):  # TODO: make delta configurable?
        return False
    else:
        return True


def setup_logging(level=logging.INFO, config_file=None, log_file=None):
    if config_file:
        config_file = pathlib.Path(config_file)
        if not config_file.exists():
            raise FileNotFoundError(f"Logging configuration file '{config_file}' not found")
        if log_file is None:
            tmpfile = tempfile.NamedTemporaryFile(delete=False)
            log_file = tmpfile.name
        logging.config.fileConfig(config_file, defaults={"logfile": log_file}, disable_existing_loggers=False)
    else:
        log_format = "%(asctime)-15s [%(name)-34s] %(levelname)-7s: %(message)s"
        logging.basicConfig(format=log_format, stream=sys.stderr, level=level)

    # if logging.getLogger().level == logging.DEBUG:
    pika_logger = logging.getLogger("pika")
    pika_logger.setLevel(logging.WARNING)

    if config_file and log_file:
        logger.info(f"Using log file {log_file}")


def get_ip_addresses():
    """
    Return the configured ip addresses (v4 & v6) as list.
    """
    result = []
    # Iterate through interfaces: eth0, eth1, wlan0, etc.
    for interface in netifaces.interfaces():
        if (interface != "lo") and (
            netifaces.AF_INET in netifaces.ifaddresses(interface)
        ):  # filter loopback, and active ipv4
            for ip_address in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                logger.debug("Adding %s IP to result" % ip_address["addr"])
                result.append(ip_address["addr"])
        if (interface != "lo") and (
            netifaces.AF_INET6 in netifaces.ifaddresses(interface)
        ):  # filter loopback, and active ipv6
            for ipv6_address in netifaces.ifaddresses(interface)[netifaces.AF_INET6]:
                logger.debug("Adding %s IP to result" % ipv6_address["addr"])
                result.append(ipv6_address["addr"])

    return result


def sleep_threaded(delay):
    waiter = threading.Thread(target=functools.partial(time.sleep, delay), args=())
    waiter.start()
    waiter.join()


def to_list(x, default=None):
    if x is None:
        return default
    if not isinstance(x, (list, tuple)):
        return [x]
    else:
        return x


def load_class(module_names, class_names, errors: str = "raise"):
    """
    Load class from dotted string notation.

    https://stackoverflow.com/questions/1176136/convert-string-to-python-class-object
    """
    module_names = to_list(module_names)
    class_names = to_list(class_names)

    # TODO: Implement multiple class names.
    class_name = class_names[0]

    recorded_exceptions = []
    for module in module_names:
        try:
            # Load the module.
            m = importlib.import_module(module)

            # Get the class from module.
            c = getattr(m, class_name)
            logger.info(f"Loading class successful: {module}.{class_name}")
            return c

        except Exception as ex:
            recorded_exceptions.append(ex)

    # Forward all exceptions to log output.
    for ex in recorded_exceptions:
        logger.exception(ex)

    # Re-raise first exception.
    # TODO: When there is more than one exception, prefer non-ImportError's to re-raise.
    #       Rationale: When, for example, importing an action like ``buzzer.Buzzer``, the first
    #       exception would be like ``ImportError: Unable to import secpi.sensor.buzzer.Buzzer``,
    #       because the ``secpi.sensor`` namespace is tried first.
    if errors == "raise":
        exception = recorded_exceptions[0]
        exception.all_exceptions = recorded_exceptions
        raise exception


def get_random_identifier(length):
    """
    Create random identifiers like `GSKHJ` or `AMB3C`.
    """
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


class DataContainer(JSONSerializable):
    """
    Helper for JSONWizard that ensures dumping to JSON puts keys in snake_case.

    https://github.com/rnag/dataclass-wizard/issues/63
    """

    def __init_subclass__(cls, str=True):
        """
        Method for binding child class to DumpMeta.
        """
        super().__init_subclass__(str)
        DumpMeta(key_transform="SNAKE").bind_to(cls)


def sa_record_to_dict(row, with_class_tweak=False):
    """
    Convert SQLAlchemy object to dictionary.

    https://stackoverflow.com/a/68775487
    """
    record = copy(row.__dict__)
    del record["_sa_instance_state"]

    if with_class_tweak:
        record["class"] = record["cl"]
        del record["cl"]

    return record


def run_tasks(tasks: t.List[t.Callable]) -> t.List[Future]:
    futures: t.List[Future] = []
    with ThreadPoolExecutor() as executor:
        for task in tasks:
            future = executor.submit(task)
            futures.append(future)
    return futures
