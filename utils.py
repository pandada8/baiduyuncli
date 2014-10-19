def shortStr(s,length):
	if length < 5:
		return ''
	if length >= len(s):
		return s
	else:
		prefix = int((length - 3)/2)
		postfix = length - prefix - 3
		return '{}...{}'.format(s[:prefix],s[-postfix:])