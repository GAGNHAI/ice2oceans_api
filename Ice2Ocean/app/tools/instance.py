'''
A worker instance for processing 
Parker's NetCDF files from blob storage.
'''

import sys
import subprocess
import builder as b

# Process label
iam  = sys.argv[1]
# Work items to handle
todo = sys.argv[2].split()

print '{0} is working on: {1}'.format(iam,sys.argv[2])

for t in todo:
	print '{0} started {1}'.format(iam,t)

	# Mark the file as started
	try:
		b.label_in_process(t)
	except Exception as e:
		m = 'Unable to label as started.'
		m = '{0} on {1}: {2} More details: {3}'.format(iam, t, m, e)
		print m
		b._label(t,'Error',msg=m)
		continue
	
	# Construct images of the depth slices
	# for each parameter with a geotemporal index.
	try:
		# b.depth_slice(t)
		print 'Constructing inversion layers from {0}...'.format(t)
		b.inversion_aggregate(t)
	except Exception as e:
		m = 'Generating depth slices failed.'
		m = '{0} on {1}: {2} More details: {3}'.format(iam, t, m, e)
		print m
		b._label(t,'Error', msg=m)
		continue
	
	# # Push the surface geotemporal parameters
	# # into an azure table for point/vector/grid
	# # lookups
	# try:
	# 	b.table_builder(t)python
	# except Exception as e:
	# 	m = 'Failed to process the surface table.'
	# 	m = '{0} on {1}: {2} More details: {3}'.format(iam, t, m, e)
	# 	print m
	# 	b._label(t,'Error', msg=m)
	# 	continue
	
	# Label the file processed and handle the next
	try:
		b.label_processed(t)
	except Exception as e:
		m = 'Unable to label completed.'
		m = '{0} on {1}: {2} More details: {3}'.format(iam, t, m, e)
		print m
		b._label(t,'Error',msg=m)
		continue
	
	print '{0} finished {1}'.format(iam, t)
