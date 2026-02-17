import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.audit_logger import AuditLogger


def test_audit_logger_log_and_integrity(tmp_path):
    logfile = tmp_path / "audit.csv"
    al = AuditLogger(str(logfile))

    al.logEvent("EVENT_ONE")
    al.logEvent("EVENT_TWO")

    assert len(al.entries) == 2
    # Check file written
    assert os.path.exists(str(logfile))

    # Validate integrity
    assert al.validateIntegrity() is True

    # Compute checksum consistency
    checksum1 = al.entries[0].checksum
    recomputed = al.computeChecksum("EVENT_TWO")
    # computeChecksum uses previousChecksum from entries; after two events, previous for new event would be last checksum
    assert isinstance(checksum1, str) and len(checksum1) == 64


def test_rollback_removes_last_entry(tmp_path):
    logfile = tmp_path / "audit2.csv"
    al = AuditLogger(str(logfile))

    al.logEvent("A")
    al.logEvent("B")
    al.logEvent("C")
    assert len(al.entries) == 3

    al.rollback()
    assert len(al.entries) == 2
    # File should be rewritten and still valid
    assert al.validateIntegrity() is True
