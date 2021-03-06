from webfinger import WebFinger
from webdav import WebDAV
import urllib

class remoteStorage:
	def __init__(self):
		self.storage_info = None

	def get_storage_info(self, user_address):
		self.storage_info = WebFinger(user_address).finger()
		return self.storage_info

	def create_oauth_address(self, scopes, redirect_uri):
		if self.storage_info.type == 'https://www.w3.org/community/rww/wiki/read-write-web-00#simple':
			scopes_str = ' '.join(scopes)
		else:
			scopes_str = ','.join([scope.split(':')[0].split('/')[0] for scope in scopes])

		host_and_rest = redirect_uri[redirect_uri.find('://')+3:]
		host = host_and_rest.split(':')[0].split('/')[0]

		attrs = [
			'redirect_uri='+urllib.quote_plus(redirect_uri),
			'scope='+urllib.quote_plus(scopes_str),
			'response_type=token',
			'client_id='+urllib.quote_plus(host)
		]
		authHref = self.storage_info.properties['http://oauth.net/core/1.0/endpoint/request']

		return authHref+("?" if authHref.find('?') == -1 else "&")+'&'.join(attrs)

	def create_client(self, category, token=None):
		return remoteStorageClient(self.storage_info, category, token)

class remoteStorageClient:
	def __init__(self, storage_info, path, token=None):
		self.storage_info = storage_info
		self.path = path
		self.token = token
		self.driver = self.get_driver()

	def resolve_key(self, rel_path):
		item_path_parts = ((self.path+'/' if self.path else '')+rel_path).split('/')
		item = '_'.join(item_path_parts[1:])
		return self.storage_info.href + '/' + item_path_parts[0] + self.storage_info.properties.get('legacy_suffix', '') + '/' + ('u' if item[0] == '_' else '') + item

	def get_driver(self):
		if self.storage_info.type == 'https://www.w3.org/community/unhosted/wiki/remotestorage-2011.10#webdav':
			return WebDAV()

	def get(self, key):
		return self.driver.get(self.resolve_key(key), self.token)

	def put(self, key, value):
		return self.driver.put(self.resolve_key(key), value, self.token)

	def delete(self, key):
		return self.driver.delete(self.resolve_key(key), self.token)

if __name__ == "__main__":
	# Example usage

	# Create an instance of remoteStorage
	rs = remoteStorage()
	# Get the storage info
	rs.get_storage_info('lukashed@owncube.com')

	# Gets you an oauth address like https://owncube.com/apps/remoteStorage/auth.php/lukashed?redirect_uri=http%3A%2F%2Flukasklein.com%2F&scope=remoteStorage.py&response_type=token&client_id=lukasklein.com
	# The scope specifies the categories that you want to access, the redirect uri can basically be any URL, that's the bad part about
	# remoteStorage.py. You have to manually copy that address to your browser and then copy the generated bearer token from the redirect
	# URI. Do you have any suggestions on how to make this better?
	print rs.create_oauth_address(['remoteStorage.py'], 'http://lukasklein.com/')

	# Creates a client instance for the given category. Token is optional, but if you need write access it's obviously compulsory.
	cl = rs.create_client('remoteStorage.py', 'thebearertoken')
	# Puts some data
	cl.put('test', 'This is just a Test.')
	# And gets it again
	print cl.get('test')