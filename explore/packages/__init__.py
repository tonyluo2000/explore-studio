"""Public Explorer Package validation and local loading API."""

from explore.packages.contribution_models import (
    LoadedCharacter,
    LoadedContribution,
    LoadedExplorerPackage,
    LoadedWorldObject,
    PackageAssetReference,
    PackageLoadIssue,
    PackageLoadIssueCode,
    PackageLoadResult,
    PackageProvenance,
)
from explore.packages.loader import load_explorer_package
from explore.packages.models import (
    AssetDeclaration,
    Compatibility,
    ContributionDeclaration,
    ExplorerPackageManifest,
    IssueCode,
    PackageMetadata,
    ValidationIssue,
    ValidationReport,
)
from explore.packages.policy import (
    DISPLAY_NAME_MAX_LENGTH,
    IDENTIFIER_MAX_LENGTH,
    MAX_ASSET_SIZE_BYTES,
    SUPPORTED_SCHEMA_VERSION,
    SUPPORTED_STUDENT_API_VERSION,
)
from explore.packages.registration_adapter import (
    build_student_api_registration_plan,
    plan_loaded_explorer_package,
)
from explore.packages.registration_models import (
    CharacterRegistration,
    CharacterRegistrationSpec,
    RegistrationPlanIssue,
    RegistrationPlanIssueCode,
    RegistrationPlanResult,
    StudentAPIRegistrationEntry,
    StudentAPIRegistrationPlan,
    WorldObjectRegistration,
    WorldObjectRegistrationSpec,
)
from explore.packages.validator import validate_explorer_package

__all__ = [
    "AssetDeclaration",
    "Compatibility",
    "CharacterRegistration",
    "CharacterRegistrationSpec",
    "ContributionDeclaration",
    "DISPLAY_NAME_MAX_LENGTH",
    "ExplorerPackageManifest",
    "IDENTIFIER_MAX_LENGTH",
    "IssueCode",
    "LoadedCharacter",
    "LoadedContribution",
    "LoadedExplorerPackage",
    "LoadedWorldObject",
    "MAX_ASSET_SIZE_BYTES",
    "PackageAssetReference",
    "PackageLoadIssue",
    "PackageLoadIssueCode",
    "PackageLoadResult",
    "PackageMetadata",
    "PackageProvenance",
    "RegistrationPlanIssue",
    "RegistrationPlanIssueCode",
    "RegistrationPlanResult",
    "SUPPORTED_SCHEMA_VERSION",
    "SUPPORTED_STUDENT_API_VERSION",
    "StudentAPIRegistrationEntry",
    "StudentAPIRegistrationPlan",
    "ValidationIssue",
    "ValidationReport",
    "WorldObjectRegistration",
    "WorldObjectRegistrationSpec",
    "build_student_api_registration_plan",
    "load_explorer_package",
    "plan_loaded_explorer_package",
    "validate_explorer_package",
]
