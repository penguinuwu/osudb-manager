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
import progress_bar


def read_maps(maps_path):
	maps = []
	with open(maps_path, "r") as f:
		while (line := f.readline().strip()) != "beatmaps:":
			pass
		maps = f.readlines()
	return map(int, maps)


def read_downloaded_maps(map_ids, directory):
	for f in os.listdir(directory):
		map_id = f.split()[0]
		if not isdigit(map_id):
			continuecommit 
		map_ids.remove(int(map_id))


def request_home(s):
	return s.get("https://osu.ppy.sh/home")


def request_login(s, token):
	url = "https://osu.ppy.sh/session"
	data = {"_token": token,
		"username": input("username: "),
		"password": getpass.getpass(prompt="password: "),
		}

	# dont know why this is required
	# otherwise error 403
	headers = {"Referer": "https://osu.ppy.sh/home"}

	return s.post(url, data=data, headers=headers)


def check_quota(s):
	try:
		q = s.get("https://osu.ppy.sh/home/download-quota-check")
		return q.json()["quota_used"]
	except:
		return 0


def download_maps(s, map_ids, directory):
	progress = [0, len(map_ids)]
	for map_id in map_ids:
		progress[0] += 1
		progress_bar.print_progress_bar(*progress)
		while not check_quota(s) > 0:
			time.sleep(2)
		download_map(s, map_id, directory)


def download_map(s, map_id, d):
	return bancho_download(s, map_id, d) or bloodcat_download(s, map_id, d)


def bancho_download(s, map_id, d):
	# still dont know why this is required
	url = f"https://osu.ppy.sh/beatmapsets/{map_id}/download"
	headers = {"Referer": f"https://osu.ppy.sh/beatmapsets/{map_id}"}
	download = s.get(url, headers=headers)
	if not download.ok or "Content-Disposition" not in download.headers:
		return False

	regex = "filename\\s*=\\s*\"(.*)\""
	result = re.search(regex, download.headers["Content-Disposition"])
	if not result:
		return False

	with open(f"{d}{os.path.sep}{result.group(1)}", "wb") as f:
		f.write(download.content)
	return True


def bloodcat_download(s, map_id, d):
	url = f"https://bloodcat.com/osu/s/{map_id}"
	download = s.get(url)

	if not len(download.content) > 330:
		print(f"map {map_id} does not exist")
		return False

	with open(f"{d}{os.path.sep}{lines[i].rstrip()}.osz", "wb") as f:
		f.write(download.content)
	return True


def main(maps_path, directory):
	with requests.session() as s:
		home = request_home(s)
		if not home.ok or "XSRF-TOKEN" not in home.cookies:
			print(f"Error: status code {home.status_code}")
			s.close()
			return

		login = request_login(s, home.cookies["XSRF-TOKEN"])
		if not home.ok or "XSRF-TOKEN" not in home.cookies:
			print(f"Error: status code {login.status_code}")
			s.close()
			return

		map_ids = read_maps(maps_path, directory)
		read_downloaded_maps(map_ids, directory)
		download_maps(s, map_ids)


if __name__ == "__main__":
	maps_path = sys.argv[1] if len(sys.argv) > 1 else "data"
	directory = sys.argv[2] if len(sys.argv) > 2 else "songs"
	main(maps_path, directory)
