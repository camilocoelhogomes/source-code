"""Unit — manifesto zoekt compose + docs pré-req (T22 / UT-Z*).

Cobre extremos/corners do contrato M-T22-* sem duplicar cegamente o BDD.
Sem compose up; sem secrets; sem alterar produção.
"""

from __future__ import annotations

import re
import unittest

from tests.support.compose_manifest import (
    ZOEKT_COMMAND_TOKENS,
    assert_compose_provider_prereq_docs,
    assert_no_embedded_secrets,
    assert_zoekt_webserver_command,
    parse_command_argv,
    service_block,
    zoekt_command_blob,
)
from tests.unit.delivery.helpers import (
    COMPOSE,
    COMPOSE_DEV,
    COMPOSE_E2E,
    COMPOSE_FILES,
    REPO_ROOT,
    read_text,
)

E2E_README = REPO_ROOT / "e2e" / "README.md"
RUNBOOK = REPO_ROOT / "docs" / "runbook-local.md"

_CANONICAL_COMMAND = (
    'command: ["zoekt-webserver", "-index", "/data/index", "-rpc"]'
)


def _compose_with_zoekt(
    *,
    command_line: str | None = _CANONICAL_COMMAND,
    image: str = "sourcegraph/zoekt:latest",
    extra_zoekt: str = "",
    volume_line: str = "      - zoekt_index:/data/index\n",
) -> str:
    """YAML sintético mínimo com serviço zoekt (para corners)."""
    command_block = f"    {command_line}\n" if command_line is not None else ""
    return (
        "services:\n"
        "  zoekt:\n"
        f"    image: {image}\n"
        f"{command_block}"
        "    volumes:\n"
        f"{volume_line}"
        "    environment:\n"
        "      ZOEKT_INDEX_DIR: /data/index\n"
        "    ports:\n"
        '      - "6070:6070"\n'
        f"{extra_zoekt}"
        "  app:\n"
        "    image: example\n"
    )


class TestUTZRepoManifestContracts(unittest.TestCase):
    """UT-Z01..Z05 — contratos nos três composes reais (RED até Developer)."""

    def test_ut_z01_zoekt_command_in_each_compose(self) -> None:
        errors: list[str] = []
        for path in COMPOSE_FILES:
            try:
                assert_zoekt_webserver_command(
                    read_text(path), compose_name=path.name
                )
            except AssertionError as exc:
                errors.append(f"{path.name}: {exc}")
        self.assertEqual(errors, [], msg="\n".join(errors))

    def test_ut_z02_parity_across_user_e2e_dev(self) -> None:
        argvs: dict[str, list[str]] = {}
        for path in COMPOSE_FILES:
            blob = assert_zoekt_webserver_command(
                read_text(path), compose_name=path.name
            )
            argvs[path.name] = parse_command_argv(blob)
        # Mesmo argv efetivo (tokens canônicos na mesma ordem lógica).
        expected = list(ZOEKT_COMMAND_TOKENS)
        for name, argv in argvs.items():
            positions = [argv.index(t) for t in expected]
            self.assertEqual(
                positions,
                sorted(positions),
                msg=f"{name}: ordem lógica distinta",
            )
            for token in expected:
                self.assertIn(token, argv, msg=f"{name}: falta {token!r}")

    def test_ut_z03_no_entrypoint_override_prefer_command_only(self) -> None:
        errors: list[str] = []
        for path in COMPOSE_FILES:
            text = read_text(path)
            block = service_block(text, "zoekt")
            if re.search(r"^\s*entrypoint\s*:", block, re.M):
                errors.append(
                    f"{path.name}: não sobrescrever entrypoint (preservar tini)"
                )
            try:
                zoekt_command_blob(text)
            except AssertionError as exc:
                errors.append(f"{path.name}: {exc}")
        self.assertEqual(errors, [], msg="\n".join(errors))

    def test_ut_z04_index_volume_and_env_port(self) -> None:
        for path in COMPOSE_FILES:
            with self.subTest(compose=path.name):
                block = service_block(read_text(path), "zoekt")
                self.assertIn("/data/index", block)
                self.assertRegex(block, re.compile(r"ZOEKT_INDEX_DIR", re.I))
                self.assertIn("6070", block)

    def test_ut_z05_compose_roles_all_present(self) -> None:
        self.assertEqual(
            {p.name for p in COMPOSE_FILES},
            {
                "docker-compose.yml",
                "docker-compose.e2e.yml",
                "docker-compose.dev.yml",
            },
        )
        for path in (COMPOSE, COMPOSE_E2E, COMPOSE_DEV):
            self.assertTrue(path.is_file(), msg=f"compose ausente: {path.name}")


class TestUTZDocsProviderPrereq(unittest.TestCase):
    """UT-Z06 — docs leves M-T22-010..012 (RED até Developer)."""

    def test_ut_z06_e2e_readme_and_runbook_provider_strings(self) -> None:
        errors: list[str] = []
        for path in (E2E_README, RUNBOOK):
            try:
                assert_compose_provider_prereq_docs(
                    read_text(path),
                    doc_name=str(path.relative_to(REPO_ROOT)),
                )
            except AssertionError as exc:
                errors.append(str(exc))
        self.assertEqual(errors, [], msg="\n".join(errors))


class TestUTZNoSecrets(unittest.TestCase):
    """UT-Z07 — M-T22-006/014."""

    def test_ut_z07_composes_and_docs_no_embedded_secrets(self) -> None:
        for path in (*COMPOSE_FILES, E2E_README, RUNBOOK):
            with self.subTest(path=path.name):
                assert_no_embedded_secrets(
                    read_text(path), artifact_name=path.name
                )


class TestUTZExtremesSynthetic(unittest.TestCase):
    """UT-Z10..Z19 — extremos/corners com YAML sintético (helpers)."""

    def test_ut_z10_missing_command_raises_f_t04_002(self) -> None:
        text = _compose_with_zoekt(command_line=None)
        with self.assertRaises(AssertionError) as ctx:
            zoekt_command_blob(text)
        self.assertIn("sem `command`", str(ctx.exception))
        self.assertIn("F-T04-002", str(ctx.exception))

    def test_ut_z11_command_only_tini_rejected(self) -> None:
        text = _compose_with_zoekt(
            command_line='command: ["/sbin/tini", "--"]'
        )
        with self.assertRaises(AssertionError) as ctx:
            assert_zoekt_webserver_command(text, compose_name="synthetic")
        self.assertIn("zoekt-webserver", str(ctx.exception))

    def test_ut_z12_wrong_command_zoekt_index_rejected(self) -> None:
        text = _compose_with_zoekt(
            command_line='command: ["zoekt-index", "-index", "/data/index"]'
        )
        with self.assertRaises(AssertionError) as ctx:
            assert_zoekt_webserver_command(text, compose_name="synthetic")
        msg = str(ctx.exception)
        self.assertTrue(
            "zoekt-webserver" in msg or "-rpc" in msg,
            msg=f"esperado rejeitar argv de indexação: {msg}",
        )

    def test_ut_z13_image_tag_change_command_ok_passes(self) -> None:
        text = _compose_with_zoekt(image="sourcegraph/zoekt:5.0.0")
        blob = assert_zoekt_webserver_command(text, compose_name="synthetic")
        self.assertIn("zoekt-webserver", blob)

    def test_ut_z14_multiline_yaml_command_accepted(self) -> None:
        text = _compose_with_zoekt(
            command_line=(
                "command:\n"
                "      - zoekt-webserver\n"
                "      - -index\n"
                "      - /data/index\n"
                "      - -rpc"
            )
        )
        blob = assert_zoekt_webserver_command(text, compose_name="synthetic")
        argv = parse_command_argv(blob)
        self.assertEqual(
            [t for t in argv if t in ZOEKT_COMMAND_TOKENS],
            list(ZOEKT_COMMAND_TOKENS),
        )

    def test_ut_z15_flag_order_scrambled_rejected(self) -> None:
        text = _compose_with_zoekt(
            command_line=(
                'command: ["-rpc", "-index", "/data/index", "zoekt-webserver"]'
            )
        )
        with self.assertRaises(AssertionError) as ctx:
            assert_zoekt_webserver_command(text, compose_name="synthetic")
        self.assertIn("ordem lógica", str(ctx.exception))

    def test_ut_z16_rpc_flag_missing_rejected(self) -> None:
        text = _compose_with_zoekt(
            command_line=(
                'command: ["zoekt-webserver", "-index", "/data/index"]'
            )
        )
        with self.assertRaises(AssertionError) as ctx:
            assert_zoekt_webserver_command(text, compose_name="synthetic")
        self.assertIn("-rpc", str(ctx.exception))

    def test_ut_z17_different_index_path_rejected(self) -> None:
        text = (
            "services:\n"
            "  zoekt:\n"
            "    image: sourcegraph/zoekt:latest\n"
            '    command: ["zoekt-webserver", "-index", "/tmp/index", "-rpc"]\n'
            "    volumes:\n"
            "      - zoekt_index:/data/index\n"
            "  app:\n"
            "    image: example\n"
        )
        with self.assertRaises(AssertionError) as ctx:
            assert_zoekt_webserver_command(text, compose_name="synthetic")
        self.assertIn("/data/index", str(ctx.exception))

    def test_ut_z18_empty_compose_and_missing_service(self) -> None:
        with self.assertRaises(AssertionError) as ctx:
            service_block("", "zoekt")
        self.assertIn("vazio", str(ctx.exception).lower())

        with self.assertRaises(AssertionError) as ctx2:
            service_block("services:\n  app:\n    image: x\n", "zoekt")
        self.assertIn("ausente", str(ctx2.exception))

    def test_ut_z19_empty_command_list_rejected(self) -> None:
        text = _compose_with_zoekt(command_line="command: []")
        with self.assertRaises(AssertionError) as ctx:
            assert_zoekt_webserver_command(text, compose_name="synthetic")
        self.assertRegex(
            str(ctx.exception).lower(),
            r"vazio|zoekt-webserver|sem `command`",
        )

    def test_ut_z20_docs_yml_mention_alone_not_enough(self) -> None:
        weak = (
            "# Setup\n"
            "Use docker-compose.e2e.yml with podman compose up.\n"
        )
        with self.assertRaises(AssertionError) as ctx:
            assert_compose_provider_prereq_docs(weak, doc_name="weak.md")
        self.assertIn("podman-compose", str(ctx.exception))

    def test_ut_z21_docs_empty_rejected(self) -> None:
        with self.assertRaises(AssertionError) as ctx:
            assert_compose_provider_prereq_docs("   \n", doc_name="empty.md")
        self.assertIn("vazio", str(ctx.exception).lower())

    def test_ut_z22_canonical_happy_synthetic(self) -> None:
        text = _compose_with_zoekt()
        blob = assert_zoekt_webserver_command(text, compose_name="synthetic")
        argv = parse_command_argv(blob)
        self.assertEqual(argv[:4], list(ZOEKT_COMMAND_TOKENS))


if __name__ == "__main__":
    unittest.main()
