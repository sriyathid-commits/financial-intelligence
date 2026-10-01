import json, logging, sys
from datetime import datetime, timezone
class JsonFormatter(logging.Formatter):
    def format(self,record):
        return json.dumps({"timestamp":datetime.now(timezone.utc).isoformat(),"level":record.levelname,"logger":record.name,"message":record.getMessage()},ensure_ascii=False)
def configure_logging():
    handler=logging.StreamHandler(sys.stdout);handler.setFormatter(JsonFormatter())
    root=logging.getLogger();root.handlers.clear();root.addHandler(handler);root.setLevel(logging.INFO)
