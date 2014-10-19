class ApiError(Exception):
    def __init__(self,info):
    	self.info = info
    def __str__(self):
    	return str(self.info)
class BadCommand(Exception):
	pass
class NoSuchSignFunc(Exception):
	pass