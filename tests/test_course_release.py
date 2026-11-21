"""Regression: published S09 + valid older production runtime must block class."""

from __future__ import annotations

import copy
import io
import json
import zipfile
from pathlib import Path

import pytest

from scripts import course_release as release
from scripts import prepare_course_kit_publication as publication
from scripts import verify_live_course_release as live
from scripts.course_release_acceptance import accept


@pytest.fixture(scope="module")
def contract():
    return release.load_contract()


@pytest.fixture(scope="module")
def candidate(tmp_path_factory, contract):
    path = tmp_path_factory.mktemp("release") / "candidate.zip"
    release.rebuild_from_commit(contract["materials_provenance"], release.ROOT, path)
    return path


def changed_zip(candidate, tmp_path, *, edit=None, extra=None, duplicate=False):
    path = tmp_path / "modified.zip"
    with zipfile.ZipFile(candidate) as source, zipfile.ZipFile(path, "w") as target:
        for name in source.namelist():
            data = source.read(name)
            if edit and name == release.MATERIALS:
                record = json.loads(data)
                record.update(edit)
                data = json.dumps(record).encode()
            target.writestr(name, data)
        if extra:
            target.writestr(extra, "unapproved")
        if duplicate:
            target.writestr(release.MATERIALS, source.read(release.MATERIALS))
    return path


def test_matching_approved_runtime_and_bytes_pass(candidate, contract):
    assert (
        release.verify_artifact(candidate, contract)["expected_runtime_pin"]
        == contract["expected_runtime_pin"]
    )


def test_s09_old_structurally_valid_production_kit_fails(contract):
    # Immutable regression fixture, independent of whether publication later merges.
    import subprocess

    payload = subprocess.check_output(
        ["git", "show", f"c01e718:{release.PUBLIC}"], cwd=release.ROOT
    )
    with pytest.raises(release.ReleaseError, match="PRODUCTION_COURSE_KIT_STALE") as error:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.zip"
            path.write_bytes(payload)
            release.verify_artifact(path, contract)
    message = str(error.value)
    for text in (
        "S09",
        "d1e89a1d",
        contract["expected_runtime_pin"],
        "Required action:",
        "publication PR",
    ):
        assert text in message


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_course_kit_sha256", "0" * 64),
        ("expected_runtime_pin", "0" * 40),
        ("materials_provenance", "0" * 40),
        ("expected_course_kit_members", 999),
    ],
)
def test_wrong_candidate_metadata_fails(candidate, contract, field, value):
    wrong = dict(contract, **{field: value})
    with pytest.raises(release.ReleaseError, match=field):
        release.verify_artifact(candidate, wrong)


def test_unexpected_member_even_with_correct_count_fails(candidate, contract, tmp_path):
    path = changed_zip(candidate, tmp_path, extra=f"{release.ZIP_ROOT}/unexpected.txt")
    wrong = dict(contract, expected_course_kit_members=contract["expected_course_kit_members"] + 1)
    with pytest.raises(release.ReleaseError, match="member_names"):
        release.verify_artifact(path, wrong)


@pytest.mark.parametrize(
    "member",
    [
        "../escape",
        "other/file",
        f"{release.ZIP_ROOT}/my-explore-world/mine.py",
        f"{release.ZIP_ROOT}/engine/private.py",
        f"{release.ZIP_ROOT}/.env",
    ],
)
def test_unsafe_member_refused(candidate, tmp_path, member):
    with pytest.raises(ValueError):
        release.inspect_zip(changed_zip(candidate, tmp_path, extra=member))


def test_duplicate_member_fails(candidate, tmp_path):
    with (
        pytest.warns(UserWarning, match="Duplicate"),
        pytest.raises(release.ReleaseError, match="DUPLICATE_ZIP_MEMBER"),
    ):
        release.inspect_zip(changed_zip(candidate, tmp_path, duplicate=True))


def test_requirements_and_embedded_runtime_must_agree(candidate, tmp_path):
    with pytest.raises(release.ReleaseError, match="RUNTIME_PIN_MISMATCH"):
        release.inspect_zip(
            changed_zip(candidate, tmp_path, edit={"course_platform_commit": "0" * 40})
        )


@pytest.mark.parametrize("files", [[], [str(release.PUBLIC), "README.md"], ["README.md"]])
def test_publication_diff_unrelated_files_fail(files):
    with pytest.raises(release.ReleaseError, match="UNRELATED_PUBLICATION_DIFF"):
        release.publication_diff(files)


def test_publication_diff_exact_zip_passes():
    release.publication_diff([str(release.PUBLIC)])


def test_deterministic_double_build_mismatch_fails(candidate, tmp_path):
    wrong = tmp_path / "wrong.zip"
    wrong.write_bytes(candidate.read_bytes() + b"different")
    with pytest.raises(release.ReleaseError, match="NONDETERMINISTIC"):
        release.compare_builds(candidate, wrong)
    release.compare_builds(candidate, candidate)


def response(payload, status=200):
    class Response(io.BytesIO):
        headers = {"Cache-Control": "public, max-age=0"}

    result = Response(payload)
    result.status = status
    return result


def test_live_correct_sha_cache_busting_and_no_classroom_claim(candidate, contract, monkeypatch):
    monkeypatch.setattr(live, "published_head", lambda *a: "a" * 40)

    def opener(request, timeout):
        assert "?course_release=" in request.full_url and "&t=" in request.full_url
        assert request.get_header("Cache-control") == "no-cache"
        assert timeout > 0
        return response(candidate.read_bytes())

    receipt = live.verify_live(contract, opener=opener)
    assert receipt["release_state"] == "LIVE_VERIFIED"
    assert receipt["classroom_readiness"] == "BLOCKED"


def test_live_stale_sha_fails(candidate, contract):
    wrong = dict(contract, expected_course_kit_sha256="0" * 64)
    with pytest.raises(release.ReleaseError, match="LIVE_COURSE_KIT_STALE"):
        live.verify_live(wrong, opener=lambda *a, **kw: response(candidate.read_bytes()))


def test_live_http_failure(contract):
    with pytest.raises(release.ReleaseError, match="LIVE_HTTP_ERROR"):
        live.verify_live(contract, opener=lambda *a, **kw: response(b"", status=503))


def test_implementation_phase_allows_explicit_lag_but_main_and_publication_fail(
    monkeypatch, contract, tmp_path
):
    monkeypatch.setattr(release, "validate_candidate", lambda *a: None)
    monkeypatch.setattr(
        release,
        "verify_artifact",
        lambda *a, **kw: (_ for _ in ()).throw(release.ReleaseError("PRODUCTION_COURSE_KIT_STALE")),
    )
    assert "BLOCKED" in release.check_phase(
        contract, "implementation", ["engine/changed.py"], tmp_path
    )
    for phase, files in (("main", []), ("publication", [str(release.PUBLIC)])):
        with pytest.raises(release.ReleaseError, match="PRODUCTION_COURSE_KIT_STALE"):
            release.check_phase(contract, phase, files, tmp_path)


def test_implementation_requires_valid_candidate(monkeypatch, contract):
    def fail(*args):
        raise release.ReleaseError("invalid candidate evidence")

    monkeypatch.setattr(release, "validate_candidate", fail)
    with pytest.raises(release.ReleaseError, match="invalid candidate"):
        release.check_phase(contract, "implementation", [])


def test_implementation_cannot_mix_publication(contract):
    with pytest.raises(release.ReleaseError, match="MIXED_PUBLICATION_PHASE"):
        release.check_phase(contract, "implementation", [str(release.PUBLIC), "engine/changed.py"])


def test_contract_rebuilt_from_immutable_source_matches_current_materials(contract):
    release.validate_candidate(contract)


def test_publication_refuses_wrong_arguments_before_writing(monkeypatch, contract, tmp_path):
    monkeypatch.setattr(publication, "clean_source", lambda *a: None)
    monkeypatch.setattr(publication, "load_contract", lambda *a: contract)
    for sha, pin, message in (
        ("0" * 64, contract["expected_runtime_pin"], "WRONG_CANDIDATE_SHA"),
        (contract["expected_course_kit_sha256"], "0" * 40, "WRONG_RUNTIME_PIN"),
    ):
        with pytest.raises(release.ReleaseError, match=message):
            publication.publish(tmp_path / "absent.zip", sha, pin, tmp_path)
    assert not (tmp_path / release.PUBLIC).exists()


def test_dirty_source_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(release, "git", lambda *a: "?? unrelated.py")
    with pytest.raises(release.ReleaseError, match="DIRTY_SOURCE"):
        release.clean_source(tmp_path)


def test_isolated_install_preserves_student_workspace(candidate, monkeypatch, tmp_path):
    home = tmp_path / "real-home"
    student = home / "my-explore-world"
    student.mkdir(parents=True)
    sentinel = student / "mine.py"
    sentinel.write_text("my work")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PYTHONPATH", str(release.ROOT))
    monkeypatch.setattr(live.venv, "create", lambda *a, **kw: None)
    calls = []

    def run(args, **options):
        assert Path(options["env"]["HOME"]) != home
        assert Path(options["cwd"]) == Path(options["env"]["HOME"]) / release.ZIP_ROOT
        assert Path(args[0]).parent.parent == Path(options["cwd"]) / ".venv"
        assert "PYTHONPATH" not in options["env"]
        assert student not in Path(options["cwd"]).parents
        calls.append(args)

    monkeypatch.setattr(live.subprocess, "run", run)
    assert live.fresh_install(candidate)["fresh_install"] == "passed"
    assert len(calls) == 3
    assert sentinel.read_text() == "my work"
    assert list(student.iterdir()) == [sentinel]
    assert not (home / "explore-studio-course").exists()


@pytest.mark.parametrize("session", ["S06", "S07", "S08", "S09"])
def test_deterministic_lesson_acceptance_from_candidate(candidate, tmp_path, session):
    with zipfile.ZipFile(candidate) as archive:
        archive.extractall(tmp_path)
    assert accept(tmp_path / release.ZIP_ROOT, session)["acceptance"] == "passed"


def test_contract_does_not_accept_a_state_claim(contract, tmp_path):
    c = copy.deepcopy(contract)
    c["release_state"] = "CLASSROOM_VERIFIED"
    p = tmp_path / release.CONTRACT
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(c))
    with pytest.raises(release.ReleaseError, match="INVALID_RELEASE_CONTRACT"):
        release.load_contract(tmp_path)


def test_publication_pr_reports_candidate_until_owner_merge(monkeypatch, contract):
    monkeypatch.setattr(release, "validate_candidate", lambda *a: None)
    monkeypatch.setattr(release, "verify_artifact", lambda *a: {})
    text = release.check_phase(contract, "publication", [str(release.PUBLIC)])
    assert "awaiting owner merge" in text
    assert "COURSE KIT PUBLISHED" not in text


def test_matching_live_bytes_cannot_certify_unmerged_publication(candidate, contract, monkeypatch):
    monkeypatch.setattr(live, "published_head", lambda *a: None)
    result = live.verify_live(contract, opener=lambda *a, **kw: response(candidate.read_bytes()))
    assert result["release_state"] == "BUILDING"
    assert result["classroom_readiness"] == "BLOCKED"
    monkeypatch.setattr(live, "fresh_install", lambda *a: {"fresh_install": "passed"})
    with pytest.raises(release.ReleaseError, match="PUBLICATION_NOT_MERGED"):
        live.verify_live(
            contract, install=True, opener=lambda *a, **kw: response(candidate.read_bytes())
        )


def test_changed_task_card_canonical_command_requires_new_acceptance(candidate, tmp_path):
    with zipfile.ZipFile(candidate) as archive:
        archive.extractall(tmp_path)
    root = tmp_path / release.ZIP_ROOT
    card = root / "lessons/sessions/s09/student/task-card.md"
    card.write_text(card.read_text().replace("count-object-interactions", "different-mission"))
    with pytest.raises(RuntimeError, match="canonical command changed"):
        accept(root, "S09")


def test_publication_refuses_behind_main_before_replacing(
    candidate, contract, monkeypatch, tmp_path
):
    monkeypatch.setattr(publication, "clean_source", lambda *a: None)
    monkeypatch.setattr(publication, "load_contract", lambda *a: contract)
    monkeypatch.setattr(publication, "validate_candidate", lambda *a: None)
    monkeypatch.setattr(
        publication, "git", lambda root, *args: "a" * 40 if args[-1] == "HEAD" else "b" * 40
    )
    target = tmp_path / release.PUBLIC
    target.parent.mkdir(parents=True)
    target.write_bytes(b"previous kit")
    with pytest.raises(release.ReleaseError, match="STALE_PUBLICATION_BASE"):
        publication.publish(
            candidate,
            contract["expected_course_kit_sha256"],
            contract["expected_runtime_pin"],
            tmp_path,
        )
    assert target.read_bytes() == b"previous kit"


def test_main_cannot_certify_hand_advanced_state(contract, candidate, monkeypatch, tmp_path):
    target = tmp_path / release.PUBLIC
    target.parent.mkdir(parents=True)
    target.write_bytes(candidate.read_bytes())
    wrong = dict(contract, expected_runtime_pin="0" * 40)
    monkeypatch.setattr(release, "validate_candidate", lambda *a: None)
    with pytest.raises(release.ReleaseError, match="PRODUCTION_COURSE_KIT_STALE"):
        release.check_phase(wrong, "main", [], tmp_path)
