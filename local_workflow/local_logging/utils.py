import yaml, json
import os, shutil, hashlib, datetime
import logging

def setup_trace_level():
    """Add TRACE logging level at 15 (between DEBUG and INFO)"""
    TRACE_LEVEL = 15
    
    # Check if already exists
    if hasattr(logging, 'TRACE'):
        return
    
    # Add the level name
    logging.addLevelName(TRACE_LEVEL, 'TRACE')
    
    # Add method to Logger class
    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, message, args, **kwargs)
    
    # Add method to logging module
    def trace_root(message, *args, **kwargs):
        logging.log(TRACE_LEVEL, message, *args, **kwargs)
    
    # Set attributes
    setattr(logging, 'TRACE', TRACE_LEVEL)
    setattr(logging.getLoggerClass(), 'trace', trace)
    setattr(logging, 'trace', trace_root)

def configure_logging(level=logging.INFO, **kwargs):
    """Configure logging with basicConfig and setup trace level"""
    setup_trace_level()
    
    # Handle string level names including 'TRACE'
    if isinstance(level, str):
        level = level.upper()
        if level == 'TRACE':
            level = logging.TRACE
        else:
            level = getattr(logging, level)
    
    logging.basicConfig(level=level, **kwargs)

def get_logger(name=None):
    """Get a logger with trace level configured"""
    setup_trace_level()
    return logging.getLogger(name)

logger = get_logger(__name__)

def setup_logs(config_file: str, location: str = "runs") -> str:
    with open(config_file, 'r') as infile:
        config = yaml.safe_load(infile)
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H:%M:%S")
    run_name = f"{timestamp}_{hashlib.md5(json.dumps(config).encode()).hexdigest()}"
    logger.info(f"Run name: {run_name}")
    if not os.path.exists(location):
        os.makedirs(location)
    run_dir = f"{location}/{run_name}"
    os.makedirs(run_dir)
    shutil.copy(config_file, f"{run_dir}/config.yaml")
    results_path = f"{run_dir}/results.jsonl" 
    return config, results_path