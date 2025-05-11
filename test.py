# ...existing code replaced with bootstrap...
from my_app import run_app, cleanup
try:
    run_app()
except KeyboardInterrupt:
    pass
finally:
    cleanup()
