import logging
import json
import hashlib
from datetime import datetime
from config import LOG_LEVEL, LOG_FILE, AUDIT_LOG_FILE

def setup_logger():
    """Setup application logger with forensic-grade logging"""
    logger = logging.getLogger('gopnik')
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Create handlers
    file_handler = logging.FileHandler(LOG_FILE)
    console_handler = logging.StreamHandler()
    
    # Create formatters
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Add formatters to handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def generate_file_hash(file_path):
    """Generate SHA256 hash of a file for forensic integrity"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read file in chunks for large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"Error generating hash: {str(e)}"

def log_processing(input_path, output_path, pii_results, logger):
    """Log detailed processing information for forensic purposes"""
    try:
        # Generate file hashes
        input_hash = generate_file_hash(input_path)
        output_hash = generate_file_hash(output_path)
        
        # Prepare audit log entry
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'input_file': input_path,
            'input_hash': input_hash,
            'output_file': output_path,
            'output_hash': output_hash,
            'pii_detected': len(pii_results),
            'pii_details': pii_results,
            'processing_time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        }
        
        # Write to audit log
        with open(AUDIT_LOG_FILE, 'a') as audit_log:
            audit_log.write(json.dumps(audit_entry) + '\n')
        
        logger.info(f"Processed {input_path} -> {output_path}")
        logger.info(f"Detected {len(pii_results)} PII instances")
        
    except Exception as e:
        logger.error(f"Error in audit logging: {str(e)}")

def get_audit_logs(limit=100):
    """Retrieve recent audit logs"""
    try:
        with open(AUDIT_LOG_FILE, 'r') as audit_log:
            lines = audit_log.readlines()[-limit:]
            return [json.loads(line) for line in lines]
    except FileNotFoundError:
        return []
    except Exception as e:
        return [{'error': f'Could not read audit log: {str(e)}'}]