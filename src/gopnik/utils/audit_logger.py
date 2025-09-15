"""
Audit logging system for Gopnik deidentification toolkit.
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from contextlib import contextmanager
import os

from ..models.audit import AuditLog, AuditTrail, AuditOperation, AuditLevel
from .crypto import CryptographicUtils


class AuditLogger:
    """
    Comprehensive audit logging system with structured logging, storage, and cryptographic signing.
    
    Features:
    - Structured audit log creation and management
    - SQLite database storage with indexing
    - Cryptographic signing for integrity
    - Thread-safe operations
    - Automatic log rotation and cleanup
    - Export capabilities (JSON, CSV)
    """
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        enable_signing: bool = True,
        auto_sign: bool = True,
        max_logs_per_file: int = 10000,
        retention_days: int = 365
    ):
        """
        Initialize audit logger.
        
        Args:
            storage_path: Path to store audit logs (default: ./audit_logs)
            enable_signing: Enable cryptographic signing
            auto_sign: Automatically sign logs when created
            max_logs_per_file: Maximum logs per storage file before rotation
            retention_days: Days to retain audit logs
        """
        self.storage_path = storage_path or Path("./audit_logs")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.enable_signing = enable_signing
        self.auto_sign = auto_sign
        self.max_logs_per_file = max_logs_per_file
        self.retention_days = retention_days
        
        # Initialize database
        self.db_path = self.storage_path / "audit_logs.db"
        self._init_database()
        
        # Logger for internal operations (initialize early)
        self.logger = logging.getLogger(__name__)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize crypto utilities
        self.crypto = CryptographicUtils()
        if self.enable_signing:
            self._init_signing_keys()
        
        # Current audit trail
        self.current_trail: Optional[AuditTrail] = None
    
    def _init_database(self) -> None:
        """Initialize SQLite database for audit log storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    operation TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    document_id TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    profile_name TEXT,
                    detections_summary TEXT,
                    input_hash TEXT,
                    output_hash TEXT,
                    file_paths TEXT,
                    processing_time REAL,
                    memory_usage REAL,
                    error_message TEXT,
                    warning_messages TEXT,
                    signature TEXT,
                    details TEXT,
                    system_info TEXT,
                    chain_id TEXT,
                    parent_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operation ON audit_logs(operation)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_document_id ON audit_logs(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON audit_logs(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chain_id ON audit_logs(chain_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_level ON audit_logs(level)")
            
            # Create audit trails table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_trails (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT,
                    log_count INTEGER DEFAULT 0
                )
            """)
            
            conn.commit()
    
    def _init_signing_keys(self) -> None:
        """Initialize cryptographic keys for signing."""
        key_path = self.storage_path / "signing_keys"
        key_path.mkdir(exist_ok=True)
        
        private_key_path = key_path / "private_key.pem"
        public_key_path = key_path / "public_key.pem"
        
        if private_key_path.exists() and public_key_path.exists():
            # Load existing keys
            with open(private_key_path, 'rb') as f:
                private_key_pem = f.read()
            with open(public_key_path, 'rb') as f:
                public_key_pem = f.read()
            
            self.crypto.load_rsa_private_key(private_key_pem)
            self.crypto.load_rsa_public_key(public_key_pem)
            
            self.logger.info("Loaded existing signing keys")
        else:
            # Generate new keys
            private_key_pem, public_key_pem = self.crypto.generate_rsa_key_pair()
            
            with open(private_key_path, 'wb') as f:
                f.write(private_key_pem)
            with open(public_key_path, 'wb') as f:
                f.write(public_key_pem)
            
            # Set secure permissions
            os.chmod(private_key_path, 0o600)
            os.chmod(public_key_path, 0o644)
            
            self.logger.info("Generated new signing keys")
    
    @contextmanager
    def _get_db_connection(self):
        """Get thread-safe database connection."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    def create_audit_trail(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> AuditTrail:
        """
        Create a new audit trail.
        
        Args:
            name: Human-readable name for the trail
            metadata: Additional metadata
            
        Returns:
            Created audit trail
        """
        trail = AuditTrail(
            id=self.crypto.generate_secure_id(),
            name=name,
            metadata=metadata or {}
        )
        
        # Store in database
        with self._get_db_connection() as conn:
            conn.execute("""
                INSERT INTO audit_trails (id, name, created_at, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                trail.id,
                trail.name,
                trail.created_at.isoformat(),
                json.dumps(trail.metadata)
            ))
            conn.commit()
        
        self.current_trail = trail
        self.logger.info(f"Created audit trail: {name} ({trail.id})")
        return trail
    
    def set_current_trail(self, trail_id: str) -> Optional[AuditTrail]:
        """
        Set the current audit trail by ID.
        
        Args:
            trail_id: ID of trail to set as current
            
        Returns:
            Audit trail if found, None otherwise
        """
        trail = self.get_audit_trail(trail_id)
        if trail:
            self.current_trail = trail
            self.logger.info(f"Set current audit trail: {trail.name} ({trail_id})")
        return trail
    
    def log_operation(
        self,
        operation: AuditOperation,
        level: AuditLevel = AuditLevel.INFO,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log an audit operation.
        
        Args:
            operation: Type of operation
            level: Audit level
            document_id: Document ID if applicable
            user_id: User ID if applicable
            session_id: Session ID if applicable
            **kwargs: Additional audit log fields
            
        Returns:
            Created audit log
        """
        audit_log = AuditLog(
            operation=operation,
            timestamp=datetime.now(timezone.utc),
            level=level,
            document_id=document_id,
            user_id=user_id,
            session_id=session_id,
            **kwargs
        )
        
        # Auto-sign if enabled
        if self.auto_sign and self.enable_signing:
            self.sign_audit_log(audit_log)
        
        # Add to current trail if exists (set chain_id before storing)
        if self.current_trail:
            audit_log.chain_id = self.current_trail.id
            self.current_trail.add_log(audit_log)
        
        # Store in database
        self._store_audit_log(audit_log)
        
        # Update trail log count if needed
        if self.current_trail:
            self._update_trail_log_count(self.current_trail.id)
        
        self.logger.debug(f"Logged audit operation: {operation.value} ({audit_log.id})")
        return audit_log
    
    def log_document_operation(
        self,
        operation: AuditOperation,
        document_id: str,
        user_id: Optional[str] = None,
        profile_name: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log a document-related operation.
        
        Args:
            operation: Type of operation
            document_id: Document ID
            user_id: User ID
            profile_name: Redaction profile name
            **kwargs: Additional fields
            
        Returns:
            Created audit log
        """
        return self.log_operation(
            operation=operation,
            document_id=document_id,
            user_id=user_id,
            profile_name=profile_name,
            **kwargs
        )
    
    def log_error(
        self,
        error_message: str,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log an error operation.
        
        Args:
            error_message: Error message
            document_id: Document ID if applicable
            user_id: User ID if applicable
            **kwargs: Additional fields
            
        Returns:
            Created audit log
        """
        return self.log_operation(
            operation=AuditOperation.ERROR_OCCURRED,
            level=AuditLevel.ERROR,
            document_id=document_id,
            user_id=user_id,
            error_message=error_message,
            **kwargs
        )
    
    def log_system_operation(
        self,
        operation: AuditOperation,
        level: AuditLevel = AuditLevel.INFO,
        **kwargs
    ) -> AuditLog:
        """
        Log a system operation.
        
        Args:
            operation: Type of operation
            level: Audit level
            **kwargs: Additional fields
            
        Returns:
            Created audit log
        """
        return self.log_operation(
            operation=operation,
            level=level,
            **kwargs
        )
    
    def sign_audit_log(self, audit_log: AuditLog) -> None:
        """
        Cryptographically sign an audit log.
        
        Args:
            audit_log: Audit log to sign
        """
        if not self.enable_signing:
            self.logger.warning("Signing is disabled")
            return
        
        try:
            content_hash = audit_log.get_content_hash()
            signature = self.crypto.sign_data_rsa(content_hash)
            audit_log.signature = signature
            
            self.logger.debug(f"Signed audit log: {audit_log.id}")
        except Exception as e:
            self.logger.error(f"Failed to sign audit log {audit_log.id}: {e}")
            raise
    
    def verify_audit_log(self, audit_log: AuditLog) -> bool:
        """
        Verify the cryptographic signature of an audit log.
        
        Args:
            audit_log: Audit log to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not audit_log.is_signed():
            return False
        
        if not self.enable_signing:
            self.logger.warning("Signing is disabled, cannot verify")
            return False
        
        try:
            content_hash = audit_log.get_content_hash()
            return self.crypto.verify_signature_rsa(content_hash, audit_log.signature)
        except Exception as e:
            self.logger.error(f"Failed to verify audit log {audit_log.id}: {e}")
            return False
    
    def _store_audit_log(self, audit_log: AuditLog) -> None:
        """Store audit log in database."""
        with self._get_db_connection() as conn:
            conn.execute("""
                INSERT INTO audit_logs (
                    id, operation, timestamp, level, document_id, user_id, session_id,
                    ip_address, user_agent, profile_name, detections_summary, input_hash,
                    output_hash, file_paths, processing_time, memory_usage, error_message,
                    warning_messages, signature, details, system_info, chain_id, parent_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_log.id,
                audit_log.operation.value,
                audit_log.timestamp.isoformat(),
                audit_log.level.value,
                audit_log.document_id,
                audit_log.user_id,
                audit_log.session_id,
                audit_log.ip_address,
                audit_log.user_agent,
                audit_log.profile_name,
                json.dumps(audit_log.detections_summary),
                audit_log.input_hash,
                audit_log.output_hash,
                json.dumps(audit_log.file_paths),
                audit_log.processing_time,
                audit_log.memory_usage,
                audit_log.error_message,
                json.dumps(audit_log.warning_messages),
                audit_log.signature,
                json.dumps(audit_log.details),
                json.dumps(audit_log.system_info.to_dict()),
                audit_log.chain_id,
                audit_log.parent_id
            ))
            conn.commit()
    
    def _update_trail_log_count(self, trail_id: str) -> None:
        """Update log count for audit trail."""
        with self._get_db_connection() as conn:
            conn.execute("""
                UPDATE audit_trails 
                SET log_count = (
                    SELECT COUNT(*) FROM audit_logs 
                    WHERE chain_id = ? OR id IN (
                        SELECT id FROM audit_logs WHERE chain_id IS NULL
                    )
                )
                WHERE id = ?
            """, (trail_id, trail_id))
            conn.commit()
    
    def get_audit_log(self, log_id: str) -> Optional[AuditLog]:
        """
        Retrieve audit log by ID.
        
        Args:
            log_id: Audit log ID
            
        Returns:
            Audit log if found, None otherwise
        """
        with self._get_db_connection() as conn:
            row = conn.execute("""
                SELECT * FROM audit_logs WHERE id = ?
            """, (log_id,)).fetchone()
            
            if row:
                return self._row_to_audit_log(row)
            return None
    
    def get_audit_trail(self, trail_id: str) -> Optional[AuditTrail]:
        """
        Retrieve audit trail by ID.
        
        Args:
            trail_id: Audit trail ID
            
        Returns:
            Audit trail if found, None otherwise
        """
        with self._get_db_connection() as conn:
            # Get trail metadata
            trail_row = conn.execute("""
                SELECT * FROM audit_trails WHERE id = ?
            """, (trail_id,)).fetchone()
            
            if not trail_row:
                return None
            
            # Get associated logs - logs are linked to trail via chain_id
            # When a trail is current, new logs get the trail's ID as chain_id
            log_rows = conn.execute("""
                SELECT * FROM audit_logs 
                WHERE chain_id = ?
                ORDER BY timestamp
            """, (trail_id,)).fetchall()
            
            # Create trail
            trail = AuditTrail(
                id=trail_row['id'],
                name=trail_row['name'],
                created_at=datetime.fromisoformat(trail_row['created_at']),
                metadata=json.loads(trail_row['metadata'] or '{}')
            )
            
            # Add logs
            for row in log_rows:
                audit_log = self._row_to_audit_log(row)
                trail.add_log(audit_log)
            
            return trail
    
    def _row_to_audit_log(self, row: sqlite3.Row) -> AuditLog:
        """Convert database row to AuditLog object."""
        from ..models.audit import SystemInfo
        
        return AuditLog(
            id=row['id'],
            operation=AuditOperation(row['operation']),
            timestamp=datetime.fromisoformat(row['timestamp']),
            level=AuditLevel(row['level']),
            document_id=row['document_id'],
            user_id=row['user_id'],
            session_id=row['session_id'],
            ip_address=row['ip_address'],
            user_agent=row['user_agent'],
            profile_name=row['profile_name'],
            detections_summary=json.loads(row['detections_summary'] or '{}'),
            input_hash=row['input_hash'],
            output_hash=row['output_hash'],
            file_paths=json.loads(row['file_paths'] or '[]'),
            processing_time=row['processing_time'],
            memory_usage=row['memory_usage'],
            error_message=row['error_message'],
            warning_messages=json.loads(row['warning_messages'] or '[]'),
            signature=row['signature'],
            details=json.loads(row['details'] or '{}'),
            system_info=SystemInfo.from_dict(json.loads(row['system_info'] or '{}')),
            chain_id=row['chain_id'],
            parent_id=row['parent_id']
        )
    
    def query_logs(
        self,
        operation: Optional[AuditOperation] = None,
        level: Optional[AuditLevel] = None,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.
        
        Args:
            operation: Filter by operation type
            level: Filter by audit level
            document_id: Filter by document ID
            user_id: Filter by user ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            
        Returns:
            List of matching audit logs
        """
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if operation:
            query += " AND operation = ?"
            params.append(operation.value)
        
        if level:
            query += " AND level = ?"
            params.append(level.value)
        
        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        with self._get_db_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_audit_log(row) for row in rows]
    
    def export_logs_to_json(self, output_path: Path, **query_params) -> int:
        """
        Export audit logs to JSON file.
        
        Args:
            output_path: Output file path
            **query_params: Query parameters for filtering
            
        Returns:
            Number of logs exported
        """
        logs = self.query_logs(**query_params)
        
        export_data = {
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_logs': len(logs),
            'query_params': query_params,
            'logs': [log.to_dict() for log in logs]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.logger.info(f"Exported {len(logs)} audit logs to {output_path}")
        return len(logs)
    
    def export_logs_to_csv(self, output_path: Path, **query_params) -> int:
        """
        Export audit logs to CSV file.
        
        Args:
            output_path: Output file path
            **query_params: Query parameters for filtering
            
        Returns:
            Number of logs exported
        """
        import csv
        
        logs = self.query_logs(**query_params)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            writer.writerow(AuditLog.get_csv_headers())
            
            # Write data
            for log in logs:
                writer.writerow(log.to_csv_row())
        
        self.logger.info(f"Exported {len(logs)} audit logs to {output_path}")
        return len(logs)
    
    def validate_all_logs(self) -> Tuple[int, int, List[str]]:
        """
        Validate all audit logs in the database.
        
        Returns:
            Tuple of (total_logs, valid_logs, list_of_issues)
        """
        logs = self.query_logs()
        total_logs = len(logs)
        valid_logs = 0
        all_issues = []
        
        for log in logs:
            if self.verify_audit_log(log):
                valid_logs += 1
            else:
                all_issues.append(f"Invalid signature for log {log.id}")
        
        self.logger.info(f"Validated {total_logs} logs: {valid_logs} valid, {len(all_issues)} issues")
        return total_logs, valid_logs, all_issues
    
    def cleanup_old_logs(self, retention_days: Optional[int] = None) -> int:
        """
        Clean up old audit logs based on retention policy.
        
        Args:
            retention_days: Days to retain (uses instance default if None)
            
        Returns:
            Number of logs deleted
        """
        retention_days = retention_days or self.retention_days
        cutoff_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=retention_days)
        
        with self._get_db_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM audit_logs WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            deleted_count = cursor.rowcount
            conn.commit()
        
        self.logger.info(f"Cleaned up {deleted_count} old audit logs (older than {retention_days} days)")
        return deleted_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._get_db_connection() as conn:
            # Total logs
            total_logs = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
            
            # Logs by operation
            operation_stats = {}
            for row in conn.execute("""
                SELECT operation, COUNT(*) as count 
                FROM audit_logs 
                GROUP BY operation
            """).fetchall():
                operation_stats[row[0]] = row[1]
            
            # Logs by level
            level_stats = {}
            for row in conn.execute("""
                SELECT level, COUNT(*) as count 
                FROM audit_logs 
                GROUP BY level
            """).fetchall():
                level_stats[row[0]] = row[1]
            
            # Recent activity (last 24 hours)
            recent_cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            recent_logs = conn.execute("""
                SELECT COUNT(*) FROM audit_logs WHERE timestamp >= ?
            """, (recent_cutoff,)).fetchone()[0]
            
            # Signed logs
            signed_logs = conn.execute("""
                SELECT COUNT(*) FROM audit_logs WHERE signature IS NOT NULL
            """).fetchone()[0]
            
            # Error logs
            error_logs = conn.execute("""
                SELECT COUNT(*) FROM audit_logs WHERE level IN ('error', 'critical')
            """).fetchone()[0]
            
            return {
                'total_logs': total_logs,
                'operations': operation_stats,
                'levels': level_stats,
                'recent_logs_24h': recent_logs,
                'signed_logs': signed_logs,
                'error_logs': error_logs,
                'signing_enabled': self.enable_signing,
                'auto_sign_enabled': self.auto_sign,
                'storage_path': str(self.storage_path),
                'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            }
    
    def close(self) -> None:
        """Close the audit logger and clean up resources."""
        self.logger.info("Closing audit logger")
        # Database connections are closed automatically with context managers
        # No additional cleanup needed for this implementation