import threading
from collections import defaultdict

class RequestMetrics:
    def __init__(self):
        self.lock=threading.Lock();self.counts=defaultdict(int);self.latency=defaultdict(float)
    def record(self,method:str,route:str,status:int,seconds:float):
        key=(method,route,status)
        with self.lock:
            self.counts[key]+=1;self.latency[key]+=seconds
    def prometheus(self)->str:
        with self.lock:
            counts=dict(self.counts);latencies=dict(self.latency)
        lines=["# HELP finintel_http_requests_total Completed HTTP requests","# TYPE finintel_http_requests_total counter"]
        for (method,route,status),count in sorted(counts.items()):
            safe=route.replace('"','')
            lines.append(f'finintel_http_requests_total{{method="{method}",route="{safe}",status="{status}"}} {count}')
        lines.extend(["# HELP finintel_http_request_duration_seconds_total Total request duration in seconds","# TYPE finintel_http_request_duration_seconds_total counter"])
        for (method,route,status),seconds in sorted(latencies.items()):
            safe=route.replace('"','')
            lines.append(f'finintel_http_request_duration_seconds_total{{method="{method}",route="{safe}",status="{status}"}} {seconds:.6f}')
        return "\n".join(lines)+"\n"

metrics=RequestMetrics()
