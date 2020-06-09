#!/usr/bin/python

"""
downloads osu maps
"""
import getpass
import os
import re
import requests
import sys
import time
import pickle
import progress_bar


def read_maps(maps_path):
	"""for plaintext data, now replaced with read_save"""
	maps = []
	with open(maps_path, "r") as f:
		# read until "beatmaps:" is reached
		while (line := f.readline().strip()) != "beatmaps:":
			pass
		# list of rest of file
		maps = f.readlines()
		# not very good but it works for now

	# set of ints representing map_ids
	return set(map(int, maps))


def read_save(maps_path):
	map_ids = set()
	with open(maps_path, "rb") as p:
		map_ids = pickle.load(p)["beatmaps_id"]
	return map_ids


def read_downloaded_maps(map_ids, directory):
	if not os.path.isdir(directory):
		return

	# slowly iterates through downloads directory
	for f in os.listdir(directory):
		map_id = f.split()[0]
		if not map_id.isdigit():
			continue
		map_ids.discard(int(map_id))


def request_home(s):
	return s.get("https://osu.ppy.sh/home")


def request_login(s):
	url = "https://osu.ppy.sh/session"
	data = {"username": input("username: "),
			"password": getpass.getpass(prompt="password: ")}
	# dont know why this is required
	# otherwise error 403
	headers = {"Referer": "https://osu.ppy.sh/home"}

	return s.post(url, data=data, headers=headers)


def check_quota(s):
	# unused function; quota does not work like this
	# https://osu.ppy.sh/beatmapsets/814033#osu/1714827
	try:
		q = s.get("https://osu.ppy.sh/home/download-quota-check")
		return q.json()["quota_used"]
	except:
		return 0


def download_maps(s, map_ids, directory, maximum=170, wait_per_5=60):
	# progress[0] : number of maps downloaded
	# progress[1] : total amount of maps to download
	progress = [0, min(len(map_ids), maximum)]
	print(f"downloading {progress[1]} maps")

	for map_id in map_ids:
		quota = check_quota(s)

		progress[0] += 1
		prefix = f"d: {progress[0]}"
		progress_bar.print_progress_bar(*progress, prefix=prefix)
		if progress[0] >= progress[1]: break

		# https://github.com/Piotrekol/CollectionManager/issues/15
		# throttle downloads
		if progress[0] % 5 == 0:
			print(f"\r{prefix} | waiting {wait_per_5}s |", end="\r")
			time.sleep(wait_per_5)

		if not download_map(s, map_id, directory):
			print(f"\nmap {map_id} does not exist")
			os.mkdir(f"{directory}{os.path.sep}{map_id}")


def download_map(s, map_id, d):
	# try bancho first
	# if bancho fails, then try bloodcat
	return bancho_download(s, map_id, d) or bloodcat_download(s, map_id, d)


def get_map_name(string):
	regex = "filename\\s*=\\s*[\"'](.*)[\"'];"
	result = re.search(regex, string)
	if not result: return ""
	return result.group(1)


def write_map(d, filename, content):
	# https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
	# replace illegal characters with space for windows
	name = re.sub('["*/:><?\\\|]', " ", filename)
	with open(f"{d}{os.path.sep}{name}", "wb") as f:
		f.write(content)


def bancho_download(s, map_id, d):
	url = f"https://osu.ppy.sh/beatmapsets/{map_id}/download"
	
	# still dont know why this is required
	headers = {"Referer": f"https://osu.ppy.sh/beatmapsets/{map_id}"}
	
	download = s.get(url, headers=headers)
	# copyrighted songs will give code 404, so (download.ok == False)
	if not download.ok or "Content-Disposition" not in download.headers:
		return False

	filename = get_map_name(download.headers["Content-Disposition"])
	if not filename: return False

	write_map(d, filename, download.content)
	return True


def bloodcat_download(s, map_id, d):
	url = f"https://bloodcat.com/osu/s/{map_id}"
	
	download = s.get(url)

	# if map does not exist
	# then (download.content == b"* File not found or inaccessible!")
	if (not len(download.content) > 40 or 
		"Content-Disposition" not in download.headers):
		return False

	# bloodcat gives quoted filename; must unquote
	filename = requests.utils.unquote(
		get_map_name(download.headers["Content-Disposition"]))
	if not filename: return False

	write_map(d, filename, download.content)
	return True


def main(maps_path, directory, downloaded_maps_path):
	map_ids = read_save(maps_path) - read_save(downloaded_maps_path)
	read_downloaded_maps(map_ids, directory)

	with requests.session() as s:
		home = request_home(s)
		if not home.ok or "XSRF-TOKEN" not in home.cookies:
			print(f"Error: status code {home.status_code}")
			s.close()
			return

		login = request_login(s)
		if not login.ok:
			print(f"Error: status code {login.status_code}")
			s.close()
			return

		download_maps(s, map_ids, directory, maximum=5000)


if __name__ == "__main__":
	if len(sys.argv) > 1 and "--help" in sys.argv:
		print("download_maps.py <undownloaded_maps_path> <downloads_directory> <downloaded_maps_path>")
	else:
		maps_path = sys.argv[1] if len(sys.argv) > 1 else "data"
		directory = sys.argv[2] if len(sys.argv) > 2 else "songs"
		downloaded_maps_path = sys.argv[3] if len(sys.argv) > 3 else ""
		main(maps_path, directory, downloaded_maps_path)
