from datetime import datetime
from typing import List
import csv
import hashlib
import os


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
        if os.path.exists(logFilePath):
            self._load_entries_from_file()
    
    def _load_entries_from_file(self) -> None:
        """Load existing entries from the CSV file."""
        with open(self.logFilePath, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                entryId = int(row[0])
                timeStamp = datetime.fromisoformat(row[1])
                eventType = row[2]
                previousChecksum = row[3]
                checksum = row[4]
                entry = AuditLogEntry(entryId, eventType, previousChecksum, checksum)
                entry.timeStamp = timeStamp
                self.entries.append(entry)
    
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
        """Write a single entry to the log file in CSV format."""
        with open(self.logFilePath, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                entry.entryId,
                entry.timeStamp.isoformat(),
                entry.eventType,
                entry.previousChecksum,
                entry.checksum
            ])
    
    def computeChecksum(self, event: str) -> str:
        """Compute a checksum for audit integrity based on event and previous checksum using SHA256."""
        previousChecksum = self.entries[-1].checksum if self.entries else "INIT"
        data = (previousChecksum + event).encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    def rollback(self) -> None:
        """Rollback to a previous state by removing the last entry and rewriting the log file."""
        if self.entries:
            self.entries.pop()
            # Rewrite the entire file to maintain integrity
            with open(self.logFilePath, 'w', newline='') as f:
                writer = csv.writer(f)
                for entry in self.entries:
                    writer.writerow([
                        entry.entryId,
                        entry.timeStamp.isoformat(),
                        entry.eventType,
                        entry.previousChecksum,
                        entry.checksum
                    ])
    
    def validateIntegrity(self) -> bool:
        """Validate the integrity of the audit trail by checking all checksums."""
        for i, entry in enumerate(self.entries):
            expected_previous = "INIT" if i == 0 else self.entries[i - 1].checksum
            if entry.previousChecksum != expected_previous:
                return False
            # Recompute checksum
            data = (entry.previousChecksum + entry.eventType).encode('utf-8')
            expected_checksum = hashlib.sha256(data).hexdigest()
            if entry.checksum != expected_checksum:
                return False
        return True
