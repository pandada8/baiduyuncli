import base64
import hashlib
import error

__all__ = ['GetMethod']
__MAP__ = {}


	
def register(md5):
	def wrapper(func):
		__MAP__[md5] = func
		return func
	return wrapper

def simpleMD5(content):
	return hashlib.md5(content.encode('ascii')).hexdigest()

def GetMethod(content):
	md5 = simpleMD5(content)
	if md5 in __MAP__:
		return __MAP__[md5]
	else:
		raise error.NoSuchSignFunc

@register('3427ab806a0d8de49f1576d97b806b18')
def __sign1(sign3,sign1):
	a = {}
	p = {}
	o = []
	for i in range(256):
		a[i] = ord(sign3[i % len(sign3)])
		p[i] = i
	u = 0
	for i in range(256):
		u = (u + p[i] + a[i]) % 256
		p[u],p[i] = p[i],p[u]
	j,u = 0,0
	for i in range(len(sign1)):
		j = (j + 1) % 256;
		u = (u + p[j]) % 256;
		p[u],p[j] = p[j],p[u]
		k = p[(p[j] + p[u]) % 256]
		print(k)
		o.append(ord(sign1[i]) ^ k) # 异或

	return bytes(o)
# @register(simpleMD5('test'))
# def __test():
# 	pass
# if __name__ == '__main__':
# 	print(GetMethod('test') == __test)