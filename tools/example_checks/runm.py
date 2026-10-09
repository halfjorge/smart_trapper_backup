import subprocess,sys,time,resource
t=time.time(); p=subprocess.run(sys.argv[2:],capture_output=True,text=True)
ru=resource.getrusage(resource.RUSAGE_CHILDREN)
print(f"{sys.argv[1]}: {time.time()-t:.1f}s, peak memory {ru.ru_maxrss/1024:.0f} MB, exit {p.returncode}")
print(p.stdout[-1500:], p.stderr[-800:])
