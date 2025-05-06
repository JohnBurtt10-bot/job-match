# ...existing code replaced with bootstrap...
from app import run_app, cleanup
try:
    run_app()
except KeyboardInterrupt:
    pass
finally:
    cleanup()
