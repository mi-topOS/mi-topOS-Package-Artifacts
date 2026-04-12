#!/usr/bin/env python3

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    output_dir = args.output_dir.resolve()
    packages_dir = output_dir / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    package_entries = []
    for source in manifest["sources"]:
        repo = source["repo"]
        release_tag = source["release_tag"]
        github_repo = source.get("github", f"mi-topOS/{repo}")
        deb_zip_pattern = source.get("deb_zip_pattern")
        repo_dir = packages_dir / repo
        repo_dir.mkdir(parents=True, exist_ok=True)

        if deb_zip_pattern:
            subprocess.run(
                [
                    "gh",
                    "release",
                    "download",
                    release_tag,
                    "--repo",
                    github_repo,
                    "--pattern",
                    deb_zip_pattern,
                    "--dir",
                    str(repo_dir),
                ],
                check=True,
            )
            for zpath in list(repo_dir.glob("*.zip")):
                with zipfile.ZipFile(zpath, "r") as zf:
                    zf.extractall(repo_dir)
                zpath.unlink()
            for deb in sorted(repo_dir.rglob("*.deb")):
                if deb.parent != repo_dir:
                    dest = repo_dir / deb.name
                    if dest.exists():
                        dest.unlink()
                    shutil.move(str(deb), dest)
            artifacts_dir = repo_dir / "artifacts"
            if artifacts_dir.is_dir():
                shutil.rmtree(artifacts_dir, ignore_errors=True)
        else:
            subprocess.run(
                [
                    "gh",
                    "release",
                    "download",
                    release_tag,
                    "--repo",
                    github_repo,
                    "--pattern",
                    "*.deb",
                    "--dir",
                    str(repo_dir),
                ],
                check=True,
            )

        for package_path in sorted(repo_dir.glob("*.deb")):
            package_entries.append(
                {
                    "repo": repo,
                    "release_tag": release_tag,
                    "filename": package_path.name,
                    "sha256": sha256(package_path),
                    "size_bytes": package_path.stat().st_size,
                }
            )

    bundle_manifest = {
        "bundle_tag": manifest["bundle_tag"],
        "distro": manifest["distro"],
        "architecture": manifest["architecture"],
        "packages": package_entries,
    }
    bundle_manifest_path = output_dir / manifest["manifest_asset"]
    bundle_manifest_path.write_text(json.dumps(bundle_manifest, indent=2) + "\n")

    github_output = Path.cwd() / ".bundle-output"
    github_output.write_text(
        "\n".join(
            [
                f"bundle_tag={manifest['bundle_tag']}",
                f"manifest_asset={manifest['manifest_asset']}",
            ]
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
