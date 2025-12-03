#!/usr/bin/env python3
"""
Comprehensive import path fixing script for AlphaCouncil project
Fixes all tradingagents imports to local project paths
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

class ImportFixer:
    """Import path fixing utility"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.fixed_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
        # Define comprehensive replacement rules
        self.replacements = [
            # Basic module imports
            (r'from tradingagents\.agents\.', 'from backend.agents.'),
            (r'from tradingagents\.tools\.', 'from backend.dataflows.'),
            (r'from tradingagents\.dataflows\.', 'from backend.dataflows.'),
            (r'from tradingagents\.utils\.', 'from backend.utils.'),
            (r'from tradingagents\.models\.', 'from backend.models.'),
            (r'from tradingagents\.config\.', 'from backend.config.'),
            (r'from tradingagents\.api\.', 'from backend.api.'),
            
            # Specific file imports
            (r'from tradingagents\.utils\.logging_init import', 'from backend.utils.logging_config import'),
            (r'from tradingagents\.utils\.logging_manager import', 'from backend.utils.logging_config import'),
            (r'from tradingagents\.utils\.tool_logging import', 'from backend.utils.tool_logging import'),
            (r'from tradingagents\.utils\.stock_utils import', 'from backend.utils.stock_utils import'),
            
            # News tools
            (r'from tradingagents\.tools\.unified_news_tool import', 'from backend.dataflows.news.unified_news_tool import'),
            (r'from tradingagents\.dataflows\.unified_news_tool import', 'from backend.dataflows.news.unified_news_tool import'),
            
            # Agent utilities
            (r'from tradingagents\.agents\.utils\.', 'from backend.agents.utils.'),
            
            # Specific dataflows
            (r'from tradingagents\.dataflows\.interface import', 'from backend.dataflows.interface import'),
            (r'from tradingagents\.dataflows\.improved_hk_utils import', 'from backend.dataflows.improved_hk_utils import'),
            (r'from tradingagents\.dataflows\.realtime_news_utils import', 'from backend.dataflows.realtime_news_utils import'),
            (r'from tradingagents\.dataflows\.tushare_utils import', 'from backend.dataflows.tushare_utils import'),
            (r'from tradingagents\.dataflows\.akshare_utils import', 'from backend.dataflows.akshare_utils import'),
            
            # Import statements
            (r'import tradingagents\.agents\.', 'import backend.agents.'),
            (r'import tradingagents\.', 'import backend.'),
            (r'import tradingagents', '# import tradingagents (removed)'),
        ]
        
    def fix_file(self, file_path: Path) -> Tuple[bool, str]:
        """Fix imports in a single file"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            modified = False
            
            # Apply all replacement rules
            for pattern, replacement in self.replacements:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    modified = True
                    content = new_content
                    
            # Write back if modified
            if modified:
                # Create backup
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                if not backup_path.exists():
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                        
                # Write modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.fixed_count += 1
                return True, f"Fixed: {file_path.relative_to(self.project_root)}"
            else:
                self.skipped_count += 1
                return False, f"No changes: {file_path.relative_to(self.project_root)}"
                
        except Exception as e:
            self.error_count += 1
            return False, f"Error in {file_path.relative_to(self.project_root)}: {str(e)}"
            
    def fix_directory(self, directory: Path) -> List[str]:
        """Fix all Python files in directory recursively"""
        results = []
        
        for py_file in directory.rglob('*.py'):
            # Skip __pycache__ and backup files
            if '__pycache__' in str(py_file) or py_file.suffix == '.backup':
                continue
                
            # Skip TradingAgents-CN-main directory
            if 'TradingAgents-CN-main' in str(py_file):
                continue
                
            fixed, message = self.fix_file(py_file)
            results.append(message)
            
        return results
        
    def run(self) -> None:
        """Run the import fixing process"""
        print("=" * 70)
        print("AlphaCouncil Import Path Fixer")
        print("=" * 70)
        print(f"Project root: {self.project_root}")
        print()
        
        # Directories to process
        directories = [
            self.project_root / 'agents',
            self.project_root / 'backend',
            self.project_root / 'scripts',
            self.project_root / 'api',
        ]
        
        all_results = []
        
        for directory in directories:
            if directory.exists():
                print(f"Processing: {directory.relative_to(self.project_root)}/")
                results = self.fix_directory(directory)
                all_results.extend(results)
                print(f"  Processed {len(results)} files")
                
        # Print summary
        print()
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"✅ Fixed files: {self.fixed_count}")
        print(f"⏭️  Skipped files: {self.skipped_count}")
        print(f"❌ Error files: {self.error_count}")
        
        # Show fixed files
        if self.fixed_count > 0:
            print()
            print("Fixed files:")
            for result in all_results:
                if result.startswith("Fixed:"):
                    print(f"  • {result}")
                    
        # Show errors
        if self.error_count > 0:
            print()
            print("Errors:")
            for result in all_results:
                if result.startswith("Error"):
                    print(f"  • {result}")
                    
        print()
        print("💡 Tips:")
        print("  1. Original files are backed up with .backup extension")
        print("  2. Review the changes to ensure correctness")
        print("  3. Run tests to verify functionality")
        

def main():
    """Main entry point"""
    # Get project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Create and run fixer
    fixer = ImportFixer(project_root)
    fixer.run()
    
    # Return exit code
    sys.exit(0 if fixer.error_count == 0 else 1)


if __name__ == "__main__":
    main()
