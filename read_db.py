#!/usr/bin/python
"""
This script parses through an osu!.db database file and converts it into a pickle file to be used in download_maps.py

Usage:

	read_db.py <path to osu!.db file> <Location of the output file (including name)>

Example:

	read_db.py D:\Apps\osu!\osu!.db D:\Documents\data\osu_pickle

For further information, use the -h or --help flag

"""
import os
import pickle
import progress_bar
import argparse


def read_byte(f):
	return f.read(1)


def read_number(f, byte):
	return int.from_bytes(f.read(byte), byteorder="little", signed=False)


def read_short(f):
	return read_number(f, 2)


def read_int(f):
	return read_number(f, 4)


def read_long(f):
	return read_number(f, 8)


def decode_uleb128(f):
	result = 0
	shift = 0
	while b := ord(read_byte(f)):
		result |= (b & 0x7f) << shift
		if not b & 0x80: break
		shift += 7
	return result


def read_single(f):
	# TODO: write this
	f.read(4)
	return None


def read_double(f):
	# TODO: write this
	f.read(8)
	return None


def read_boolean(f):
	return read_byte(f) != b'\x00'


def read_string(f):
	if read_byte(f) != b'\x0b': return None
	length = decode_uleb128(f)
	if length <= 0: return None
	return str(f.read(length), encoding="utf-8")


def read_int_double_pair(f):
	# TODO: write this
	f.read(14)
	return None


def read_timing_point(f):
	# TODO: write this
	f.read(17)
	return None


def read_date_time(f):
	x = read_long(f)
	return x
	#print(x)
	#return datetime.datetime.fromtimestamp(x / 1e7)


def read_beatmap(f, osu_version):
	return {
		"size": read_int(f) if (osu_version < 20191106) else None,
		"artist_name": read_string(f),
		"artist_name_unicode": read_string(f),
		"song_title": read_string(f),
		"song_title_unicode": read_string(f),
		"creator_name": read_string(f),
		"difficulty": read_string(f),
		"audio_name": read_string(f),
		"map_MD5_hash": read_string(f),
		"name_of_map": read_string(f),
		"rank_status": read_byte(f),
		"hitcircles": read_short(f),
		"sliders": read_short(f),
		"spinners": read_short(f),
		"last_modification": read_long(f),
		"AR": read_byte(f) if (osu_version < 20191106) else read_single(f),
		"CS": read_byte(f) if (osu_version < 20191106) else read_single(f),
		"HP": read_byte(f) if (osu_version < 20191106) else read_single(f),
		"OD": read_byte(f) if (osu_version < 20191106) else read_single(f),
		"slider_velocity": read_double(f),
		"S_stars": None if (osu_version < 20140609) else 
			[read_int_double_pair(f) for i in range(read_int(f))],
		"T_stars": None if (osu_version < 20140609) else 
			[read_int_double_pair(f) for i in range(read_int(f))],
		"C_stars": None if (osu_version < 20140609) else 
			[read_int_double_pair(f) for i in range(read_int(f))],
		"M_stars": None if (osu_version < 20140609) else 
			[read_int_double_pair(f) for i in range(read_int(f))],
		"drain_time": read_int(f),
		"total_time": read_int(f),
		"preview_time": read_int(f),
		"timing_points": 
			[read_timing_point(f) for i in range(read_int(f))],
		"beatmap_ID": read_int(f),
		"beatmap_set_ID": read_int(f),
		"beatmap_thread_ID": read_int(f),
		"S_grade": read_byte(f),
		"T_grade": read_byte(f),
		"C_grade": read_byte(f),
		"M_grade": read_byte(f),
		"beatmap_offset": read_short(f),
		"stack_leniency": read_single(f),
		"game_mode": read_byte(f),
		"song_source": read_string(f),
		"song_tags": read_string(f),
		"online_offset": read_short(f),
		"title_font": read_string(f),
		"unplayed": read_boolean(f),
		"last_play": read_long(f),
		"is_osz2": read_boolean(f),
		"folder_name": read_string(f),
		"last_online_sync": read_long(f),
		"ignore_beatmap_hitsounds": read_boolean(f),
		"ignore_beatmap_skin": read_boolean(f),
		"disable_storyboard": read_boolean(f),
		"disable_video": read_boolean(f),
		"visual_override": read_boolean(f),
		"wtf": read_short(f) if (osu_version < 20140609) else None,
		"last_modification_time": read_int(f),
		"scroll_speed": read_byte(f),
	}


def read_database(path):
	data = {
		"osu_version": None,
		"folder_count": None,
		"account_unlocked": None,
		"date_time": None,
		"name": None,
		"maps_amount": None,
		"beatmaps": [],
		"beatmaps_id": set(),
		"permissions": None,
	}

	with open(path, "rb") as f:
		data["osu_version"] = read_int(f)
		data["folder_count"] = read_int(f)
		data["account_unlocked"] = read_boolean(f)
		data["date_time"] = read_date_time(f)
		data["name"] = read_string(f)
		data["maps_amount"] = read_int(f)

		print("osu_version:", data["osu_version"])
		print("folder_count:", data["folder_count"])
		print("account_unlocked:", data["account_unlocked"])
		print("date_time:", str(data["date_time"]))
		print("name:", data["name"])
		print("maps_amount:", data["maps_amount"])
		
		for m in range(data["maps_amount"]):
			x = read_beatmap(f, data["osu_version"])
			data["beatmaps"].append(x)
			data["beatmaps_id"].add(x["beatmap_set_ID"])
			progress_bar.print_progress_bar(m+1, data["maps_amount"])

		data["permissions"] = read_int(f)
		print("permissions:", data["permissions"])

	return data


def print_database(data):
	print(
		f'osu_version: {data["osu_version"]}{os.linesep}' +
		f'folder_count: {data["folder_count"]}{os.linesep}' +
		f'account_unlocked: {data["account_unlocked"]}{os.linesep}' +
		f'date_time: {str(data["date_time"])}{os.linesep}' +
		f'name: {data["name"]}{os.linesep}' +
		f'maps_amount: {data["maps_amount"]}{os.linesep}' +
		f'permissions: {data["permissions"]}{os.linesep}' +
		f'beatmaps:{os.linesep}' +
		str(os.linesep).join(map(str, data["beatmaps_id"]))
	)


def save_database(data, filename):
	os.makedirs(os.path.dirname(filename), exist_ok=True)
	with open(filename, "wb") as p:
		pickle.dump(data, p)

def parse_args():
	parser = argparse.ArgumentParser(description='Convert osu!.db to pickle file')

	parser.add_argument("osu_db", type=str, help="Path to osu!.db database file",)
	parser.add_argument("output_file", type=str, help="Name of outputted pickle file",)
	parser.add_argument("--print_contents",help="Print database contents")
	args = parser.parse_args()
	return args.osu_db, args.output_file, args.print_contents



def main(path, filename, print_db=False):
	data = read_database(path)
	if filename: save_database(data, filename)
	if print_db: print_database(data)


if __name__ == "__main__":
	
	db_path, output_file, print_contents = parse_args()
	main(db_path, output_file, print_contents)
