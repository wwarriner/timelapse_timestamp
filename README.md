# Timelapse Timestamp

Small Python utility to add wallclock timestamps to timelapse videos.

## Setup

It is assumed that [Anaconda](https://anaconda.org/) is installed. Dependencies are listed in `env.yml`. The simplest way to pull the dependencies is to use `conda env create -f env.yml` to create the environment.

## Configuration

Configuration is limited, options are available in `config.yml`. There is not a lot of error checking so be gentle. The expected data types are written using the Python typing module syntax. Units are variable name suffixes where appropriate.

- `origin_px`: `Tuple[int, int]` List of two pixel values denoting lower-left position of the timestamp, starting from the bottom-left corner of the video.
- `scale_factor`: `float` Timestamp text size scaling factor.
- `color_rgb_uint8`: `Tuple[int, int, int]` List of three integers in the range `[0, 255]` denoting an RGB color for the timestamp text.
- `thickness_px`: `float` Positive float indicating thickness of timestamp text in pixels. Affected by `scale_factor`.

If the config is deleted, simply run the application with only the flag `--rebuild-config`.

## Usage

Typical example for a timelapse frame interval of 5 seconds: `python timestamp.py -i 5 "path/to/video-file.mp4"`

To specify an output, add a second path as `python timestamp.py -i 5 "path/to/input.mp4" "path/for/output.mp4"`

If no output is specified, the input name will be used with `-timestamped` appended.

To force a config refresh use `python timestamp.py --rebuild-config`.

### Formats

`python timestamp.py -i N input-file [output-file]`

`python timestamp.py --rebuild-config`

### Flags

`--rebuild-config` forces a rebuild of the config file. This is a destructive change that cannot be undone. No other flags are required with this flag.

`-i`, `--interval` specify the interval between timelapse frames in seconds. Required for typical use.

`input-file` is a path to the input video file.

`[output-file]` is the optional location to write the output.

## Known Issues

`PyAV` uses `ffmpeg` on the backend, and there is a spurious warning involving color space ranges when writing each frame. These warnings may be ignored.

## Developer Notes

- `PyAV` for video IO operations.
- `cv2.putText()` to place the timestamp text on each frame.
- `pyyaml` for config.
