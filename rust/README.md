# BPIO2 tooling for Rust

In this directory you can find:

- `tooling/bpio_generated.rs`: the flatbuffer code generated from the `bpio.fbs` schema using `flatc`
- `include/`: a copy of the [`flatbuffers` crate][fbc] needed to use the generated code
- `bpio2/`: a crate that packages the generated code in a way that allows users to avoid
  build problems caused by including the `bpio_generated.rs` file directly in their own
  projects. It also includes an example that shows how to use the flatbuffers to
  communicate with the Bus Pirate.

[fbc]: https://crates.io/crates/flatbuffers
