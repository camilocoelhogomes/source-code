# Unit test plan — T34-fix-host-local-repos-path-resolution

| Campo | Valor |
|---|---|
| Task | `T34-fix-host-local-repos-path-resolution` |
| Estado | `APPROVED_BY_ARCHITECT` |
| Versão | `0.1.0` |

## UT-T34-01 — `remap_repos_mount_path` sem host_repos

| Entrada | Saída |
|---|---|
| `/repos`, `None` | `/repos` |
| `/repos/foo`, `""` | `/repos/foo` |

## UT-T34-02 — remap root e subpath

| Entrada | Saída |
|---|---|
| `/repos`, `/tmp/host-repos` | `Path("/tmp/host-repos").resolve()` |
| `/repos/sample-local`, `/tmp/host-repos` | `resolve(/tmp/host-repos/sample-local)` |

## UT-T34-03 — paths não-/repos inalterados

| Entrada | Saída |
|---|---|
| `/mnt/data`, `/tmp/host-repos` | `/mnt/data` |

## UT-T34-04 — discovery com host_repos descobre via file:///repos/*

Mock inspector ou repo real; `host_repos` setado; base acessível pós-remap.

## UT-T34-05 — discovery sem host_repos: /repos inacessível → issue

Paridade T06 LOC-03.

## UT-T34-06 — `wire_catalog_sync` passa HOST_REPOS

Assert `LocalRepoDiscovery` construído com `host_repos` do environ.
