#!/usr/bin/python

"""
This script parses through two pickle files outputted by read_db.py and downloads the difference.
For the two pickle scripts, one is converted from an old osu!.db with maps you wish to recover, 
and another from your current osu!.db make sure no duplicate maps are downloaded.

Usage:

	download_maps.py <path to reference_db_pickle> <path to current_db_pickle> <Path to download songs to (use '<path to osu!>\Songs' for convienience)

Example:

	python download_maps.py D:\Documents\old.pickle D:\osu!\Songs D:\Documents\current.pickle D:\osu!\Songs

For further information, use the -h or --help flag

WARNING:

	Setting a timeout of lower than 60s will likely result in the osu website blocking your downloads. In which case, please wait until unblocked before re-running the script.
	This can be checked by attempting to download maps manually form the website.

	This program also caps the number of maps to be downloaded in any 1 run to 3000

"""
import getpass
import os
import re
import requests
# import sys
import time
import pickle
import progress_bar
import argparse

global_timeout = 60
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
		raise Exception("Directory does not exist")

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
	data = {"_token": s.cookies["XSRF-TOKEN"],
            "username": input("username: "),
            "password": getpass.getpass(prompt="password: ")}
	# dont know why this is required
	# otherwise error 403
	headers = {"Referer": "https://osu.ppy.sh/home", "Origin": "https://osu.ppy.sh"}

	return s.post(url, data=data, headers=headers)


def check_quota(s):
	# unused function; quota does not work like this
	# https://osu.ppy.sh/beatmapsets/814033#osu/1714827
	try:
		q = s.get("https://osu.ppy.sh/home/download-quota-check")
		return q.json()["quota_used"]
	except:
		return 0


def download_maps(s, map_ids, directory, maximum=170):
	# progress[0] : number of maps downloaded
	# progress[1] : total amount of maps to download
	progress = [0, min(len(map_ids), maximum)]
	print(f"Number of maps to be downloaded: {progress[1]}")

	for map_id in map_ids:
		# quota = check_quota(s)
		progress[0] += 1
		prefix = f"m: {map_id} d: {progress[0]}"

		# https://github.com/Piotrekol/CollectionManager/issues/15
		# throttle downloads
		if progress[0] % 5 == 0:
			print(f"\r{prefix} | waiting {timeout}s |", end="\r")
			time.sleep(timeout)

		progress_bar.print_progress_bar(*progress, prefix=prefix)
		if progress[0] >= progress[1]: break

		dl_map_status = download_map(s, map_id, directory)

		if not dl_map_status:
			print(f"\nMap ID: {map_id} cannot be found")


def download_map(s, map_id, d):
	# try bancho first
	# if bancho fails, then try bloodcat
	return bancho_download(s, map_id, d) or bloodcat_download(s, map_id, d)


def get_map_name(string):
	# regex = "filename\\s*=\\s*[\"'](.*)[\"'];"
	# result = re.search(regex, string)
	result = re.findall(r'"(.*?)"', string)
	if not result: return ""
	return result[0]


def write_map(d, filename, content):
	# https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file
	# replace illegal characters with space for windows
	print(f"Downloading {filename}")
	name = re.sub('["*/:><?\\\|]', " ", filename)
	with open(f"{d}{os.path.sep}{name}", "wb") as f:
		f.write(content)


def bancho_download(session, map_id, d):
	url = f"https://osu.ppy.sh/beatmapsets/{map_id}/download"
	
	# still dont know why this is required
	headers = {"Referer": f"https://osu.ppy.sh/beatmapsets/{map_id}"
	    		,"Path":  f"/beatmapsets/{map_id}/download"}

	download = session.get(url, headers=headers)

	if download.status_code == 429:
		raise(Exception("Error: Rate limited. Please wait before re-running program."))
	# copyrighted songs will give code 404, so (download.ok == False)
	if not download.ok or "Content-Disposition" not in download.headers:
		return False

	filename = get_map_name(download.headers["Content-Disposition"])
	if not filename: return False

	write_map(d, filename, download.content)
	return True


def bloodcat_download(s, map_id, d):
	return False
	# url = f"https://bloodcat.com/osu/s/{map_id}"
	
	# download = s.get(url)

	# # if map does not exist
	# # then (download.content == b"* File not found or inaccessible!")
	# if (not len(download.content) > 40 or 
	# 	"Content-Disposition" not in download.headers):
	# 	return False

	# # bloodcat gives quoted filename; must unquote
	# filename = requests.utils.unquote(
	# 	get_map_name(download.headers["Content-Disposition"]))
	# if not filename: return False

	# write_map(d, filename, download.content)
	# return True


def main(maps_path, directory, downloaded_maps_path):
	map_ids = read_save(maps_path) - read_save(downloaded_maps_path)
	read_downloaded_maps(map_ids, directory)
	print("Number of map IDs: " + str(len(map_ids)))

	with requests.session() as req:
		home = request_home(req)
		if not home.ok or "XSRF-TOKEN" not in home.cookies:
			print(f"HomeError: status code {home.status_code}")
			req.close()
			return

		login = request_login(req)
		if not login.ok:
			print(f"Login Error: status code {login.status_code}")
			req.close()
			return

		download_maps(req, map_ids, directory, maximum=3000)


def parse_args():
	parser = argparse.ArgumentParser(description='Download osu files based on difference of given pickle files')

	parser.add_argument("reference_pickl", type=str, help="Path to pickle file for maps to be downloaded", default="data")
	parser.add_argument("current_pickl",help="Path to pickle file for maps already owned", default="")
	parser.add_argument("downloads_dir", type=str, help="Path to where files will be downloaded (path to osu!\Songs)", default="D:\osu!\Songs")
	parser.add_argument("--timeout", type=int, help="Duration to wait inbetween downloading every 5 maps", default=60)
	args = parser.parse_args()
	return args.reference_pickl, args.downloads_dir, args.current_pickl, args.timeout

if __name__ == "__main__":

	reference_pickl, downloads_dir, current_pickl, timeout = parse_args()
	global_timeout = timeout
	main(reference_pickl, downloads_dir, current_pickl)
