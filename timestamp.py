import argparse
import datetime as dt
from pathlib import PurePath
from typing import Any, Dict, Tuple

import av
import cv2 as cv
import yaml

DEBUG = False
DEFAULT_CONFIG = {
    "timestamp": {
        "origin_px": (25, 25),
        "scale_factor": 2.0,
        "color_rgb_uint8": (255, 0, 0),
        "thickness_px": 3,
    }
}


def parse_args() -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Adds timestamps to timelapse videos.")
    parser.add_argument(
        "--interval",
        "-i",
        type=float,
        nargs=1,
        required=False,
        help="Wall clock interval between frames in seconds.",
    )
    parser.add_argument("input", type=PurePath, nargs="?", help="Input file path.")
    parser.add_argument(
        "output", type=PurePath, nargs="?", help="Output file path.", default=None
    )
    parser.add_argument("--rebuild-config", action="store_true", default=False)
    args = parser.parse_args()

    if args.rebuild_config:
        parsed = {"rebuild_config": True}
    else:
        frame_interval_seconds: int = args.interval[0]
        input_path: PurePath = args.input
        if args.output is None:
            new_file_name = (
                "-".join([input_path.stem.split(".")[0], "timestamped"])
                + input_path.suffix
            )
            output_path: PurePath = input_path.parent / new_file_name
        else:
            output_path: PurePath = args.output[0]
        parsed = {
            "frame_interval_seconds": frame_interval_seconds,
            "input_path": input_path,
            "output_path": output_path,
        }

    return parsed


def read_config() -> Dict[str, Any]:
    with open("config.yml", "r") as f:
        try:
            config_missing = False
            config = yaml.safe_load(f)
        except:
            config_missing = True
            config = DEFAULT_CONFIG

    if config_missing:
        rebuild_config()

    return config


def rebuild_config() -> None:
    with open("config.yml", "w") as f:
        yaml.safe_dump(DEFAULT_CONFIG, f)


def create_timestamp(frame_number: int, frame_interval_seconds: float) -> str:
    current_time_seconds = frame_number * frame_interval_seconds
    time_seconds_delta = dt.timedelta(seconds=current_time_seconds)
    timestamp = format_timedelta_in_hundredths_of_seconds(t=time_seconds_delta)
    return timestamp


def format_timedelta_in_hundredths_of_seconds(t: dt.timedelta) -> str:
    # HUNDREDTHS_OF_SECONDS_PER_DAY = 24 * 60 * 60 * 100
    HUNDREDTHS_OF_SECONDS_PER_HOUR = 60 * 60 * 100
    HUNDREDTHS_OF_SECONDS_PER_MINUTE = 60 * 100
    HUNDREDTHS_OF_SECONDS_PER_SECOND = 100
    MICROSECONDS_PER_HUNDREDTHS_OF_SECONDS = 10000

    microseconds_total = t / dt.timedelta(microseconds=1)
    hundredths_of_seconds_total = (
        microseconds_total / MICROSECONDS_PER_HUNDREDTHS_OF_SECONDS
    )

    remainder = hundredths_of_seconds_total
    # days, remainder = divmod(remainder, HUNDREDTHS_OF_SECONDS_PER_DAY)
    hours, remainder = divmod(remainder, HUNDREDTHS_OF_SECONDS_PER_HOUR)
    minutes, remainder = divmod(remainder, HUNDREDTHS_OF_SECONDS_PER_MINUTE)
    seconds, remainder = divmod(remainder, HUNDREDTHS_OF_SECONDS_PER_SECOND)
    # hundredths_of_seconds = remainder

    # days = int(days)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    # hundredths_of_seconds = int(hundredths_of_seconds)

    # lead with: {days:03d}
    # end with: .{hundredths_of_seconds:02d}
    out = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return out


def transform_frame(
    frame: av.VideoFrame,
    timestamp: str,
    origin_px: Tuple[int, int],
    scale_factor: float,
    color_rgb: Tuple[int, int, int],
    thickness_px: float,
) -> av.VideoFrame:
    stamped_frame = cv.putText(
        frame.to_rgb().to_ndarray(),
        timestamp,
        origin_px,
        cv.FONT_HERSHEY_SIMPLEX,
        scale_factor,
        color_rgb,
        thickness_px,
    )
    stamped_frame = av.VideoFrame.from_ndarray(stamped_frame)
    return stamped_frame


def interface() -> None:
    args = parse_args()
    if "rebuild_config" in args:
        rebuild_config()
        print("Config rebuilt using defaults. Exiting...")
        exit()

    config = read_config()

    try:
        timestamp_config = config["timestamp"]
    except:
        raise RuntimeError(
            "config not formatted correctly, please delete config.yml and try again"
        )

    # prepare input container
    input_v = av.open(str(args["input_path"]))
    input_stream = input_v.streams.video[0]
    width = input_stream.width
    height = input_stream.height

    # prepare output container
    output_v = av.open(str(args["output_path"]), "w")
    output_stream = output_v.add_stream("h264")
    output_stream.width = width
    output_stream.height = height

    # transform values
    origin_px: Tuple[int, int] = timestamp_config.get("origin_px", (25, 25))
    scale_factor: float = timestamp_config.get("scale_factor", 2.0)
    color_rgb: Tuple[int, int, int] = timestamp_config.get(
        "color_rgb_uint8", (255, 0, 0)
    )
    thickness_px: float = timestamp_config.get("thickness_px", 3.0)

    # transform text origin
    origin_px = (origin_px[0], height - origin_px[1] + 1)

    for frame in input_v.decode(input_stream, video=0):
        if DEBUG and frame.index >= 100:
            break

        timestamp = create_timestamp(
            frame_number=frame.index,
            frame_interval_seconds=args["frame_interval_seconds"],
        )
        stamped_frame = transform_frame(
            frame=frame,
            timestamp=timestamp,
            origin_px=origin_px,
            scale_factor=scale_factor,
            color_rgb=color_rgb,
            thickness_px=thickness_px,
        )

        # encode
        for packet in output_stream.encode(stamped_frame):
            output_v.mux(packet)

    # flush buffer
    for packet in output_stream.encode(None):
        output_v.mux(packet)

    # close containers
    input_v.close()
    output_v.close()


if __name__ == "__main__":
    interface()
