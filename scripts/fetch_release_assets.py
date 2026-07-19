from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.parse
import urllib.request

ALLOWED_SOURCE_HOSTS = {"github.com", "huggingface.co"}
CHUNK_SIZE = 1024 * 1024


def main() -> None:
    sources = json.loads(pathlib.Path("manifest/release-sources.json").read_text())
    destination = pathlib.Path("release-assets")
    destination.mkdir(exist_ok=True)

    for artifact in sources["artifacts"]:
        file_name = artifact["fileName"]
        if pathlib.Path(file_name).name != file_name:
            raise ValueError(f"unsafe artifact filename: {file_name}")

        source_url = artifact["sourceUrl"]
        parsed = urllib.parse.urlparse(source_url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_SOURCE_HOSTS:
            raise ValueError(f"unapproved artifact source: {source_url}")

        target = destination / file_name
        digest = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(source_url, timeout=60) as response, target.open("wb") as file:
            while chunk := response.read(CHUNK_SIZE):
                size += len(chunk)
                if size > artifact["sizeBytes"]:
                    raise ValueError(f"{file_name} exceeds its declared size")
                digest.update(chunk)
                file.write(chunk)

        if size != artifact["sizeBytes"]:
            raise ValueError(f"{file_name} has size {size}, expected {artifact['sizeBytes']}")
        if digest.hexdigest() != artifact["sha256"]:
            raise ValueError(f"{file_name} failed its SHA-256 check")

        print(f"verified {file_name}: {size} bytes")


if __name__ == "__main__":
    main()
