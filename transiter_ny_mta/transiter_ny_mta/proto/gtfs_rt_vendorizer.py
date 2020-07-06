"""
Vendorize the GTFS realtime protobuf reader and add NYCT extensions on top of it.

The reader is vendorized because the NYCT extension works by modifying the GTFS realtime
reader. By default, it modifies the standard reader google.transiter.gtfs_realtime_pb2.
Given the structure of the reader this is _probably_ okay, but it's safest to vendorize
it because, in Transiter, the standard reader is used by other parsers.

The main difficulty in vendorizing the readers is that the protobuf system namespaces
code in a similar way to the namespacing of Java code. Given a package and a
definition inside that package, the protobuf system assumes (package, definition) is
_globally_ unique. Because of this, we can't do the usual easy Python vendorization
where we just duplicate the gtfs_realtime_pb2.py file and import it separately.

In addition, the profobuf system appears to have two different ways of determining the
package of a protobuf file. The C++ protobuf compiler uses the package declaration
in the proto file. The native Python protobuf compiler uses the location of the proto
file on disk relative to the current working directory. This vendorization script covers
both cases - i.e., ensures that whichever way the package is determined it does not
collide with the package of google.transit.gtfs_realtime_pb2. From trial and error,
covering both cases seems to be necessary.
"""

import os
import requests
import subprocess
import importlib
import dataclasses

GTFS_RT_PROTO_URL = (
    "https://raw.githubusercontent.com/google/transit"
    "/master/gtfs-realtime/proto/gtfs-realtime.proto"
)
TRANSITER_EXT_PROTO_URL = (
    "https://raw.githubusercontent.com/jamespfennell/transiter"
    "/master/transiter/parse/transiter_gtfs_rt_pb2"
    "/gtfs-realtime-transiter-extension.proto"
)
INIT_PY_TEMPLATE = """
from .{} import *
from . import {}
from . import {}

MTA_EXTENSION_ID = {}

"""


@dataclasses.dataclass
class Config:
    key: str
    mta_ext_proto_url: str
    mta_extension_id: int

    @property
    def directory(self):
        return self.key + "_pb2"

    @property
    def gtfs_rt_filename(self):
        return f"transiter-ny-mta-{self.key}-gtfs-rt-base.proto"

    @property
    def mta_filename(self):
        return f"transiter-ny-mta-{self.key}-mta-extension.proto"

    @property
    def transiter_filename(self):
        return self._build_proto_path("transiter-extension")

    def _build_proto_path(self, postfix):
        return f"transiter-ny-mta-{self.key}-{postfix}.proto"


alerts_config = Config(
    key="alerts",
    mta_ext_proto_url=(
        "https://raw.githubusercontent.com/OneBusAway/onebusaway-gtfs-realtime-api"
        "/master/src/main/resources/com/google/transit/realtime/"
        "gtfs-realtime-service-status.proto"
    ),
    mta_extension_id=1001,
)
subway_trips_config = Config(
    key="subwaytrips",
    mta_ext_proto_url=(
        "https://raw.githubusercontent.com/OneBusAway/onebusaway-gtfs-realtime-api"
        "/master/src/main/resources/com/google/transit/realtime/"
        "gtfs-realtime-NYCT.proto"
    ),
    mta_extension_id=1001,
)


def run(config: Config):
    directory = os.path.join(os.path.dirname(__file__), config.directory)
    os.makedirs(directory, exist_ok=True)

    for url, filename in [
        (GTFS_RT_PROTO_URL, config.gtfs_rt_filename),
        (TRANSITER_EXT_PROTO_URL, config.transiter_filename),
        (config.mta_ext_proto_url, config.mta_filename),
    ]:
        print(f"[{config.key}] Generating {filename}")
        response = requests.get(url)
        response.raise_for_status()
        raw_proto = response.text
        proto = _substitute_package_settings(raw_proto, config)
        with open(os.path.join(directory, filename), "w") as f:
            f.write(proto)

    print(f"[{config.key}] Compiling protobufs")
    subprocess.run(
        [
            "protoc",
            "--python_out=.",
            "--proto_path=.",
            config.gtfs_rt_filename,
            config.transiter_filename,
            config.mta_filename,
        ],
        cwd=directory,
    )

    for filename in [
        config.transiter_filename,
        config.mta_filename,
    ]:
        filename = _proto_to_pb2(filename) + ".py"
        print(f"[{config.key}] Fixing Python imports in {filename}")
        with open(os.path.join(directory, filename)) as f:
            content = f.read()
        content = content.replace(
            "import transiter_ny_mta", "from . import transiter_ny_mta"
        )
        with open(os.path.join(directory, filename), "w") as f:
            f.write(content)

    print(f"[{config.key}] Writing __init__.py")
    with open(os.path.join(directory, "__init__.py"), "w") as f:
        f.write(
            INIT_PY_TEMPLATE.format(
                _proto_to_pb2(config.gtfs_rt_filename),
                _proto_to_pb2(config.transiter_filename),
                _proto_to_pb2(config.mta_filename),
                config.mta_extension_id,
            )
        )

    print(f"[{config.key}] Attempting to import generated module...")
    try:
        importlib.import_module(".alerts_pb2", "transiter_ny_mta.proto")
        print(f"[{config.key}] Success")
    except Exception:
        print(f"[{config.key}] Failed! Exiting with stack trace:")
        raise


def _proto_to_pb2(filename):
    return filename[: -len(".proto")].replace("-", "_") + "_pb2"


def _substitute_package_settings(proto: str, config: Config):
    output = []
    for line in proto.splitlines():
        if line.startswith("option java_package"):
            output.append(
                f'option java_package = "com.github.transiter-ny-mta.{config.key}";'
            )
        elif line.startswith("package"):
            output.append(f"package transiter_ny_mta_{config.key};")
        elif line.startswith("import"):
            output.append(f'import "{config.gtfs_rt_filename}";')
        else:
            output.append(line.replace("transit_realtime.", ""))
    return "\n".join(output)


run(alerts_config)
run(subway_trips_config)
