"""Adversarial tests for bounded Phase E package submission."""

from __future__ import annotations

import hashlib
import inspect
import json
import shutil
import sqlite3
import stat
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from threading import Barrier

import pytest

from explore.online import (
    Actor,
    AssuranceLevel,
    AuditEvent,
    AuthenticatedOIDCIdentity,
    Cohort,
    CohortMembership,
    CohortRole,
    IdentityProvider,
    NamespaceGrant,
    NamespacePermission,
    PackageNamespace,
    PackageSubmissionService,
    PrincipalKind,
    PublicationAcknowledgment,
    PublicationAuthority,
    PublicationPolicy,
    SQLiteSubmissionStore,
    SubmissionAccessDeniedError,
    SubmissionAuthenticationError,
    SubmissionConflictError,
    SubmissionPolicyError,
    SubmissionState,
    SubmissionValidationError,
    SubmissionValidationOutcome,
    SubmissionVerificationIssueCode,
    verify_submitted_archive,
)
from explore.packages import export_explorer_package
from explore.packages.explorer_package_export_models import EXPLORER_PACKAGE_EXPORT_FILE_MODE

NOW = datetime(2026, 9, 5, 14, 0, tzinfo=UTC)
CREATED = datetime(2026, 9, 1, 14, 0, tzinfo=UTC)
CLOSES = datetime(2027, 6, 30, 23, 59, tzinfo=UTC)
ISSUER = "https://identity.example.edu"
COHORT_ID = "fall-explorers"
PACKAGE_ID = "nova-character"
ACTOR_IDS = {
    "student": "00000000-0000-4000-8000-000000000001",
    "other-student": "00000000-0000-4000-8000-000000000004",
    "course-admin": "00000000-0000-4000-8000-000000000003",
}
SUBJECTS = {
    "student": "provider-student-101",
    "other-student": "provider-student-202",
    "course-admin": "provider-admin-1",
}
POLICY = PublicationPolicy("terms-2026-09", "course-license-policy-2026-09")
ACKNOWLEDGMENT = PublicationAcknowledgment(
    POLICY.terms_version,
    POLICY.license_policy_version,
    PublicationAuthority.SELF,
)
PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "explorer-packages" / PACKAGE_ID


def _identity(name: str = "student") -> AuthenticatedOIDCIdentity:
    return AuthenticatedOIDCIdentity(ISSUER, SUBJECTS[name], AssuranceLevel.AAL1)


def _membership(name: str, *, active: bool = True) -> CohortMembership:
    return CohortMembership(
        cohort_id=COHORT_ID,
        actor_id=ACTOR_IDS[name],
        role=CohortRole.STUDENT,
        granted_by_actor_id=ACTOR_IDS["course-admin"],
        granted_at=CREATED,
        active=active,
    )


def _open_seeded_store(path: Path) -> SQLiteSubmissionStore:
    store = SQLiteSubmissionStore.open(path)
    store.initialize_schema()
    store.approve_identity_provider(IdentityProvider(ISSUER))
    for name, actor_id in ACTOR_IDS.items():
        store.bind_federated_actor(
            issuer=ISSUER,
            subject=SUBJECTS[name],
            proposed_actor=Actor(actor_id, CREATED),
        )
    admin = CohortMembership(
        cohort_id=COHORT_ID,
        actor_id=ACTOR_IDS["course-admin"],
        role=CohortRole.COURSE_ADMIN,
        granted_by_actor_id=ACTOR_IDS["course-admin"],
        granted_at=CREATED,
    )
    store.create_cohort(Cohort(COHORT_ID, "Example Academy", CREATED, CLOSES), admin)
    store.grant_membership(_membership("student"))
    store.grant_membership(_membership("other-student"))
    store.create_namespace(PackageNamespace(PACKAGE_ID, COHORT_ID, ACTOR_IDS["student"], CREATED))
    return store


@pytest.fixture
def store(tmp_path: Path) -> SQLiteSubmissionStore:
    value = _open_seeded_store(tmp_path / "online.sqlite3")
    yield value
    value.close()


@pytest.fixture
def archive(tmp_path: Path) -> bytes:
    destination = tmp_path / "nova-character-1.0.0.explorer-package.zip"
    result = export_explorer_package(EXAMPLE_ROOT.resolve(), destination.resolve())
    assert result.is_exported
    return destination.read_bytes()


def _service(store: SQLiteSubmissionStore, *, clock=lambda: NOW) -> PackageSubmissionService:
    return PackageSubmissionService(store, POLICY, clock=clock)


def _submit(
    store: SQLiteSubmissionStore,
    archive: bytes,
    *,
    identity: AuthenticatedOIDCIdentity | None = None,
    key: str = "submit-nova-v1",
    acknowledgment: PublicationAcknowledgment = ACKNOWLEDGMENT,
):
    return _service(store).submit(
        identity=identity or _identity(),
        filename="nova-character-1.0.0.explorer-package.zip",
        archive_bytes=archive,
        idempotency_key=key,
        acknowledgment=acknowledgment,
    )


def _canonical_zip(members: list[tuple[str, bytes]]) -> bytes:
    target = BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as value:
        for name, content in members:
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | EXPLORER_PACKAGE_EXPORT_FILE_MODE) << 16
            info.internal_attr = 0
            info.extra = b""
            info.comment = b""
            value.writestr(info, content)
    return target.getvalue()


def _members(archive: bytes) -> list[tuple[str, bytes]]:
    with zipfile.ZipFile(BytesIO(archive), "r") as value:
        return [(item.filename, value.read(item)) for item in value.infolist()]


def _different_valid_archive(tmp_path: Path) -> bytes:
    source = tmp_path / "changed-package"
    shutil.copytree(EXAMPLE_ROOT, source)
    contribution = source / "character" / "nova.yaml"
    contribution.write_text(
        contribution.read_text(encoding="utf-8").replace("x: 430", "x: 431"),
        encoding="utf-8",
    )
    destination = tmp_path / "changed-dist" / "nova-character-1.0.0.explorer-package.zip"
    destination.parent.mkdir()
    result = export_explorer_package(source.resolve(), destination.resolve())
    assert result.is_exported
    return destination.read_bytes()


def test_valid_archive_identity_and_member_provenance_are_server_derived(archive: bytes) -> None:
    verification = verify_submitted_archive("nova-character-1.0.0.explorer-package.zip", archive)

    assert verification.is_valid
    assert verification.archive is not None
    assert verification.archive.package_id == PACKAGE_ID
    assert verification.archive.semantic_version == "1.0.0"
    assert verification.archive.raw_archive_sha256 == hashlib.sha256(archive).hexdigest()
    assert tuple(member.relative_path for member in verification.archive.members) == (
        "manifest.yaml",
        "character/nova.yaml",
    )


@pytest.mark.parametrize(
    ("filename", "payload", "code"),
    [
        ("nova.zip", b"not-a-zip", SubmissionVerificationIssueCode.FILENAME_INVALID),
        (
            "nova-character-1.0.0.explorer-package.zip",
            b"",
            SubmissionVerificationIssueCode.ARCHIVE_REQUIRED,
        ),
        (
            "nova-character-1.0.0.explorer-package.zip",
            b"not-a-zip",
            SubmissionVerificationIssueCode.ARCHIVE_INVALID,
        ),
    ],
)
def test_non_package_inputs_fail_closed(
    filename: str,
    payload: bytes,
    code: SubmissionVerificationIssueCode,
) -> None:
    result = verify_submitted_archive(filename, payload)

    assert not result.is_valid
    assert result.archive is None
    assert result.issues[0].code is code


def test_archive_size_limit_is_enforced_before_zip_parsing(
    archive: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from explore.online import submission_verification as module

    monkeypatch.setattr(module, "MAX_EXPLORER_PACKAGE_EXPORT_ARCHIVE_BYTES", len(archive) - 1)

    result = verify_submitted_archive("nova-character-1.0.0.explorer-package.zip", archive)

    assert result.issues[0].code is SubmissionVerificationIssueCode.ARCHIVE_TOO_LARGE


def test_archive_must_have_exact_declared_members_in_order(archive: bytes) -> None:
    members = _members(archive)
    extra = _canonical_zip([*members, ("undeclared.txt", b"hidden")])
    reversed_archive = _canonical_zip(list(reversed(members)))

    extra_result = verify_submitted_archive("nova-character-1.0.0.explorer-package.zip", extra)
    reversed_result = verify_submitted_archive(
        "nova-character-1.0.0.explorer-package.zip", reversed_archive
    )

    assert extra_result.issues[0].code is SubmissionVerificationIssueCode.ARCHIVE_STRUCTURE_INVALID
    assert (
        reversed_result.issues[0].code is SubmissionVerificationIssueCode.ARCHIVE_STRUCTURE_INVALID
    )


def test_semantically_equivalent_but_nondeterministic_zip_is_rejected(archive: bytes) -> None:
    target = BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as value:
        for name, content in _members(archive):
            value.writestr(name, content)

    result = verify_submitted_archive(
        "nova-character-1.0.0.explorer-package.zip", target.getvalue()
    )

    assert result.issues[0].code is SubmissionVerificationIssueCode.ARCHIVE_NOT_DETERMINISTIC


def test_manifest_declared_traversal_is_rejected_without_extraction(archive: bytes) -> None:
    members = _members(archive)
    manifest = members[0][1].replace(b"character/nova.yaml", b"../outside.yaml")
    malicious = _canonical_zip([("manifest.yaml", manifest), ("../outside.yaml", members[1][1])])

    result = verify_submitted_archive("nova-character-1.0.0.explorer-package.zip", malicious)

    assert result.issues[0].code is SubmissionVerificationIssueCode.PACKAGE_CONTENT_INVALID


def test_yaml_anchors_and_aliases_are_rejected_at_online_ingest(archive: bytes) -> None:
    members = _members(archive)
    anchored = members[1][1].replace(b'name: "Nova"', b'name: &student_name "Nova"')
    adversarial = _canonical_zip([members[0], (members[1][0], anchored)])

    result = verify_submitted_archive("nova-character-1.0.0.explorer-package.zip", adversarial)

    assert result.issues[0].code is SubmissionVerificationIssueCode.PACKAGE_CONTENT_INVALID


def test_declarative_python_looking_text_remains_inert(tmp_path: Path) -> None:
    marker = tmp_path / "executed"
    root = tmp_path / "package"
    shutil.copytree(
        PROJECT_ROOT / "examples" / "explorer-packages" / "crystal-lantern",
        root,
    )
    contribution = root / "objects" / "lantern.yaml"
    contribution.write_text(
        contribution.read_text(encoding="utf-8")
        + f'\nwhen_interacted: \'__import__("pathlib").Path("{marker}").touch()\'\n',
        encoding="utf-8",
    )
    destination = tmp_path / "crystal-lantern-0.1.0.explorer-package.zip"
    exported = export_explorer_package(root.resolve(), destination.resolve())
    assert exported.is_exported

    result = verify_submitted_archive(destination.name, destination.read_bytes())

    assert result.is_valid
    assert not marker.exists()


def test_success_persists_reviewable_submission_version_artifact_audit_and_acknowledgment(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    receipt = _submit(store, archive)
    submission = receipt.submission

    assert not receipt.replayed
    assert submission.state is SubmissionState.REVIEWABLE
    assert submission.validation_outcome is SubmissionValidationOutcome.VALID
    assert submission.package_version.package_id == PACKAGE_ID
    assert submission.package_version.package_version == "1.0.0"
    assert submission.package_version.raw_zip_sha256 == hashlib.sha256(archive).hexdigest()
    assert submission.acknowledgment == ACKNOWLEDGMENT
    assert submission.artifact_retention_until == CLOSES.replace(year=CLOSES.year + 1)
    assert store.load_submission_artifact(submission.submission_id) == archive
    provenance = json.loads(submission.validation_provenance_json)
    assert provenance["validation_outcome"] == "valid"
    assert provenance["raw_archive_sha256"] == hashlib.sha256(archive).hexdigest()
    audit = store._connection.execute(
        "SELECT object_id, details_json, retention_until FROM audit_events"
    ).fetchone()
    assert audit[0] == submission.submission_id
    assert json.loads(audit[1])["state"] == "reviewable"
    assert datetime.fromisoformat(audit[2].replace("Z", "+00:00")) == CLOSES.replace(
        year=CLOSES.year + 2
    )


def test_submission_api_has_no_client_owner_cohort_role_digest_or_version_claims() -> None:
    parameters = inspect.signature(PackageSubmissionService.submit).parameters

    assert set(parameters) == {
        "self",
        "identity",
        "filename",
        "archive_bytes",
        "idempotency_key",
        "acknowledgment",
    }


def test_unbound_identity_cannot_bootstrap_an_actor(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    unknown = AuthenticatedOIDCIdentity(ISSUER, "unknown-subject", AssuranceLevel.AAL1)

    with pytest.raises(SubmissionAuthenticationError):
        _submit(store, archive, identity=unknown)

    assert store._connection.execute("SELECT count(*) FROM actors").fetchone() == (3,)


def test_bola_guessed_and_cross_actor_namespaces_share_one_denial(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    attacker = _identity("other-student")
    with pytest.raises(SubmissionAccessDeniedError) as existing:
        _submit(store, archive, identity=attacker)

    altered = _members(archive)
    altered[0] = (
        "manifest.yaml",
        altered[0][1].replace(b"nova-character", b"ghost-package"),
    )
    unknown_archive = _canonical_zip(altered)
    with pytest.raises(SubmissionAccessDeniedError) as missing:
        _service(store).submit(
            identity=attacker,
            filename="ghost-package-1.0.0.explorer-package.zip",
            archive_bytes=unknown_archive,
            idempotency_key="guess-unknown",
            acknowledgment=ACKNOWLEDGMENT,
        )

    assert str(existing.value) == str(missing.value) == "submission is not authorized"


def test_same_cohort_explicit_grant_authorizes_submission(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    store.grant_namespace(
        NamespaceGrant(
            PACKAGE_ID,
            COHORT_ID,
            ACTOR_IDS["other-student"],
            NamespacePermission.SUBMIT,
            ACTOR_IDS["course-admin"],
            CREATED,
        )
    )

    receipt = _submit(store, archive, identity=_identity("other-student"))

    assert receipt.submission.submitted_by_actor_id == ACTOR_IDS["other-student"]


def test_inactive_membership_and_closed_cohort_fail_closed(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    store._connection.execute(
        """
        UPDATE cohort_memberships SET active = 0, revision = 2
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["student"]),
    )
    with pytest.raises(SubmissionAccessDeniedError):
        _submit(store, archive)

    store._connection.execute(
        """
        UPDATE cohort_memberships SET active = 1, revision = 3
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["student"]),
    )
    closed = PackageSubmissionService(
        store,
        POLICY,
        clock=lambda: CLOSES,
    )
    with pytest.raises(SubmissionAccessDeniedError):
        closed.submit(
            identity=_identity(),
            filename="nova-character-1.0.0.explorer-package.zip",
            archive_bytes=archive,
            idempotency_key="closed-cohort",
            acknowledgment=ACKNOWLEDGMENT,
        )


def test_policy_versions_are_checked_against_trusted_configuration(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    stale = PublicationAcknowledgment(
        "old-terms",
        POLICY.license_policy_version,
        PublicationAuthority.SELF,
    )

    with pytest.raises(SubmissionPolicyError):
        _submit(store, archive, acknowledgment=stale)


def test_invalid_archive_never_creates_a_reviewable_submission(
    store: SQLiteSubmissionStore,
) -> None:
    with pytest.raises(SubmissionValidationError) as rejected:
        _service(store).submit(
            identity=_identity(),
            filename="nova-character-1.0.0.explorer-package.zip",
            archive_bytes=b"not-a-zip",
            idempotency_key="invalid-archive",
            acknowledgment=ACKNOWLEDGMENT,
        )

    assert not rejected.value.verification.is_valid
    assert store._connection.execute("SELECT count(*) FROM package_submissions").fetchone() == (0,)
    assert store._connection.execute("SELECT count(*) FROM audit_events").fetchone() == (0,)


def test_identical_idempotent_replay_returns_same_opaque_submission(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    first = _submit(store, archive)
    replay = _submit(store, archive)

    assert replay.replayed
    assert replay.submission == first.submission
    assert store._connection.execute("SELECT count(*) FROM package_versions").fetchone() == (1,)
    assert store._connection.execute("SELECT count(*) FROM package_submissions").fetchone() == (1,)
    assert store._connection.execute("SELECT count(*) FROM audit_events").fetchone() == (1,)


def test_idempotency_key_reuse_with_different_bytes_fails_closed(
    store: SQLiteSubmissionStore,
    archive: bytes,
    tmp_path: Path,
) -> None:
    _submit(store, archive)
    changed = _different_valid_archive(tmp_path)

    with pytest.raises(SubmissionConflictError, match="idempotency key"):
        _submit(store, changed)


def test_existing_exact_version_cannot_be_rebound_to_conflicting_bytes(
    store: SQLiteSubmissionStore,
    archive: bytes,
    tmp_path: Path,
) -> None:
    first = _submit(store, archive)
    changed = _different_valid_archive(tmp_path)

    with pytest.raises(SubmissionConflictError):
        _submit(store, changed, key="different-request-key")

    persisted = store.load_package_version(PACKAGE_ID, "1.0.0")
    assert persisted == first.submission.package_version
    assert store._connection.execute("SELECT count(*) FROM package_submissions").fetchone() == (1,)
    assert store._connection.execute("SELECT count(*) FROM audit_events").fetchone() == (1,)


def test_replay_rechecks_current_authorization_and_cannot_restore_privilege(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    _submit(store, archive)
    store._connection.execute(
        """
        UPDATE cohort_memberships SET active = 0, revision = 2
        WHERE cohort_id = ? AND actor_id = ?
        """,
        (COHORT_ID, ACTOR_IDS["student"]),
    )

    with pytest.raises(SubmissionAccessDeniedError):
        _submit(store, archive)


def test_concurrent_identical_submission_creates_one_version_and_submission(
    tmp_path: Path,
    archive: bytes,
) -> None:
    database = tmp_path / "concurrent.sqlite3"
    seeded = _open_seeded_store(database)
    seeded.close()
    barrier = Barrier(2)

    def submit() -> tuple[str, bool]:
        local = SQLiteSubmissionStore.open(database)
        try:
            barrier.wait()
            receipt = _submit(local, archive, key="concurrent-request")
            return receipt.submission.submission_id, receipt.replayed
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: submit(), range(2)))

    check = SQLiteSubmissionStore.open(database)
    try:
        assert len({result[0] for result in results}) == 1
        assert sorted(result[1] for result in results) == [False, True]
        assert check._connection.execute("SELECT count(*) FROM package_versions").fetchone() == (1,)
        assert check._connection.execute("SELECT count(*) FROM package_submissions").fetchone() == (
            1,
        )
        assert check._connection.execute("SELECT count(*) FROM audit_events").fetchone() == (1,)
    finally:
        check.close()


def test_audit_failure_rolls_back_version_submission_artifact_and_idempotency(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    store.append_audit_event(
        AuditEvent(
            event_id="00000000-0000-4000-8000-000000000099",
            occurred_at=NOW,
            retention_until=CLOSES.replace(year=CLOSES.year + 2),
            principal_kind=PrincipalKind.ACTOR,
            principal_id=ACTOR_IDS["student"],
            event_type="package.submitted",
            object_type="test",
            object_id="reserved",
            cohort_id=COHORT_ID,
            idempotency_key="atomic-failure",
            details_json="{}",
        )
    )

    with pytest.raises(sqlite3.IntegrityError):
        _submit(store, archive, key="atomic-failure")

    assert store._connection.execute("SELECT count(*) FROM package_versions").fetchone() == (0,)
    assert store._connection.execute("SELECT count(*) FROM package_submissions").fetchone() == (0,)
    assert store._connection.execute("SELECT count(*) FROM idempotency_records").fetchone() == (0,)


def test_submission_rows_and_artifact_bytes_are_immutable(
    store: SQLiteSubmissionStore,
    archive: bytes,
) -> None:
    receipt = _submit(store, archive)
    submission_id = receipt.submission.submission_id

    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store._connection.execute(
            "UPDATE package_submissions SET state = 'reviewable' WHERE submission_id = ?",
            (submission_id,),
        )
    with pytest.raises(sqlite3.IntegrityError, match="immutable"):
        store._connection.execute(
            "DELETE FROM package_submissions WHERE submission_id = ?",
            (submission_id,),
        )
    assert store.load_submission_artifact(submission_id) == archive


def test_submission_module_does_not_cross_deferred_boundaries() -> None:
    from explore.online import submission as module

    source = inspect.getsource(module).lower()
    forbidden = (
        "flask",
        "fastapi",
        "requests",
        "subprocess",
        "authorizationaction.approve",
        "registry_read",
        "signing",
        "deployment",
        "moderation",
        "exec(",
        "eval(",
    )

    assert all(token not in source for token in forbidden)
