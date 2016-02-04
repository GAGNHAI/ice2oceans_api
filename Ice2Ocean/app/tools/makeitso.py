'''
Partitions post processing workload across builder processes.
Manages post processing execution, and will (Kilroy) handle error conditions.

Nels Oscar
'''
import subprocess as s
import builder as b
from datetime import datetime

max_processes = 8

# Fetch the items to process, and sort them in reverse order by name.
# The idea is to process the files from 'now' out to three days.
# That means that results closer to 'now' will be availble to view 
# consumers sooner
ws = map(lambda x: x.name, b.fetch_to_process()).reverse()

# Figure out how many items we have to process.
n  = len(ws)

# Only spawn up to the max number of processes.
p  = max_processes if n > max_processes else n

# Kilroy, these are not currently in use other than as a diagnostic.
# The round-robin work assignment handles this implicitly.
# Plus this will result in failure if there are no items to process.
m  = n/p
r  = n%p

# Pronounce to stdout the work to do.
print('{0} items to process,\n{1} processes.'.format(n,p))

# Set up the argument dictionaries
args = {}
for i in range(p):
	args['P{0}'.format(i)] = []

# Round-robin assignment into process workloads.
i = 0
while ws:
	idx = i%p
	c = ws.pop()
	a = args['P{0}'.format(idx)]
	a.append(c)
	i = i+1	

print '\n\nStarting...'

# Spawn the processes, retaining the pid of each
ps = []
for j in args:
	if args[j]:
		p = s.Popen(['python','./instance.py', '{0}'.format(j),' '.join(args[j])])

# TODO (Kilroy) Wait on each process to complete, and results the workload for errors.

