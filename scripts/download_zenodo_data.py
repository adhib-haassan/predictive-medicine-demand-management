import argparse
import hashlib
from pathlib import Path

import requests


RECORD_URL = "https://zenodo.org/api/records/18851842"
USER_AGENT = "predictive-medicine-demand-management/1.0"


def _request(url, stream=False):
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        stream=stream,
        timeout=(15, 120),
    )
    response.raise_for_status()
    return response


def _md5(path):
    checksum = hashlib.md5()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def _download_file(file_info, output_dir):
    path = output_dir / file_info["key"]
    checksum_type, expected_checksum = file_info["checksum"].split(":", 1)
    if checksum_type != "md5":
        raise ValueError(f"Unsupported checksum type for {path.name}: {checksum_type}")

    if path.exists():
        actual_checksum = _md5(path)
        if actual_checksum != expected_checksum:
            raise ValueError(f"Existing file checksum mismatch: {path}")
        print(f"Verified {path.name}")
        return

    temporary_path = path.with_name(path.name + ".part")
    try:
        with _request(file_info["links"]["self"], stream=True) as response:
            with temporary_path.open("wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output_file.write(chunk)

        actual_checksum = _md5(temporary_path)
        if actual_checksum != expected_checksum:
            raise ValueError(f"Downloaded file checksum mismatch: {path.name}")
        temporary_path.replace(path)
        print(f"Downloaded and verified {path.name}")
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def main():
    parser = argparse.ArgumentParser(description="Download and verify all files in Zenodo record 18851842.")
    parser.add_argument("--output", type=Path, required=True, help="Directory for the record files")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    record = _request(RECORD_URL).json()

    files = sorted(record["files"], key=lambda item: item["key"].casefold())
    if not files:
        raise ValueError("The Zenodo record contains no files.")

    for file_info in files:
        _download_file(file_info, args.output)

    print(f"Verified {len(files)} files in {args.output}")


if __name__ == "__main__":
    main()