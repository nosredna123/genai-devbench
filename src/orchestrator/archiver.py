"""
Artifact archiving and integrity verification.

Compresses run artifacts and computes checksums.
"""

import tarfile
import hashlib
import json
from pathlib import Path
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__, component="orchestrator")


class Archiver:
    """Handles artifact archiving and verification."""
    
    def __init__(self, run_id: str, run_dir: Path):
        """
        Initialize archiver for a run.
        
        Args:
            run_id: Run identifier
            run_dir: Run directory path
        """
        self.run_id = run_id
        self.run_dir = run_dir
        
    def create_archive(
        self,
        workspace_dir: Path,
        metrics_file: Path,
        logs: Dict[str, Path]
    ) -> Path:
        """
        Create compressed archive of run artifacts.
        
        Args:
            workspace_dir: Framework workspace directory
            metrics_file: Path to metrics.json
            logs: Dictionary of log file paths
            
        Returns:
            Path to created archive
        """
        archive_path = self.run_dir / "run.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            # Add workspace
            if workspace_dir.exists():
                tar.add(workspace_dir, arcname="workspace")
                logger.debug("Added workspace to archive",
                           extra={'run_id': self.run_id})
            
            # Add metrics
            if metrics_file.exists():
                tar.add(metrics_file, arcname="metrics.json")
                logger.debug("Added metrics to archive",
                           extra={'run_id': self.run_id})
            
            # Add artifacts directory (generated code from frameworks like ChatDev)
            artifacts_dir = self.run_dir / "artifacts"
            if artifacts_dir.exists():
                tar.add(artifacts_dir, arcname="artifacts")
                logger.debug("Added artifacts to archive",
                           extra={'run_id': self.run_id,
                                 'metadata': {'artifact_count': len(list(artifacts_dir.iterdir()))}})
            
            # Add logs
            for log_name, log_path in logs.items():
                if log_path.exists():
                    tar.add(log_path, arcname=log_name)
                    logger.debug(f"Added {log_name} to archive",
                               extra={'run_id': self.run_id})
                               
        logger.info(f"Archive created: {archive_path}",
                   extra={'run_id': self.run_id, 'event': 'archive_created'})
                   
        return archive_path
        
    def compute_hash(self, archive_path: Path) -> str:
        """
        Compute SHA-256 hash of archive.
        
        Args:
            archive_path: Path to archive file
            
        Returns:
            Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()
        
        with open(archive_path, 'rb') as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        hash_value = sha256_hash.hexdigest()
        
        logger.info(f"Archive hash computed: {hash_value[:16]}...",
                   extra={'run_id': self.run_id, 'event': 'hash_computed'})
                   
        return hash_value
        
    def create_metadata(
        self,
        archive_path: Path,
        archive_hash: str,
        framework: str,
        commit_hash: str
    ) -> Path:
        """
        Create metadata file with archive information.
        
        Args:
            archive_path: Path to archive
            archive_hash: SHA-256 hash of archive
            framework: Framework name
            commit_hash: Framework repository commit hash
            
        Returns:
            Path to metadata.json file
        """
        metadata = {
            'run_id': self.run_id,
            'framework': framework,
            'framework_commit': commit_hash,
            'archive_path': str(archive_path.name),
            'archive_hash': archive_hash,
            'archive_size_bytes': archive_path.stat().st_size
        }
        
        metadata_path = self.run_dir / "metadata.json"
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info("Metadata file created",
                   extra={'run_id': self.run_id, 'event': 'metadata_created'})
                   
        return metadata_path
        
    def save_commit_info(self, commit_hash: str) -> Path:
        """
        Save framework commit hash to file.
        
        Args:
            commit_hash: Repository commit SHA
            
        Returns:
            Path to framework_version.txt file
        """
        summary_dir = self.run_dir / "summary"
        summary_dir.mkdir(parents=True, exist_ok=True)
        commit_file = summary_dir / "framework_version.txt"
        
        with open(commit_file, 'w', encoding='utf-8') as f:
            f.write(commit_hash)
            
        logger.debug("Framework version saved",
                    extra={'run_id': self.run_id})
                    
        return commit_file
        
    def verify_archive(self, archive_path: Path, expected_hash: str) -> bool:
        """
        Verify archive integrity by comparing hashes.
        
        Args:
            archive_path: Path to archive
            expected_hash: Expected SHA-256 hash
            
        Returns:
            True if hashes match, False otherwise
        """
        actual_hash = self.compute_hash(archive_path)
        
        if actual_hash == expected_hash:
            logger.info("Archive integrity verified",
                       extra={'run_id': self.run_id, 'event': 'verification_success'})
            return True
        else:
            logger.error("Archive integrity check FAILED",
                        extra={'run_id': self.run_id, 'event': 'verification_failed',
                              'metadata': {
                                  'expected': expected_hash[:16],
                                  'actual': actual_hash[:16]
                              }})
            return False
