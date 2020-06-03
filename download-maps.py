#!/usr/bin/python

"""
downloads osu maps
"""
import os
import requests
import sys


def read_maps(path):
	maps = []
	with open(path, "r") as f:
		while (line := f.readline().strip()) != "beatmaps:":
			pass
		maps = f.readlines()
	return list(map(int, maps))


def download_maps(maps):
	for m in maps:
		pass


def main():
	print(sys.argv)
	path = sys.argv[1] if len(sys.argv) > 1 else "data"
	maps = read_maps(path)
	download_maps(maps)


if __name__ == "__main__":
	main()
