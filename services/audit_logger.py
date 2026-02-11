from datetime import datetime
from typing import List


class AuditLogEntry:
    entryId: int
    timeStamp: datetime
    eventType: str
    previousChecksum: str
    checksum: str
    
    def __init__(self, entryId: int, eventType: str, previousChecksum: str, checksum: str) -> None:
        self.entryId = entryId
        self.timeStamp = datetime.now()
        self.eventType = eventType
        self.previousChecksum = previousChecksum
        self.checksum = checksum


class AuditLogger:
    logFilePath: str
    entries: List[AuditLogEntry]
    
    def __init__(self, logFilePath: str) -> None:
        self.logFilePath = logFilePath
        self.entries = []
    
    def logEvent(self, event: str) -> None:
        """Create and log a new audit entry."""
        previousChecksum = self.entries[-1].checksum if self.entries else "INIT"
        currentChecksum = self.computeChecksum(event)
        
        # Create new entry
        entry = AuditLogEntry(
            entryId=len(self.entries) + 1,
            eventType=event,
            previousChecksum=previousChecksum,
            checksum=currentChecksum
        )
        
        self.entries.append(entry)
        self.writeEntry(entry)
    
    def writeEntry(self, entry: AuditLogEntry) -> None:
        """Write a single entry to the log file."""
        #TODO: Implement file write logic (CSV or JSON format)
        pass
    
    def computeChecksum(self, event: str) -> str:
        """Compute a checksum for audit integrity based on event and previous checksum."""
        previousChecksum = self.entries[-1].checksum if self.entries else "INIT"
        # TODO: Implement proper checksum logic (SHA256 of event + previousChecksum)
        return f"CHECKSUM_{len(self.entries) + 1}"
    
    def rollback(self) -> None:
        """Rollback to a previous state using audit trail."""
        #TODO: Implement rollback logic using entries
        pass
    
    def validateIntegrity(self) -> bool:
        """Validate the integrity of the audit trail by checking all checksums."""
        for i, entry in enumerate(self.entries):
            if i == 0:
                if entry.previousChecksum != "INIT":
                    return False
            else:
                if entry.previousChecksum != self.entries[i - 1].checksum:
                    return False
        return True
