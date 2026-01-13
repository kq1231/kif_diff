"""Directive parameter parsing for KifDiff."""

class DirectiveParams:
    """Parse and store directive parameters."""
    def __init__(self, param_string=""):
        self.params = {}
        if param_string:
            self._parse(param_string)
    
    def _parse(self, param_string):
        """Parse parameter string like 'replace_all=true, ignore_whitespace=false'"""
        # Remove parentheses if present
        param_string = param_string.strip('()')
        if not param_string:
            return
        
        # Split by comma
        for param in param_string.split(','):
            param = param.strip()
            if '=' in param:
                key, value = param.split('=', 1)
                key = key.strip()
                value = value.strip().lower()
                
                # Convert string values to appropriate types
                if value == 'true':
                    self.params[key] = True
                elif value == 'false':
                    self.params[key] = False
                elif value.isdigit():
                    self.params[key] = int(value)
                else:
                    self.params[key] = value
    
    def get(self, key, default=None):
        """Get parameter value with default."""
        return self.params.get(key, default)