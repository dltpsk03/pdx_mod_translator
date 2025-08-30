"""
Translation recovery and checkpoint management module
"""

import os
import time
import json
from typing import Dict, Optional, Any


class TranslationRecovery:
    """Enhanced recovery system with better checkpoint management"""
    
    def __init__(self, checkpoint_dir="checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        self.checkpoint_schema_version = "2.0"
    
    def save_checkpoint(self, file_path: str, completed_lines: int, total_lines: int, 
                       api_provider: str = None, error_stats: Dict = None, 
                       performance_stats: Dict = None) -> None:
        """Enhanced checkpoint saving with additional metadata"""
        checkpoint_file = os.path.join(
            self.checkpoint_dir, 
            f"{os.path.basename(file_path)}.checkpoint"
        )
        
        checkpoint_data = {
            'schema_version': self.checkpoint_schema_version,
            'file_path': file_path,
            'completed_lines': completed_lines,
            'total_lines': total_lines,
            'timestamp': time.time(),
            'api_provider': api_provider,
            'error_stats': error_stats or {},
            'performance_stats': performance_stats or {}
        }
        
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save checkpoint for {file_path}: {e}")
    
    def load_checkpoint(self, file_path: str) -> Optional[Dict]:
        """Load checkpoint with schema validation"""
        checkpoint_file = os.path.join(
            self.checkpoint_dir, 
            f"{os.path.basename(file_path)}.checkpoint"
        )
        
        if not os.path.exists(checkpoint_file):
            return None
            
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validate schema version
            if data.get('schema_version') == self.checkpoint_schema_version:
                return data
            else:
                # Migrate old format
                return {
                    'schema_version': self.checkpoint_schema_version,
                    'file_path': data.get('file_path', file_path),
                    'completed_lines': data.get('completed_lines', 0),
                    'total_lines': data.get('total_lines', 0),
                    'timestamp': data.get('timestamp', time.time()),
                    'api_provider': None,
                    'error_stats': {},
                    'performance_stats': {}
                }
        except Exception as e:
            print(f"Warning: Failed to load checkpoint for {file_path}: {e}")
            return None
    
    def remove_checkpoint(self, file_path: str) -> None:
        """Remove checkpoint file"""
        checkpoint_file = os.path.join(
            self.checkpoint_dir, 
            f"{os.path.basename(file_path)}.checkpoint"
        )
        
        try:
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
        except Exception as e:
            print(f"Warning: Failed to remove checkpoint for {file_path}: {e}")
    
    def cleanup_old_checkpoints(self, days_old: int = 7) -> None:
        """Clean up old checkpoint files"""
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        try:
            for filename in os.listdir(self.checkpoint_dir):
                if filename.endswith('.checkpoint'):
                    filepath = os.path.join(self.checkpoint_dir, filename)
                    if os.path.getctime(filepath) < cutoff_time:
                        os.remove(filepath)
        except Exception as e:
            print(f"Warning: Failed to cleanup old checkpoints: {e}")
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """Get recovery system status"""
        try:
            checkpoint_files = [
                f for f in os.listdir(self.checkpoint_dir) 
                if f.endswith('.checkpoint')
            ]
            
            return {
                'checkpoint_dir': self.checkpoint_dir,
                'active_checkpoints': len(checkpoint_files),
                'schema_version': self.checkpoint_schema_version,
                'checkpoint_files': checkpoint_files
            }
        except Exception:
            return {
                'checkpoint_dir': self.checkpoint_dir,
                'active_checkpoints': 0,
                'schema_version': self.checkpoint_schema_version,
                'checkpoint_files': []
            }