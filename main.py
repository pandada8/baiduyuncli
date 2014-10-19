from api import api,downloader
import sys
import re
import os
import getpass
import error
import utils
COMMANDS = {}

def register(command):
	def wrapper(func):
		COMMANDS[re.compile(command)] = func
		return func
	return wrapper

def find_match(command):
	ret = []
	for i,j in COMMANDS.items():
		if i.search(command):
			ret.append((len(i.search(command).group()),j))
	# print(ret)
	if not ret:
		raise error.BadCommand
	return sorted(ret,key=lambda x:x[0])[-1][1]




@register('help')
@register('-h')
def usage(foo=None):
	print('Too lazy to write a help')

@register(r'down ([\w\W]+?)+')
def down(command):
	if not api.checkLogin():
		print('You should login first')
		login('login')
	command = command[1:]
	ids = []
	for i in command:
		path,filename = os.path.split(i)
		ret =[(f['fs_id'],filename) for f in api.getFileList(path) if f['server_filename'] == filename and not f['isdir']]
		if ret:
			ids.extend(ret)
		else:
			print('Get {} info failed'.format(utils.shortStr(i,25)))
	links = [(ids[i],j) for i,j in  api.getFilesLink(i[0] for i in ids)]
	downloader.download(links)


@register('login')
def login(command):
	if api.checkLogin():
		return
	username = input('Username:')
	password = getpass.getpass()
	print('logining, please wait for a while....')
	try:
		api.login(username, password)
	except error.ApiError:
		print('Login Failed! Check your username & password please.')
def main():
	if len(sys.argv) < 2:
		usage()
		sys.exit()
	command = ' '.join(sys.argv[1:])
	try:
		find_match(command)(sys.argv[1:])
		api.syncCookie()
		api.storeConfig()
	except error.BadCommand:
		print('Bad Command,plz look the help')
		usage()
if __name__ == '__main__':
	main()
