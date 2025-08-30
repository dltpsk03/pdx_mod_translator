"""
File processing and validation module
"""

import os
import glob
import shutil
from typing import List, Tuple, Dict, Any, Optional


class FileProcessor:
    """Handle file discovery, validation, and processing"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback or print
    
    def discover_yaml_files(self, input_folder: str) -> List[str]:
        """Discover YAML files in the input folder recursively"""
        yml_files = []
        
        try:
            for ext in ['*.yml', '*.yaml']:
                pattern = os.path.join(input_folder, '**', ext)
                yml_files.extend(glob.glob(pattern, recursive=True))
            
            # Sort files for consistent processing order
            yml_files.sort()
            
            self.log_callback(f"{len(yml_files)}개의 YAML 파일을 발견했습니다.")
            return yml_files
            
        except Exception as e:
            self.log_callback(f"파일 검색 중 오류 발생: {e}")
            return []
    
    def validate_file_for_processing(self, file_path: str) -> Tuple[bool, str, Dict]:
        """Validate if file can be processed"""
        try:
            self.log_callback(f"검증 단계 1: 파일 존재 확인 - {file_path}")
            
            # Check file exists
            if not os.path.exists(file_path):
                return False, "파일이 존재하지 않습니다", {}
            
            self.log_callback(f"검증 단계 2: 파일 크기 확인")
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "파일이 비어있습니다", {'file_size': file_size}
            
            # Check if file is too large (>50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if file_size > max_size:
                return False, f"파일이 너무 큽니다 ({file_size / 1024 / 1024:.1f}MB)", {'file_size': file_size}
            
            self.log_callback(f"검증 단계 3: 파일 내용 읽기 시도 (크기: {file_size} bytes)")
            
            # Try to read file and count lines
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                
                self.log_callback(f"검증 단계 4: 파일 내용 분석 (총 {len(lines)}줄)")
                
                total_lines = len(lines)
                translatable_lines = self._count_translatable_lines(lines)
                
                self.log_callback(f"검증 단계 5: 번역 가능한 줄 수 확인 ({translatable_lines}개)")
                
                if translatable_lines == 0:
                    return False, "번역 가능한 내용이 없습니다", {
                        'total_lines': total_lines,
                        'translatable_lines': translatable_lines
                    }
                
                return True, "처리 가능", {
                    'file_size': file_size,
                    'total_lines': total_lines,
                    'translatable_lines': translatable_lines
                }
                
            except UnicodeDecodeError as e:
                self.log_callback(f"검증 오류: 인코딩 문제 - {e}")
                return False, "파일 인코딩을 읽을 수 없습니다", {'file_size': file_size}
            except Exception as e:
                self.log_callback(f"검증 오류: 파일 읽기 실패 - {e}")
                return False, f"파일 읽기 오류: {str(e)}", {'file_size': file_size}
                
        except Exception as e:
            self.log_callback(f"검증 오류: 전체 검증 실패 - {e}")
            return False, f"파일 검증 오류: {str(e)}", {}
    
    def _count_translatable_lines(self, lines: List[str]) -> int:
        """Count lines that contain translatable content"""
        translatable_count = 0
        
        for line in lines:
            cleaned_line = line.strip()
            
            # Skip empty lines, comments, and language headers
            if (cleaned_line and 
                not cleaned_line.startswith('#') and 
                not cleaned_line.startswith('l_') and
                ':' in cleaned_line):
                
                # Check if line contains quoted text (translatable content)
                if '"' in cleaned_line:
                    translatable_count += 1
        
        return translatable_count
    
    def prepare_output_path(self, file_path: str, input_folder: str, 
                           output_folder: str, target_lang: str = 'korean') -> str:
        """Prepare output path preserving folder structure and translating filename"""
        try:
            # Get relative path to preserve folder structure
            relative_path = os.path.relpath(file_path, input_folder)
            
            # Translate filename
            dir_path = os.path.dirname(relative_path)
            filename = os.path.basename(relative_path)
            name, ext = os.path.splitext(filename)
            
            # Translate language identifier in filename
            if '_l_english' in name and target_lang.lower() == 'korean':
                translated_name = name.replace('_l_english', '_l_korean')
            elif 'l_english' in name and target_lang.lower() == 'korean':
                translated_name = name.replace('l_english', 'l_korean')  
            else:
                translated_name = name
            
            translated_filename = translated_name + ext
            translated_relative_path = os.path.join(dir_path, translated_filename) if dir_path else translated_filename
            output_path = os.path.join(output_folder, translated_relative_path)
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if not empty
                os.makedirs(output_dir, exist_ok=True)
            
            return output_path
            
        except Exception as e:
            self.log_callback(f"출력 경로 준비 중 오류: {e}")
            # Fallback to simple path
            return os.path.join(output_folder, os.path.basename(file_path))
    
    def copy_file_with_header_change(self, source_path: str, output_path: str, 
                                   source_lang: str = 'english', 
                                   target_lang: str = 'korean') -> bool:
        """Copy file and change language header"""
        try:
            # Copy file first
            shutil.copy2(source_path, output_path)
            
            # Read and modify content
            with open(output_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            # Change language header (l_english: -> l_korean:)
            if target_lang.lower() == 'korean' and source_lang.lower() == 'english':
                content = content.replace('l_english:', 'l_korean:', 1)
            
            # Write modified content
            with open(output_path, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            self.log_callback(f"파일 복사 및 헤더 변경 실패: {e}")
            return False
    
    def process_single_file_basic(self, file_path: str, input_folder: str, 
                                output_folder: str, source_lang: str = 'english',
                                target_lang: str = 'korean') -> bool:
        """Basic file processing (copy + header change only)"""
        try:
            file_name = os.path.basename(file_path)
            
            # Prepare output path
            output_path = self.prepare_output_path(
                file_path, input_folder, output_folder, target_lang
            )
            
            self.log_callback(f"파일 처리 시작: {file_name} -> {os.path.basename(output_path)}")
            
            # Copy file and change header
            success = self.copy_file_with_header_change(
                file_path, output_path, source_lang, target_lang
            )
            
            if success:
                self.log_callback(f"파일 처리 완료: {file_name}")
            else:
                self.log_callback(f"파일 처리 실패: {file_name}")
            
            return success
            
        except Exception as e:
            self.log_callback(f"파일 처리 중 오류 ({os.path.basename(file_path)}): {e}")
            return False
    
    def get_file_statistics(self, yml_files: List[str]) -> Dict[str, Any]:
        """Get statistics about discovered files"""
        if not yml_files:
            return {
                'total_files': 0,
                'total_size_mb': 0.0,
                'estimated_lines': 0,
                'largest_file': None,
                'smallest_file': None
            }
        
        try:
            file_sizes = []
            total_lines = 0
            
            for file_path in yml_files:
                try:
                    size = os.path.getsize(file_path)
                    file_sizes.append((file_path, size))
                    
                    # Estimate lines (rough calculation)
                    estimated_file_lines = max(1, size // 50)  # ~50 bytes per line average
                    total_lines += estimated_file_lines
                    
                except Exception:
                    continue
            
            if not file_sizes:
                return self.get_file_statistics([])
            
            total_size = sum(size for _, size in file_sizes)
            largest_file = max(file_sizes, key=lambda x: x[1])
            smallest_file = min(file_sizes, key=lambda x: x[1])
            
            return {
                'total_files': len(yml_files),
                'total_size_mb': total_size / (1024 * 1024),
                'estimated_lines': total_lines,
                'largest_file': {
                    'path': largest_file[0],
                    'size_mb': largest_file[1] / (1024 * 1024)
                },
                'smallest_file': {
                    'path': smallest_file[0],
                    'size_mb': smallest_file[1] / (1024 * 1024)
                }
            }
            
        except Exception as e:
            self.log_callback(f"파일 통계 계산 중 오류: {e}")
            return self.get_file_statistics([])
    
    def cleanup_temp_files(self, temp_dir: Optional[str] = None) -> None:
        """Clean up temporary files"""
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                self.log_callback(f"임시 파일 정리 완료: {temp_dir}")
        except Exception as e:
            self.log_callback(f"임시 파일 정리 중 오류: {e}")