# Photius validation performance

Measured on October 21, 2026, using Python 3.14.6 on macOS with 18 CPU cores and
128 GiB RAM. Each revision ran in a fresh process against the same frozen corpus
and audit archives. The second iteration retained that process's caches.
The baseline is commit `0ce979cab234462e040eb869e1f9ce9a22935036`.
Both runs used the `corpus-2026-10-21.2` declaration in `CITATION.cff`, which
appears in the coverage result's publication metadata.

| Photius coverage resolution | Baseline | Cached compression | Reduction |
| --- | ---: | ---: | ---: |
| First iteration | 278.681 s | 208.032 s | 25.4% |
| Repeated iteration | 192.330 s | 111.273 s | 42.1% |
| First-iteration gzip calls | 215 | 36 | 83.3% |
| Repeated-iteration gzip calls | 213 | 0 | 100% |
| Process peak memory after both iterations | 5.62 GB | 6.38 GB | — |

Both iterations on both revisions returned the same canonical coverage JSON
SHA-256: `6fa0af14f08b3fb1e16d70c0e7d9248470fad6afa0859213a826e014fbc48a9e`.
The baseline compressed 4.48 GB and 3.88 GB of input in its two iterations;
the changed implementation compressed 1.24 GB and zero bytes. These are sums
over calls, including repeated inputs, rather than unique corpus sizes.

Peak process memory increased in this measurement. The new gzip cache retains
at most 128 MiB of compressed values and 128 entries; its keys contain input
digests and lengths rather than uncompressed corpus buffers. Process peak
memory also includes the existing parsed records, replay plans, and allocator
behavior. A faster check is not evidence of a lower memory requirement.

`scripts/benchmark_photius_validation.py` prints the measurements and output
hashes without writing corpus data. For a comparison with a revision that does
not contain the runner, copy the runner outside both checkouts and select each
revision's modules with `PYTHONPATH`:

```sh
PYTHONPATH=BASE_CHECKOUT/scripts python3 BENCHMARK_RUNNER.py --root FROZEN_INPUTS --repeat 2
PYTHONPATH=CHANGED_CHECKOUT/scripts python3 BENCHMARK_RUNNER.py --root FROZEN_INPUTS --repeat 2
```

Use fresh processes, the same Python and compression libraries, identical input
bytes, and similar machine load. Compare output hashes before comparing times.
These measurements cover Photius coverage resolution, not the entire release
pipeline or model inference.
