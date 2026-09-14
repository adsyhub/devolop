"""Error types shared by the EJU pipeline."""


class EjuBankError(Exception):
    """Base error for user-correctable pipeline failures."""


class ContractError(EjuBankError):
    """Raised when an input JSON contract is invalid."""


class QualityGateError(EjuBankError):
    """Raised when fail-closed validation blocks an operation."""


class RightsError(EjuBankError):
    """Raised when a requested publication channel is not licensed."""


class SessionError(EjuBankError):
    """Raised for invalid practice-session state changes."""


class SecurityError(EjuBankError):
    """Raised when a security boundary is violated (e.g. host/origin/token)."""


class MigrationError(EjuBankError):
    """Raised when database schema migration fails."""


class MediaError(EjuBankError):
    """Raised when asset or media validation/streaming fails."""


class DoctorError(EjuBankError):
    """Raised when environment or doctor verification fails."""
