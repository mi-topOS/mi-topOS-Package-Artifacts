# mi-topOS Package Artifacts

This repository aggregates Debian package release assets from the selected
`mi-topOS` package repositories into a single bundle release for the image
builder.

## Bootstrap flow

1. Each source package repository publishes Bookworm arm64 `.deb` assets to a
   GitHub release.
2. The workflow in this repository downloads those release assets using a
   checked-in bundle manifest.
3. The workflow publishes a new bundle release containing the complete package
   set plus a machine-readable manifest.

## Files

- `bundle-manifests/bookworm-arm64-bootstrap-1.json`: source release manifest
- `scripts/assemble_bundle.py`: downloads `.deb` assets and emits checksums
- `.github/workflows/publish-bundle.yml`: creates the bundle release
