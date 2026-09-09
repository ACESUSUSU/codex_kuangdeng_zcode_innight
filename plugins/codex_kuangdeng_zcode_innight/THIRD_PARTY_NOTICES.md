# Third-Party Sources

computer-use-linux v0.5.0 is developed by Avi Fenesh and contributors:
https://github.com/agent-sh/computer-use-linux

The bundled source archive is the upstream v0.5.0 archive (GitHub archive root
agent-sh-computer-use-linux-c785f85). It is redistributed under MIT, with its
original LICENSE preserved both in the archive and in assets/UPSTREAM-LICENSE.
The Ubuntu changes are an additional patch, not an upstream release.

The runtime is built on the destination machine from this source and the
included Cargo.lock. Rust dependencies are downloaded from their configured
registries and retain their own licenses. No compiled runtime or Rust
dependency source is included in the plugin ZIP.

The optional stdio console uses @modelcontextprotocol/sdk 1.30.0, installed
from npm by the setup script. The SDK is not vendored in this archive and
retains its own MIT license. System GTK/X11 tools are prerequisites, not
bundled packages.

Official ZCode and GLM services are separate products. This plugin does not
redistribute ZCode, include its credentials, or claim official endorsement.
