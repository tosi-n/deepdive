#!/usr/bin/env python3
"""
Validate SQL queries for safety and correctness.
Usage: python validate_query.py --query "SQL" [--strict]
"""

import re
import argparse
from typing import List, Tuple, Dict


class QueryValidator:
    """Validates SQL queries for safety issues."""
    
    # Patterns that indicate write operations
    WRITE_PATTERNS = [
        r'^\s*INSERT\s+INTO',
        r'^\s*UPDATE\s+',
        r'^\s*DELETE\s+FROM',
        r'^\s*DELETE\s+',
        r'^\s*TRUNCATE\s+TABLE',
        r'^\s*DROP\s+',
        r'^\s*ALTER\s+TABLE',
        r'^\s*CREATE\s+',
        r'^\s*GRANT\s+',
        r'^\s*REVOKE\s+',
    ]
    
    # Dangerous patterns that might indicate injection or errors
    DANGEROUS_PATTERNS = [
        (r';\s*DROP\s+', 'Potential SQL injection: DROP after semicolon'),
        (r';\s*DELETE\s+', 'Potential SQL injection: DELETE after semicolon'),
        (r'--\s*$', 'Comment injection attempt'),
        (r'/\*.*\*/', 'Block comment (potential injection)'),
        (r'UNION\s+SELECT', 'UNION SELECT (potential data extraction)'),
        (r'SLEEP\s*\(', 'SLEEP function (potential DoS)'),
        (r'BENCHMARK\s*\(', 'BENCHMARK function (potential DoS)'),
    ]
    
    # Common mistakes
    COMMON_MISTAKES = [
        (r'SELECT\s+\*\s+FROM\s+\w+\s*$', 'Missing WHERE clause on SELECT *'),
        (r'WHERE\s+\w+\s*=\s*NULL', 'Use IS NULL instead of = NULL'),
        (r'GROUP\s+BY\s+\w+\s+SELECT\s+.*[^,]\s+\w+\s*,', 'Missing aggregation on non-GROUP BY column'),
    ]
    
    def __init__(self, strict: bool = False):
        self.strict = strict
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def validate(self, query: str) -> Dict:
        """Run all validation checks on a query."""
        self.warnings = []
        self.errors = []
        
        # Check for write operations
        is_write = self._detect_write_operation(query)
        
        # Check for dangerous patterns
        self._check_dangerous_patterns(query)
        
        # Check for common mistakes
        self._check_common_mistakes(query)
        
        # Check query structure
        self._check_structure(query)
        
        return {
            'is_write': is_write,
            'is_valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'query_type': self._classify_query(query)
        }
    
    def _detect_write_operation(self, query: str) -> bool:
        """Detect if query is a write operation."""
        query_upper = query.strip().upper()
        
        for pattern in self.WRITE_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return True
        
        # Check for CTEs with writes
        if re.search(r'WITH\s+\w+\s+AS\s*\(.*\)\s*(INSERT|UPDATE|DELETE)', 
                     query_upper, re.IGNORECASE | re.DOTALL):
            return True
        
        return False
    
    def _check_dangerous_patterns(self, query: str):
        """Check for potentially dangerous SQL patterns."""
        for pattern, message in self.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                if self.strict:
                    self.errors.append(f"DANGER: {message}")
                else:
                    self.warnings.append(f"WARNING: {message}")
    
    def _check_common_mistakes(self, query: str):
        """Check for common SQL mistakes."""
        for pattern, message in self.COMMON_MISTAKES:
            if re.search(pattern, query, re.IGNORECASE):
                self.warnings.append(message)
    
    def _check_structure(self, query: str):
        """Check query structure and syntax."""
        # Check for unmatched parentheses
        open_parens = query.count('(')
        close_parens = query.count(')')
        if open_parens != close_parens:
            self.errors.append(f"Syntax: Unmatched parentheses ({open_parens} open, {close_parens} close)")
        
        # Check for unmatched quotes
        single_quotes = query.count("'") - query.count("\\'")
        if single_quotes % 2 != 0:
            self.errors.append("Syntax: Unmatched single quotes")
        
        # Check for SELECT without FROM (unless it's a simple expression)
        if re.search(r'SELECT\s+', query, re.IGNORECASE) and \
           not re.search(r'SELECT\s+.*\s+FROM\s+', query, re.IGNORECASE) and \
           not re.search(r'SELECT\s+\d+\s*$', query, re.IGNORECASE):
            # Might be valid (e.g., SELECT 1), but flag as warning
            pass
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query."""
        query_upper = query.strip().upper()
        
        if re.search(r'^\s*SELECT', query_upper):
            return 'SELECT'
        elif re.search(r'^\s*INSERT', query_upper):
            return 'INSERT'
        elif re.search(r'^\s*UPDATE', query_upper):
            return 'UPDATE'
        elif re.search(r'^\s*DELETE', query_upper):
            return 'DELETE'
        elif re.search(r'^\s*CREATE', query_upper):
            return 'CREATE'
        elif re.search(r'^\s*DROP', query_upper):
            return 'DROP'
        elif re.search(r'^\s*ALTER', query_upper):
            return 'ALTER'
        elif re.search(r'^\s*WITH', query_upper):
            return 'CTE'
        else:
            return 'OTHER'
    
    def get_summary(self, result: Dict) -> str:
        """Generate human-readable summary of validation."""
        lines = []
        
        lines.append(f"Query Type: {result['query_type']}")
        lines.append(f"Write Operation: {'Yes' if result['is_write'] else 'No'}")
        lines.append(f"Valid: {'✓' if result['is_valid'] else '✗'}")
        
        if result['errors']:
            lines.append("\nERRORS:")
            for error in result['errors']:
                lines.append(f"  ✗ {error}")
        
        if result['warnings']:
            lines.append("\nWARNINGS:")
            for warning in result['warnings']:
                lines.append(f"  ⚠ {warning}")
        
        return "\n".join(lines)


def check_batch_size(query: str, estimated_rows: int, threshold: int = 1000) -> Dict:
    """Check if operation affects too many rows."""
    validator = QueryValidator()
    is_write = validator._detect_write_operation(query)
    
    if is_write and estimated_rows > threshold:
        return {
            'is_batch': True,
            'affected_rows': estimated_rows,
            'threshold': threshold,
            'warning': f"This operation affects {estimated_rows} rows (threshold: {threshold})",
            'suggestion': "Consider adding WHERE clause or LIMIT"
        }
    
    return {
        'is_batch': False,
        'affected_rows': estimated_rows
    }


def main():
    parser = argparse.ArgumentParser(description='Validate SQL queries for safety')
    parser.add_argument('--query', '-q', required=True,
                       help='SQL query to validate')
    parser.add_argument('--strict', action='store_true',
                       help='Treat warnings as errors')
    parser.add_argument('--check-batch', action='store_true',
                       help='Check batch size implications')
    parser.add_argument('--estimated-rows', type=int, default=0,
                       help='Estimated number of rows affected')
    
    args = parser.parse_args()
    
    # Validate
    validator = QueryValidator(strict=args.strict)
    result = validator.validate(args.query)
    
    # Check batch size if requested
    if args.check_batch and args.estimated_rows > 0:
        batch_check = check_batch_size(args.query, args.estimated_rows)
        if batch_check['is_batch']:
            result['warnings'].append(batch_check['warning'])
            result['warnings'].append(f"Suggestion: {batch_check['suggestion']}")
    
    # Output
    print(validator.get_summary(result))
    
    # Exit code
    if result['errors']:
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
