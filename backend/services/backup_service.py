"""
Backup and Recovery System
Automated database backups with retention policies
"""
import os
import shutil
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Manage database backups and recovery"""
    
    def __init__(self, backup_dir: str = "backups", retention_days: int = 30):
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.backup_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.backup_dir / "daily").mkdir(exist_ok=True)
        (self.backup_dir / "weekly").mkdir(exist_ok=True)
        (self.backup_dir / "monthly").mkdir(exist_ok=True)
    
    def create_backup(self, db_path: str, backup_type: str = "daily") -> str:
        """
        Create a database backup
        
        Args:
            db_path: Path to database file
            backup_type: daily, weekly, or monthly
            
        Returns:
            Path to backup file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{backup_type}_{timestamp}.db"
        
        # Determine destination directory
        if backup_type == "weekly":
            dest_dir = self.backup_dir / "weekly"
        elif backup_type == "monthly":
            dest_dir = self.backup_dir / "monthly"
        else:
            dest_dir = self.backup_dir / "daily"
        
        backup_path = dest_dir / backup_name
        
        try:
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            # Compress backup
            compressed_path = f"{backup_path}.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed backup
            os.remove(backup_path)
            
            # Create metadata
            metadata = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': backup_type,
                'original_size': os.path.getsize(db_path),
                'compressed_size': os.path.getsize(compressed_path),
                'compression_ratio': round(
                    os.path.getsize(compressed_path) / os.path.getsize(db_path) * 100, 2
                )
            }
            
            metadata_path = f"{compressed_path}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Backup created: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def restore_backup(self, backup_path: str, restore_path: str) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            restore_path: Path where to restore database
            
        Returns:
            Success status
        """
        try:
            # Decompress backup
            temp_path = f"{restore_path}.temp"
            
            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Move to final location
            shutil.move(temp_path, restore_path)
            
            logger.info(f"Backup restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        for backup_type in ["daily", "weekly", "monthly"]:
            backup_dir = self.backup_dir / backup_type
            
            # Different retention for different types
            if backup_type == "weekly":
                type_retention = self.retention_days * 2
            elif backup_type == "monthly":
                type_retention = self.retention_days * 4
            else:
                type_retention = self.retention_days
            
            type_cutoff = datetime.utcnow() - timedelta(days=type_retention)
            
            for backup_file in backup_dir.glob("*.db.gz"):
                # Get file modification time
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if mtime < type_cutoff:
                    try:
                        backup_file.unlink()
                        # Also remove metadata
                        metadata_file = Path(f"{backup_file}.json")
                        if metadata_file.exists():
                            metadata_file.unlink()
                        
                        logger.info(f"Removed old backup: {backup_file}")
                    except Exception as e:
                        logger.error(f"Failed to remove backup {backup_file}: {e}")
    
    def list_backups(self, backup_type: str = None) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        types_to_check = [backup_type] if backup_type else ["daily", "weekly", "monthly"]
        
        for btype in types_to_check:
            backup_dir = self.backup_dir / btype
            
            for backup_file in sorted(backup_dir.glob("*.db.gz"), reverse=True):
                metadata_file = Path(f"{backup_file}.json")
                
                backup_info = {
                    'path': str(backup_file),
                    'type': btype,
                    'size': os.path.getsize(backup_file),
                    'created': datetime.fromtimestamp(
                        backup_file.stat().st_mtime
                    ).isoformat()
                }
                
                # Load metadata if exists
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        backup_info['metadata'] = json.load(f)
                
                backups.append(backup_info)
        
        return backups
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics"""
        stats = {
            'total_backups': 0,
            'total_size_bytes': 0,
            'by_type': {},
            'oldest_backup': None,
            'newest_backup': None
        }
        
        all_backups = self.list_backups()
        
        stats['total_backups'] = len(all_backups)
        stats['total_size_bytes'] = sum(b['size'] for b in all_backups)
        
        # Group by type
        for backup in all_backups:
            btype = backup['type']
            if btype not in stats['by_type']:
                stats['by_type'][btype] = {'count': 0, 'size': 0}
            
            stats['by_type'][btype]['count'] += 1
            stats['by_type'][btype]['size'] += backup['size']
        
        # Oldest and newest
        if all_backups:
            stats['oldest_backup'] = all_backups[-1]['created']
            stats['newest_backup'] = all_backups[0]['created']
        
        return stats
    
    def verify_backup_integrity(self, backup_path: str) -> bool:
        """Verify backup file integrity"""
        try:
            # Try to open and read compressed file
            with gzip.open(backup_path, 'rb') as f:
                # Read in chunks to verify
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
            
            logger.info(f"Backup verified: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed for {backup_path}: {e}")
            return False


# Global backup manager
_backup_manager = None

def get_backup_manager(backup_dir: str = "backups", retention_days: int = 30) -> BackupManager:
    """Get global backup manager instance"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager(backup_dir, retention_days)
    return _backup_manager


def schedule_backups():
    """Setup automated backup schedule"""
    import schedule
    import time
    import threading
    
    def run_daily_backup():
        try:
            manager = get_backup_manager()
            db_path = "db/rfp_system.db"  # Adjust path as needed
            manager.create_backup(db_path, "daily")
            manager.cleanup_old_backups()
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
    
    def run_weekly_backup():
        try:
            manager = get_backup_manager()
            db_path = "db/rfp_system.db"
            manager.create_backup(db_path, "weekly")
        except Exception as e:
            logger.error(f"Weekly backup failed: {e}")
    
    def run_monthly_backup():
        try:
            manager = get_backup_manager()
            db_path = "db/rfp_system.db"
            manager.create_backup(db_path, "monthly")
        except Exception as e:
            logger.error(f"Monthly backup failed: {e}")
    
    # Schedule backups
    schedule.every().day.at("02:00").do(run_daily_backup)
    schedule.every().sunday.at("03:00").do(run_weekly_backup)
    schedule.every().month.at("04:00").do(run_monthly_backup)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
    
    # Run scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Backup scheduler started")
