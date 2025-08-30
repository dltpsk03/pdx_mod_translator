"""
Translation caching system with SQLite backend and LRU memory cache
"""

import hashlib
import sqlite3
import os
import logging
from typing import Dict, Optional, Any
from collections import OrderedDict


class TranslationCache:
    """SQLite-based translation cache for avoiding duplicate translations"""
    
    def __init__(self, cache_dir: str = "cache", max_memory_items: int = 1000):
        self.cache_dir = cache_dir
        self.max_memory_items = max_memory_items
        os.makedirs(cache_dir, exist_ok=True)
        
        # In-memory cache for frequently accessed items
        self.memory_cache = OrderedDict()
        
        # Initialize SQLite database
        self.db_path = os.path.join(cache_dir, "translation_cache.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite cache database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translation_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text_hash TEXT UNIQUE NOT NULL,
                    original_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    source_lang TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    api_provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_text_hash ON translation_cache(text_hash)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_accessed ON translation_cache(last_accessed)
            """)
    
    def _generate_cache_key(self, text: str, source_lang: str, target_lang: str, 
                           api_provider: str, model_name: str) -> str:
        """Generate a unique cache key for the translation request"""
        content = f"{text}|{source_lang}|{target_lang}|{api_provider}|{model_name}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def get_translation(self, text: str, source_lang: str, target_lang: str,
                       api_provider: str, model_name: str) -> Optional[str]:
        """Get cached translation if available"""
        cache_key = self._generate_cache_key(text, source_lang, target_lang, api_provider, model_name)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            # Move to end (most recently used)
            translation = self.memory_cache.pop(cache_key)
            self.memory_cache[cache_key] = translation
            return translation
        
        # Check database cache
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT translated_text FROM translation_cache 
                WHERE text_hash = ?
            """, (cache_key,))
            
            result = cursor.fetchone()
            if result:
                translation = result[0]
                
                # Update access statistics
                conn.execute("""
                    UPDATE translation_cache 
                    SET access_count = access_count + 1, 
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE text_hash = ?
                """, (cache_key,))
                
                # Add to memory cache
                self._add_to_memory_cache(cache_key, translation)
                
                return translation
        
        return None
    
    def store_translation(self, text: str, translation: str, source_lang: str,
                         target_lang: str, api_provider: str, model_name: str):
        """Store translation in cache"""
        cache_key = self._generate_cache_key(text, source_lang, target_lang, api_provider, model_name)
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO translation_cache 
                (text_hash, original_text, translated_text, source_lang, target_lang, 
                 api_provider, model_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cache_key, text, translation, source_lang, target_lang, api_provider, model_name))
        
        # Add to memory cache
        self._add_to_memory_cache(cache_key, translation)
    
    def _add_to_memory_cache(self, key: str, value: str):
        """Add item to memory cache with LRU eviction"""
        if key in self.memory_cache:
            self.memory_cache.pop(key)
        elif len(self.memory_cache) >= self.max_memory_items:
            # Remove least recently used item
            self.memory_cache.popitem(last=False)
        
        self.memory_cache[key] = value
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(access_count) as total_accesses,
                    AVG(access_count) as avg_accesses,
                    COUNT(DISTINCT api_provider) as providers_used,
                    COUNT(DISTINCT model_name) as models_used
                FROM translation_cache
            """)
            
            stats = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
            stats['memory_cache_size'] = len(self.memory_cache)
            stats['memory_cache_max'] = self.max_memory_items
            
            return stats
    
    def cleanup_old_entries(self, days_old: int = 30):
        """Remove cache entries older than specified days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM translation_cache 
                WHERE last_accessed < datetime('now', '-{} days')
            """.format(days_old))
            
            deleted_count = cursor.rowcount
            logging.info(f"Cleaned up {deleted_count} old cache entries")