
import re
import pandas as pd
from collections import defaultdict
import time
import os
import sys
from optparse import OptionParser


def date_to_epoch(timestamp):
	'''Given timestamp of the form DD/Mon/YYYY:HH:MM:SS return corresponding epoch time.'''
	return int(time.mktime(time.strptime(timestamp,'%d/%b/%Y:%H:%M:%S')))


def epoch_to_date(epoch):
	'''Given epoch time returns a timestamp of the form DD/Mon/YYYY:HH:MM:SS'''
	return time.strftime('%d/%b/%Y:%H:%M:%S', time.localtime(epoch))


def top_items(dictionary, k):
	'''Return list of tuples with largest k items from the values of dictionary.'''
	# Pandas implementation performs slightly faster than a python+numpy
	# QuickSelect implementation to find the kth largest element
	# and return elements >= kth largest element ( O(n) time on average).
	# We opt to use the pandas library for better performance.
	dict_series = pd.Series(dictionary.values())
	indices = dict_series.nlargest(k).index.tolist()
	top_items = [(dictionary.keys()[i], dictionary.values()[i]) for i in indices]
	return top_items


def calculate_intervals(act_dict, window_size):
	'''Return dictionary with values being total number of visits in a moving 
	window and key being the start time of the window_size interval'''
	intervals = defaultdict(int)
	start_time = sorted(act_dict.keys())[0]
	end_time = sorted(act_dict.keys())[-1]
	# The first interval is the sum of first window_size or all values in
	# the dictionary (if less than window_size)
	i = start_time
	while i < start_time + window_size and i < end_time + 1:
		intervals[start_time] += act_dict[i]
		i += 1
	# Queue structure subtracts oldest activity and adds newest activity to interval
	for clock in xrange(start_time + 1, end_time + 1):
		intervals[clock] = intervals[clock - 1] - act_dict[clock - 1] + act_dict[clock + window_size]

	return intervals


def top_intervals_nooverlap(intervals, window_size):
	'''Returns a list with the 10 most active window_size periods that do not overlap.'''
	top_times = [('', 0)]*10
	values = intervals.values()
	keys = intervals.keys()
	if len(intervals) < 2*window_size*10:
		print 'Not enough data for 10 non-overlapping windows of size {}s.'.format(window_size)
	else:
		for i in range(10):
			max_visits = max(values)
			start_interval = values.index(max_visits)
			end_interval = start_interval + window_size
			top_times[i] = (keys[start_interval], max_visits)
			#Remove window and its contributions to neighboring window from lists
			del values[start_interval: end_interval + 3600], keys[start_interval: end_interval + 3600]

	return top_times

def main(logfile, hostfile, hourfile, resfile, blockfile,  no_overlap = False, print_time_elapsed = False):

	#Regular expression pattern used to split input string of the form: 'host - - [timestamp] "request" reply num_bytes'
	#into corresponding list: [host, timestamp, request, reply, bytes]

	line_pattern = '(.*?) - - \[(.*?)\] \"(.*?)\" (\d*?) (.*)'
	resource_pattern_full = '\w*\s(.*?)\s.*'
	resource_pattern_partial = '\w*\s(.*)'

	line_regex = re.compile(line_pattern)
	resource_full_regex = re.compile(resource_pattern_full)
	resource_partial_regex = re.compile(resource_pattern_partial)

	buf_size = 1024
	cur_time = int()
	date = str()

	host_dict = defaultdict(int)
	bw_dict = defaultdict(int)
	activity_dict = defaultdict(int)

	BLOCK_WINDOW = 300
	LOGIN_WINDOW = 20
	#List indices for blocked_dict
	LOGIN_COUNT = 0
	OLD_TIME = 1
	TIME_LEFT = 2
	DO_LOG = 3
	blocked_dict = defaultdict(lambda:[0, 0, LOGIN_WINDOW, False]) # login attempt counter,  past timestamp, time left, log?

	buffer_blocked_log = ['']*buf_size
	blocked_log = list()
	last_date = ''
	extend_logs = False
	blocked_log_index = 0

	with open(logfile, 'r') as log_file, \
		open(hostfile, 'w') as hosts_file, \
		open(resfile, 'w') as res_file, \
		open(hourfile, 'w') as hour_file, \
		open(blockfile, 'w') as block_file:

		read_lines = log_file.readlines
		buf = read_lines(buf_size)
		
		t_0 = time.time()

		while buf:
			for i, line in enumerate(buf):

				data = line_regex.match(line).groups()

				host, timestamp, request, reply, num_bytes = data[0], data[1][:20], data[2], data[3], data[4]

				#Timestamp parsing to epoch is slow, so only do it when needed
				if timestamp != last_date:
					cur_time = date_to_epoch(timestamp)

				last_date = timestamp

				#Count visits from host
				host_dict[host] += 1

				#Count bytes transferred for a resource. Additional request parsing needed for 'full' 
				# requests, eg 'GET resource HTTP/1.0' and 'partial' eg 'GET resource'
				if num_bytes.isdigit():
					result = resource_full_regex.match(request)
					if result:
						resource = result.groups()[0]
					else:
						result = resource_partial_regex.match(request)
						resource = result.groups()[0]
					bw_dict[resource] += int(num_bytes)
					
				#Count visits for a given time
				activity_dict[cur_time] += 1

				#If a given hostname fails a login (304 or 401 HTTP reply) 3 times in a 20 second window (LOGIN_WINDOW)
				#all activity from the host is logged in buffer_blocked_log for 5 minutes (BLOCK_WINDOW).				
				if blocked_dict[host][DO_LOG]:	
					if (cur_time - blocked_dict[host][OLD_TIME]) < BLOCK_WINDOW:

						buffer_blocked_log[blocked_log_index] = line
						blocked_log_index += 1
						# Extend log list if number of logs exceeds the pre-defined size
						if blocked_log_index == buf_size - 1:
							extend_logs = True
					else:
						blocked_dict[host][DO_LOG] = False
				else:
					if int(reply) in [304, 401]:
						if blocked_dict[host][OLD_TIME] == 0:
							blocked_dict[host][OLD_TIME] = cur_time
						#Count failed login attempts within login window or reset
						if blocked_dict[host][TIME_LEFT] >= 0:
							blocked_dict[host][LOGIN_COUNT] += 1
							blocked_dict[host][TIME_LEFT] -= (cur_time - blocked_dict[host][OLD_TIME])
						else:
							blocked_dict[host][LOGIN_COUNT] = 0
							blocked_dict[host][TIME_LEFT] = 20

						blocked_dict[host][OLD_TIME] = cur_time

						#Begin logging after 3 failed attempts
						if blocked_dict[host][LOGIN_COUNT] == 3:
							blocked_dict[host][DO_LOG] = True

				if extend_logs:
					blocked_log.extend(buffer_blocked_log[:blocked_log_index])
					extend_logs = False
					blocked_log_index = 0

			buf = read_lines(buf_size)

		t_1 = time.time()
		#Compute Features 1, 2, and 3
		top_visits = top_items(host_dict, 10)
		top_bw = top_items(bw_dict, 10)
		intervals = calculate_intervals(activity_dict, 3600)
		if no_overlap:
			top_times = top_intervals_nooverlap(intervals, 3600)
		else:
			top_times = top_items(intervals, 10)

		t_2 = time.time()

		#Write features 1, 2, 3, and 4 to seperate text files
		hosts_file.write('\n'.join('{},{}'.format(x[0].strip(), x[1]) for x in top_visits))
		hosts_file.write('\n')

		res_file.write('\n'.join(y[0] for y in top_bw))
		res_file.write('\n')

		hour_file.write('\n'.join('{},{}'.format(epoch_to_date(x[0]) + ' -0400', x[1]) for x in top_times))
		hour_file.write('\n')

		if len(blocked_log) > 0:
			block_file.write(''.join(x for x in blocked_log))
		else:
			block_file.write(''.join(x for x in buffer_blocked_log))

	t_3 = time.time()

	if print_time_elapsed:
		print "File processed in {}s".format(t_1 - t_0)
		print "Features 1, 2, 3 computed in {}s".format(t_2 - t_1)
		print "Features 1, 2, 3, 4 written to file in {}s".format(t_3 - t_2)

if __name__ == '__main__':

	parser = OptionParser()
	parser.add_option('-n', action = "store_true", default = False, dest = "no_overlap")
	parser.add_option('-t',action = "store_true", default = False, dest = "print_elapsed_time")	
	(options, args) = parser.parse_args()
	num_args = len(sys.argv)

	if num_args < 6:
		print 'Need input file log.txt, and output files hosts.txt, resources.txt, hours.txt, blocked.txt as arguments to continue.'
		exit()

	main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], options.no_overlap, options.print_elapsed_time)