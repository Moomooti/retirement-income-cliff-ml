import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('ENABLE_PREDICT', '1')
os.environ.setdefault('ALLOWED_ORIGINS', 'https://mirinohulab.github.io')
os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key-not-real')
