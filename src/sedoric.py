#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# vim: set ts=4 ai :
#
# $Id: sedoric.py $
# $Author: assinie <github@assinie.info> $
# $Date: 2018-02-27 $
# $Revision: 0.1 $
#
#------------------------------------------------------------------------------


#
#	Ok pour SEDORIC2, Pb avec SEDORIC3, a voir...
#

__plugin_name__ = 'sedoric'
__description__ = "Gestion des images Sedoric"
__plugin_type__ = 'OS'
__version__ = '0.4'

ORIC_SEDORIC_VERSION = '0.4'

#from oricdsk import oricdsk
from utils import dump
from transform import transform

from pprint import pprint

import time

import stat    # for file properties
import os      # for filesystem modes (O_RDONLY, etc)
import errno   # for error number codes (ENOENT, etc)
               # - note: these must be returned as negatives

from math import ceil
import getpass
import sys
import struct

version = '\x01\x00\x00\x00\x00\x00\x00\x00        ' \
+ '\x00\x00\x03\x00\x00\x00\x01\x00' \
+ 'SEDORIC                                 ' \
+ 'SEDORIC V3.006 01/01/96\x0d\x0a' \
+ 'Upgraded by Ray McLaughlin         \x0d\x0a' \
+ 'and Andr{ Ch{ramy             \x0d\x0a\x0d\x0a' \
+ 'See SEDORIC3.FIX file for information \x0d\x0a' \
+ '                                                        '

# Octet #$16 = 0x01 pour une slave (0x00 pour une maitre)
copyright = '\x00\x00\xFF\x00\xD0\x9F\xD0\x9F\x02\xB9\x01\x00\xFF\x00\x00\xB9' \
+ '\xE4\xB9\x00\x00\xE6\x12\x01\x78\xA9\x7F\x8D\x0E\x03\xA9\x10\xA0' \
+ '\x07\x8D\x6B\x02\x8C\x6C\x02\xA9\x86\x8D\x14\x03\xA9\xBA\xA0\xB9' \
+ '\x20\x1A\x00\xA9\x84\x8D\x14\x03\xA2\x02\xBD\xFD\xCC\x9D\xF7\xCC' \
+ '\xCA\x10\xF7\xA2\x37\xA0\x80\xA9\x00\x18\x79\x00\xC9\xC8\xD0\xF9' \
+ '\xEE\x37\xB9\xCA\xD0\xF3\xA2\x04\xA8\xF0\x08\xAD\x01\xB9\xA8\xD0' \
+ '\x02\xA2\x3C\x84\x00\xA9\x7B\xA0\xB9\x8D\xFE\xFF\x8C\xFF\xFF\xA9' \
+ '\x05\x8D\x12\x03\xA9\x85\x8D\x14\x03\xA9\x88\x8D\x10\x03\xA0\x00' \
+ '\x58\xAD\x18\x03\x30\xFB\xAD\x13\x03\x99\x00\xC4\xC8\x4C\x6C\xB9' \
+ '\xA9\x84\x8D\x14\x03\x68\x68\x68\xAD\x10\x03\x29\x1C\xD0\xD5\xEE' \
+ '\x76\xB9\xEE\x12\x03\xCA\xF0\x1F\xAD\x12\x03\xCD\x00\xB9\xD0\xC1' \
+ '\xA9\x58\x8D\x10\x03\xA0\x03\x88\xD0\xFD\xAD\x10\x03\x4A\xB0\xFA' \
+ '\xA9\x01\x8D\x12\x03\xD0\xAA\xA9\xC0\x8D\x0E\x03\x4C\x00\xC4\x0C' \
+ '\x11' \
+ 'SEDORIC V3.0\x0a\x0d' \
+ '` 1985 ORIC INTERNATIONAL\x0d\x0a' + chr(0)*6

boot3 = '\x00\x00\x02' + 'SYSTEMDOS' + '\x01\x00\x02\x00\x02\x00\x00' + 'BOOTUPCOM' + '\x00\x00\x00\x00' \
				+ chr(0)*16*14

boot4 = '\x00\x00\xFF\x40\x00\x14\xFF\x4F\x00\x00\x3C\x00\x00\x05\x00\x06' \
+ '\x00\x07\x00\x08\x00\x09\x00\x0A\x00\x0B\x00\x0C\x00\x0D\x00\x0E' \
+ '\x00\x0F\x00\x10\x00\x11\x01\x01\x01\x02\x01\x03\x01\x04\x01\x05' \
+ '\x01\x06\x01\x07\x01\x08\x01\x09\x01\x0A\x01\x0B\x01\x0C\x01\x0D' \
+ '\x01\x0E\x01\x0F\x01\x10\x01\x11\x02\x01\x02\x02\x02\x03\x02\x04' \
+ '\x02\x05\x02\x06\x02\x07\x02\x08\x02\x09\x02\x0A\x02\x0B\x02\x0C' \
+ '\x02\x0D\x02\x0E\x02\x0F\x02\x10\x02\x11\x03\x01\x03\x02\x03\x03' \
+ '\x03\x04\x03\x05\x03\x06\x03\x07\x03\x08\x03\x09\x03\x0A\x03\x0B' \
+ '\x03\x0C\x03\x0D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
+ chr(0)*16*7

boot5 = '\xAD\x07\xC0\x4A\xA9\x00\x6A\x8D\x24\xC0\x10\x0F\xA9\x50\x8D\x56' \
+ '\x02\x4A\x85\x31\x85\x32\x8D\x57\x02\xD0\x06\xA9\x5D\x85\x31\x85' \
+ '\x32\xEE\xC1\x02\xEE\xC2\x02\xA2\x00\xBD\x00\xC6\x2C\x24\xC0\x10' \
+ '\x03\xBD\x00\xC7\x9D\x00\x04\xE8\xD0\xEF\xA9\x4C\xA0\x00\xA2\x04' \
+ '\x85\xEF\x84\xF0\x86\xF1\xA9\x88\xA0\xC4\x2C\x24\xC0\x10\x26\x8D' \
+ '\x45\x02\x8E\x46\x02\x8C\x48\x02\x8E\x49\x02\xA9\x5B\x8D\x3C\x02' \
+ '\x8E\x3D\x02\xA9\x09\xA0\x01\x8D\x4E\x02\x8C\x4F\x02\xA9\x0F\xA2' \
+ '\x70\xA0\xD0\xD0\x12\x8D\x29\x02\x8E\x2A\x02\x8C\x2C\x02\x8E\x2D' \
+ '\x02\xA9\x07\xA2\xE4\xA0\xCF\x8D\x6A\x02\x8E\xF9\x02\x8C\xFA\x02' \
+ '\xA2\x04\xA9\xA5\xA0\xD0\x8D\xFE\xFF\x8C\xFF\xFF\xA9\x67\xA0\x61' \
+ '\x8D\xF5\x02\x8E\xF6\x02\x8C\xFC\x02\x8E\xFD\x02\xA9\x00\x8D\x09' \
+ '\xC0\x8D\x0A\xC0\x8D\x0B\xC0\x8D\x0C\xC0\x8D\x15\xC0\x8D\x18\xC0' \
+ '\x8D\xDF\x02\x8D\x48\xC0\x85\x87\xA9\x85\xA0\xD6\x8D\x1D\xC0\x8C' \
+ '\x1E\xC0\xAD\x11\x03\x8D\x0C\xC0\xA9\x23\xA0\xDE\xA2\x80\x8D\x66' \
+ '\xC0\x8C\x67\xC0\x8E\x68\xC0\x8D\x69\xC0\x8C\x6A\xC0\x8E\x6B\xC0' \
+ '\x8D\x6C\xC0\x8C\x6D\xC0\x8E\x6E\xC0\x8D\x6F\xC0\x8C\x70\xC0\x8E'

boot6 = '\x71\xC0\xA9\x2E\x8D\x75\xC0\xA9\x1A\xA0\x00\x8D\xF0\x04\x8C\xF1' \
+ '\x04\xA5\x00\xF0\x12\xA2\xFF\xE8\xBD\x74\xC5\x9D\x00\xB9\xD0\xF7' \
+ '\xA9\x00\xA0\xB9\x20\xEC\x04\xA9\x14\xA0\x01\x20\x5D\xDA\xA2\x08' \
+ '\xBD\x00\xC1\x9D\x39\xC0\xE0\x05\x90\x03\x9D\x3D\xC0\xCA\x10\xF0' \
+ '\x20\xA3\xEB\x20\xD8\xD5\xE0\xF7\x16\xF8\xA2\x41\xBD\x1E\xC1\x95' \
+ '\x36\xCA\x10\xF8\xA9\x3A\x85\x35\x20\x06\xD2\xA9\xBD\xA0\xC4\x2C' \
+ '\x24\xC0\x30\x02\xA9\xCD\x8D\xF0\x04\x8C\xF1\x04\xA2\x34\xA0\x00' \
+ '\x58\x4C\x71\x04\x0A\x8C\x81** WARNIN' \
+ 'G **\x88\x87DOS is alt' \
+ 'ered !\x0D\x0A\x00\x4C\x64\xD3\x60\xAD\xAE\xC5' \
+ '\xAE\xAF\xC5\x8D\x01\xC0\x8E\x02\xC0\xAD\xB0\xC5\xD0\xDB\x27\x09' \
+ '\x1AIN DRIVE\xA0LOAD D' \
+ 'ISCS FOR BACKUP ' \
+ 'FROM\xA0 TO\xA0\x0D\x0ALOAD ' \
+ 'SOURCE DISC\xA0\x0D\x0ALO' \
+ 'AD TARGET DISA-+'

boot7 = '\xC9\x30\x90\x04\xC9\x3A\x90\x35\x86\x0F\xAA\x30\x2E\x85\xC1\x68' \
+ '\xAA\x68\x48\xE0\xF7\xD0\x04\xC9\xC8\xF0\x09\xE0\x58\xD0\x18\xC9' \
+ '\xCA\xD0\x14\x24\x18\x6E\xFC\x04\xA0\xFF\xC8\xB1\xE9\xF0\x11\xC9' \
+ '\x3A\xF0\x0D\xC9\xD4\xD0\xF3\x8A\x48\xA5\xC1\xA6\x0F\x4C\x41\xEA' \
+ '\x68\x20\xE9\x04\x20\x67\x04\x0E\xFC\x04\xB0\x03\x4C\xAD\xC8\xEA' \
+ '\xEA\xEA\x60\x20\x77\x04\xB1\x16\x4C\x77\x04\xEA\xEA\xEA\xEA\xEA' \
+ '\xEA\xA9\x8E\xA0\xF8\xD0\x04\xA9\xAE\xA0\xD3\x8D\xF0\x04\x8C\xF1' \
+ '\x04\x20\x77\x04\x20\xEF\x04\x08\x48\x78\xAD\xFB\x04\x49\x02\x8D' \
+ '\xFB\x04\x8D\x14\x03\x68\x28\x60\x2C\x0D\x03\x50\x0F\x48\xA9\x04' \
+ '\x2D\x6A\x02\xF0\x03\xEE\x74\x02\x68\x4C\x03\xEC\x68\x68\x85\xF2' \
+ '\x68\xAA\xA9\x36\xA0\xD1\xD0\xC3\x20\xF2\x04\x68\x40\x8D\x14\x03' \
+ '\x6C\xFC\xFF\x18\x20\x77\x04\x48\xA9\x04\x48\xA9\xA8\x48\x08\xB0' \
+ '\x03\x4C\x28\x02\x20\x88\xF8\xA9\x17\xA0\xEC\x20\x6B\x04\x4C\x75' \
+ '\xC4\xA9\x04\x48\xA9\xF1\x48\x8A\x48\x98\x48\x20\xF2\x04\x4C\x70' \
+ '\xD2\xEA\xEA\xEA\xEA\xEA\xEA\xEA\xEA\x4C\x87\x04\x4C\x71\x04\x4C' \
+ '\x00\x00\x4C\x77\x04\x4C\xB3\x04\x4C\xB4\x04\x84\x00\x00\x00\x00'

boot8 = '\xC9\x30\x90\x04\xC9\x3A\x90\x35\x86\x0F\xAA\x30\x2E\x85\xC1\x68' \
+ '\xAA\x68\x48\xE0\x0E\xD0\x04\xC9\xC9\xF0\x09\xE0\x8A\xD0\x18\xC9' \
+ '\xCA\xD0\x14\x24\x18\x6E\xFC\x04\xA0\xFF\xC8\xB1\xE9\xF0\x11\xC9' \
+ '\x3A\xF0\x0D\xC9\xD4\xD0\xF3\x8A\x48\xA5\xC1\xA6\x0F\x4C\xB9\xEC' \
+ '\x68\x20\xE9\x04\x20\x67\x04\x0E\xFC\x04\xB0\x03\x4C\xC1\xC8\x6E' \
+ '\x52\x02\x60\x20\x77\x04\xB1\x16\x4C\x77\x04\xA9\x45\xA0\xD8\xD0' \
+ '\x0A\xA9\x8E\xA0\xF8\xD0\x04\xA9\xAE\xA0\xD3\x8D\xF0\x04\x8C\xF1' \
+ '\x04\x20\x77\x04\x20\xEF\x04\x08\x48\x78\xAD\xFB\x04\x49\x02\x8D' \
+ '\xFB\x04\x8D\x14\x03\x68\x28\x60\x2C\x0D\x03\x50\x0F\x48\xA9\x04' \
+ '\x2D\x6A\x02\xF0\x03\xEE\x74\x02\x68\x4C\x22\xEE\x68\x68\x85\xF2' \
+ '\x68\xAA\xA9\x36\xA0\xD1\xD0\xC3\x20\xF2\x04\x68\x40\x8D\x14\x03' \
+ '\x6C\xFC\xFF\x18\x20\x77\x04\x48\xA9\x04\x48\xA9\xA8\x48\x08\xB0' \
+ '\x03\x4C\x44\x02\x20\xB8\xF8\xA9\x17\xA0\xEC\x20\x6B\x04\x4C\x71' \
+ '\xC4\xA9\x04\x48\xA9\xF1\x48\x8A\x48\x98\x48\x20\xF2\x04\x4C\x06' \
+ '\xD3\xEA\xEA\xEA\xEA\xEA\xEA\xEA\xEA\x4C\x87\x04\x4C\x71\x04\x4C' \
+ '\x00\x00\x4C\x77\x04\x4C\xB3\x04\x4C\xB4\x04\x84\x00\x00\x00\x00'

bootsectors = [version, copyright, boot3, boot4, boot5, boot6, boot7, boot8]

def __init_plugin__():
		print "%s.__init_plugin__()" % __name__

def __setup__():
		return sedoric()


def SEDORIC_DirEntry(self, entry):
	# name = entry[0:12]
	name = entry[0:9] + '.' + entry[9:12]
	P_FCB = ord(entry[12])
	S_FCB = ord(entry[13])

	# size = taille en secteur
	size = ord(entry[14])

	lock = entry[15]
	type = ' '
	content_type = ' '
	side = 0

	size += (ord(lock) & 0x3f) * 256

	if ord(lock) & 0xC0 == 0x40:
		lock = 'U'
	elif ord(lock) & 0xC0 == 0xC0:
		lock = 'L'
	else:
		lock = '?'


	if P_FCB + S_FCB != 0:
		# print '%c  %s  %c       %d SECTORS' % (lock, name, type, len)

		# si track >= 0x80 => track = track - 0x80, face = 2
		#if P_FCB >= 0x80:
		#	P_FCB -= 0x80
		#	side = 1

		# print 'S:%d P:%02d S:%02d %c %s %c %d' % (side, P_FCB, S_FCB, lock, name, type, size)
		# Pour avoir le content_type, il lire le FCB du fichier
		#track = self.read_track(P_FCB,side)
		track = self.read_track(P_FCB & 0x7f, (P_FCB & 0x80) >> 7)

		offset = track['sectors'][S_FCB]['data_ptr'] +1
		cat = track['raw'][offset:offset+256]

		type = ord(cat[3])
		#
		# b7 b6 b5 b4 b3 b2 b1 b0
		# |  |  |  |  |  +___+ +--> Auto
		# |  |  |  |  |    +------> Inutilisés
		# |  |  |  |  +-----------> Direct
		# |  |  |  +--------------> Sequentiel
		# |  |  +-----------------> Windows (b6=1 aussi)
		# |  +--------------------> Data
		# +-----------------------> Basic
		#

		content_type = '???'
		if type & 0x08 == 0x08:
				content_type = 'Direct'
		elif type & 0x10 == 0x10:
				content_type = 'Sequentiel'
		elif type & 0x20 == 0x20:
				# type = 0x20 | 0x40
				content_type = 'Windows'
		elif type & 0x40 == 0x40:
				content_type = 'data'
		elif type & 0x80 == 0x80:
				content_type = 'basic'

		return {name: {'side': side, 'track': P_FCB, 'sector': S_FCB, 'lock': lock, 'type': type, 'size': size, 'content_type': content_type}}

	return {}


class sedoric():
	def __init__(self, source = 'DEFAULT'):
		self.dirents = {}
		self.source = source
		self.offset = 0
		self.sides = 2
		self.tracks = 41
		self.sectors = 17
		self.sectorsize = 256
		self.geometry = 1
		self.signature = 'MFM_DISK'
		self.diskname = ''
		self.dostype = 'SEDORIC'
		self.disktype = ''

		self.crc = 0
		self.trackbuf = []
		self.ptr_track = 0

		self.transform = transform()

	def validate(self, diskimg):
		ret = None

		try:
			diskimg = os.path.abspath(diskimg)

			with open(diskimg,'rb') as f:
				self.signature = f.read(8)

				if self.signature != 'MFM_DISK':
					print "Erreur signature '%s' incorrecte pour %s" % (self.signature, diskimg)
				else:
					self.source = diskimg

					track = self.read_track(0,0)
					offset = track['sectors'][1]['data_ptr'] +1
					dos = track['raw'][offset:offset+256][24:32].rstrip()

					if dos in ['XL DOS', 'SEDORIC', 'RADOS', 'ORICDOS']:

						self.sectors = len(track['sectors'])
						self.offset = 0x100
						self.sectorsize = 256

						self.sides = struct.unpack("<L", f.read(4))[0]
						self.tracks = struct.unpack("<L", f.read(4))[0]
						self.geometry = struct.unpack("<L",f.read(4))[0]

						ret = {'source': diskimg,
							'sides': self.sides,
							'tracks': self.tracks,
							'sectors': self.sectors,
							'sectorsize': self.sectorsize,
							'geometry': self.geometry,
							'offset': self.offset }

						#self.read_diskname()
						#self.read_dir()
						self.loaddisk()

		except:
			e = sys.exc_info()[0]
			print "Erreur " , sys.exc_info()
			self.source = None
			ret = None
			raise

		return ret


	def read_track(self, track, side):
		# print '***read_track(%s): Track=%d/%d, Side=%d' % (__name__, track, self.tracks, side)
		sector = {}
		read_track = {}

		if self.signature != 'MFM_DISK':
			return sector

		with open(self.source,'rb') as f:
			ptr = self.offset + (side*self.tracks +track)*6400
			f.seek(ptr)
			raw = f.read(6400)
			read_track['raw'] = raw
			sectorcount = 0
			ptr = 0
			eot = 6400

			while ptr < eot:
				while ptr < eot and ord(raw[ptr]) != 0xfe:
					ptr += 1

				if ptr >= eot:
					break

				S = ord(raw[ptr+3])
				P = ord(raw[ptr+1])
				# print 'found sector: P:%d S:%d (%d)' % (P, S, sectorcount)

				sector[S] = {}
				sector[S]['id_ptr'] = ptr
				sector[S]['data_ptr'] = -1

				sectorcount += 1
				# ID field
				n = ord(raw[ptr+4])
				# print 'ID: ', n
				# skip ID field & crc
				ptr += 7

				while ptr < eot and ord(raw[ptr]) != 0xfb and ord(raw[ptr]) != 0xfe:
					ptr += 1

				if ptr >= eot:
					break

				sector[S]['data_ptr'] = ptr

				# Skip data field and ID
				ptr += (1<<(n+7))+3
			# print sectorcount
		f.close()
		read_track['sectors'] = sector

		return read_track

	def find_free_sector(self, bitmap):
		#
		# bitmap: table avec les 2 bitmaps
		#
		print '*** find_free_sector'

		# P = 20
		# S = 2
		# track = self.read_track(P,0)
		# offset = track['sectors'][S]['data_ptr'] +1
		# raw = track['raw'][offset:offset+256]

		# S = 3
		# offset = track['sectors'][S]['data_ptr'] +1
		# raw2 = track['raw'][offset:offset+256]

		raw = bitmap[0]
		raw2 = bitmap[1]

		Smax = struct.unpack('<H', raw2[0x02:0x04])[0]
		ST =  ord(raw[0x07:0x08])

		ok = False
		offset = 0x10 -1
		track = -1
		sector = 0

		S = 0
		while not ok and S < Smax:
			offset += 1

			if offset > 0xff:
				# On passe à la seconde bitmap
				print 'Utilisation de la BitMap2'
				raw = raw2
				offset = 0x10

			if S < Smax:
				for i in range(0,8):

					if S < Smax and not ok:
						P = S / ST

						print 'Test T:%d, S:%d' % (P, (S % ST)+1)

						if ord(raw[offset:offset+1]) & 2**i == 2**i:
							print '\tbit: %d' % i
							ok = True
							track = P
							sector = (S % ST) +1

						S = S + 1

		return [track,sector]


	def set_bitmap_sector_used(self, bitmap, track, sector):
		raw = bitmap[0]
		raw2 = bitmap[1]

		Smax = struct.unpack('<H', raw2[0x02:0x04])[0]
		ST =  ord(raw[0x07:0x08])

		S = track * ST + sector -1 # Verifier que S < Smax?
		offset = 0x10 + (S / 8)
		bit = S % 8

		print "(T=%d, S=%d) => offset=%X, bit=%d" % (track, sector, offset, bit)

		if offset < 0x100:
			print '\tAvant: %X' % ord(raw[offset:offset+1])
			x = ord(raw[offset:offset+1]) & (0xff - 2**bit)
			print '\tAprès: %X' % x
			raw =  raw[:offset] + chr(x) + raw[offset+1:]
		else:
			x = ord(raw2[offset:offset+1]) & (0xff - 2**bit)
			raw2 =  raw2[:offset] + chr(x) + raw2[offset+1:]

		return [raw, raw2]

	def set_bitmap_sector_free(self, bitmap, track, sector):
		raw = bitmap[0]
		raw2 = bitmap[1]

		Smax = struct.unpack('<H', raw2[0x02:0x04])[0]
		ST =  ord(raw[0x07:0x08])

		S = track * ST + sector -1 # Verifier que S < Smax?
		offset = 0x10 + (S / 8)
		bit = S % 8

		print "(T=%d, S=%d) => offset=%d, bit=%d" % (track, sector, offset, bit)

		if offset < 0x100:
			print '\tAvant: %X' % ord(raw[offset:offset+1])
			x = ord(raw[offset:offset+1]) | (2**bit)
			print '\tAprès: %X' % x
			raw =  raw[:offset] + chr(x) + raw[offset+1:]
		else:
			x = ord(raw2[offset:offset+1]) | (2**bit)
			raw =  raw2[:offset] + chr(x) + raw2[offset+1:]

		return [raw, raw2]


	def initdisk(self, params):
		self.diskname = params['volume']
		self.tracks = params['tracks']
		self.sectors = params['sectors']
		self.sides = params['sides']

		print '*** initdisk T=%d, S=%d, H=%d' % (self.tracks, self.sectors, self.sides)

		# Disquette Slave:
		#	Piste 00/1 à 8           : Boot
		#	Piste 20/1               : Secteur Système
		#	Piste 20/2 et 3          : BitMap
		#	Piste 20/4, 7, 10, 13, 16: Catalogues
		#	-------------------------: 16 Secteurs occupés
		#

		# self.tracks = 82

		system = chr(self.tracks + 128*(self.sides-1)) * 4 \
			+ chr(0x40) \
			+ struct.pack('<H',100) + struct.pack('<H',10) \
			+ ('%- 21s' % self.diskname) \
			+ chr(0x20) * 60 \
			+ chr(0x00) * 166 \

		Smax = self.tracks*self.sectors*self.sides

		bitmap1 = chr(0xff) + chr(0x00) + struct.pack('<H',Smax-16) + struct.pack('<H',0) \
			+ chr(self.tracks) + chr(self.sectors) + chr(0x01) + chr(self.tracks + 128*(self.sides-1)) \
			+ chr(0x01) + chr(0)*5 + chr(0xff) * 240

		bitmap2 = chr(0xff) + chr(0x00) + struct.pack('<H',Smax) + struct.pack('<H',0) \
			+ chr(self.tracks) + chr(self.sectors) + chr(0x01) + chr(self.tracks + 128*(self.sides-1)) \
			+ chr(0x01) + chr(0)*5 + chr(0xff) * 240


		# Offset
		#	00-01: Piste/Secteur du catalogue suivant
		#	02   : Offset vers la première entrée libre (0x00 si plein)
		#	03-0F: $00... Inutilisé
		#	10-FF: Entrées du catalogue

		directory = chr(0x00) + chr(0x00) + chr(0x10) + chr(0x00) * 253

		bitmap = [bitmap1, bitmap2]
		for i in range(1,9):
			bitmap = self.set_bitmap_sector_used(bitmap, 0, i)     # Boot

		bitmap = self.set_bitmap_sector_used(bitmap, 20, 1)     # secteur système
		bitmap = self.set_bitmap_sector_used(bitmap, 20, 2)     # bitmap sector
		bitmap = self.set_bitmap_sector_used(bitmap, 20, 3)     # bitmap sector
		bitmap = self.set_bitmap_sector_used(bitmap, 20, 4)     # catalogue
		bitmap = self.set_bitmap_sector_used(bitmap, 20, 7)     # catalogue
		bitmap = self.set_bitmap_sector_used(bitmap, 20, 10)     # catalogue
		bitmap = self.set_bitmap_sector_used(bitmap, 20, 13)     # catalogue
		bitmap = self.set_bitmap_sector_used(bitmap, 20, 16)     # catalogue

		diskimg = []
		for i in range(0,self.tracks * self.sides):
			print '\tAjoute piste: %d' % i
			diskimg.append([chr(0x00) * self.sectorsize] *(self.sectors+1))

		for i in range(0, 8):
			diskimg[0][i] = bootsectors[i]

		diskimg[20][1-1] = system
		diskimg[20][2-1] = bitmap[0]
		diskimg[20][3-1] = bitmap[1]
		diskimg[20][4-1] = directory

		self.diskimg = {'diskimg': diskimg, 'bitmap': bitmap, 'directory': directory}
		return self.diskimg


	def add_directory_entry(self, diskimg, file):
		print '*** add_directory_entry'
		nbsector = int(ceil(float(file['size'])/float(self.sectorsize)))

		bitmap = diskimg['bitmap']

		# -nbsector libres
		# +1 pour le nombre de fichiers sur la disquette
		bitmap[0] = bitmap[0][:0x02] + struct.pack('<H', struct.unpack('<H',bitmap[0][0x02:0x04])[0]-nbsector) + struct.pack('<H',struct.unpack('<H', bitmap[0][0x04:0x06])[0] +1) + bitmap[0][0x06:]

		if file['content_type'] == 'basic':
			ext = 'BAS'
		elif file['content_type'] == 'Windows':
			ext = 'WIN'
		else:
			ext = 'BIN'

		# filename = file['filename'].replace(' ','-')
		filename = file['filename']
		file['filename'] = '%-9s%-3s' % (os.path.splitext(filename)[0][0:9], ext)

		# Entrée à ajouter
		new_entry = file['filename']
		new_entry += chr(file['track'])
		new_entry += chr(file['sector'])
		new_entry += chr(nbsector & 0x00ff)
		new_entry += chr( ((nbsector>>8) & 0x1f) | 0x40 )	# 0x40: Fichier non protégé / 0xC0: Fichier protégé

		# Lecture premier secteur du catalogue S:0 P:20 S:4

		P=20
		S=4
		ok = False

		while P != 0x00 and S != 0x00 and ok == False:
			print "Lecture: P=%d, S=%d" % (P, S)
			cat = diskimg['diskimg'][P][S-1]
			print dump(cat)

			# Chainage vers le catalogue suivant: 00 00 si dernier secteur
			P_next = ord(cat[0])
			S_next = ord(cat[1])

			# Pour le chainage en cas d'extension
			P_last = P
			S_last = S

			entry_offset = ord(cat[2])
			if entry_offset != 0x00:
				print "Ajout en P=%d, S=%d, E=%d" % (P, S, entry_offset)
				# cat = cat[:entry_offset] + new_entry + cat[entry_offset+16:]
				cat = cat[0:2]+chr((entry_offset+0x10)&0xff)+cat[3:entry_offset] + new_entry + cat[entry_offset+16:]
				diskimg['diskimg'][P][S-1] = cat
				ok = True
				break

			else:
				if P_next == 0x00 and S_next == 0x00:
					if P == 0x14:
						# Les secteurs 7/10/13/16 sont réservés pour le catalogue
						# mais ne sont pas initialisés
						if S == 4:
							S_next = 7

							# Chainage
							cat = chr(P) + chr(S_next) + cat[0x03:]
							diskimg['diskimg'][P][S-1] = cat

							# +1 pour le nombre de secteurs catalogue
							bitmap[0] = bitmap[0][0x00:0x08] + chr(ord(bitmap[0][0x08:0x09])+1) + bitmap[0][0x09:]

							new_cat = diskimg['diskimg'][P][S_next-1]
							if ord(new_cat[0x02]) == 0x00:
								new_cat = new_cat[0x00:0x02] + chr(0x10) + new_cat[0x03:]
								diskimg['diskimg'][P][S_next-1] = new_cat

						elif S == 7:
							S_next = 10

							# Chainage
							cat = chr(P) + chr(S_next) + cat[0x03:]
							diskimg['diskimg'][P][S-1] = cat

							# +1 pour le nombre de secteurs catalogue
							bitmap[0] = bitmap[0][0x00:0x08] + chr(ord(bitmap[0][0x08:0x09])+1) + bitmap[0][0x09:]

							new_cat = diskimg['diskimg'][P][S_next-1]
							if ord(new_cat[0x02]) == 0x00:
								new_cat = new_cat[0x00:0x02] + chr(0x10) + new_cat[0x03:]
								diskimg['diskimg'][P][S_next-1] = new_cat

						elif S == 10:
							S_next = 13

							# Chainage
							cat = chr(P) + chr(S_next) + cat[0x03:]
							diskimg['diskimg'][P][S-1] = cat

							# +1 pour le nombre de secteurs catalogue
							bitmap[0] = bitmap[0][0x00:0x08] + chr(ord(bitmap[0][0x08:0x09])+1) + bitmap[0][0x09:]

							new_cat = diskimg['diskimg'][P][S_next-1]
							if ord(new_cat[0x02]) == 0x00:
								new_cat = new_cat[0x00:0x02] + chr(0x10) + new_cat[0x03:]
								diskimg['diskimg'][P][S_next-1] = new_cat

						elif S == 13:
							S_next = 16

							# Chainage
							cat = chr(P) + chr(S_next) + cat[0x03:]
							diskimg['diskimg'][P][S-1] = cat

							# +1 pour le nombre de secteurs catalogue
							bitmap[0] = bitmap[0][0x00:0x08] + chr(ord(bitmap[0][0x08:0x09])+1) + bitmap[0][0x09:]

							new_cat = diskimg['diskimg'][P][S_next-1]
							if ord(new_cat[0x02]) == 0x00:
								new_cat = new_cat[0x00:0x02] + chr(0x10) + new_cat[0x03:]
								diskimg['diskimg'][P][S_next-1] = new_cat
				P = P_next
				S = S_next

		if ok == True:
			diskimg['diskimg'][20][2-1] = bitmap[0]
			diskimg['diskimg'][20][3-1] = bitmap[1]

			diskimg['bitmap'] = bitmap
			diskimg['directory'] = diskimg['diskimg'][20][4-1]

			return diskimg

		else:
			# Extension du catalogue
			bitmap = diskimg['bitmap']
			[P, S] = self.find_free_sector(bitmap)
			print "Directory extension Track: %d, Sector: %d" % (P, S)

			if P == -1:
				return False

			bitmap = self.set_bitmap_sector_used(bitmap, P, S)

			# +1 pour le nombre de secteurs catalogue
			bitmap[0] = bitmap[0][0x00:0x08] + chr(ord(bitmap[0][0x08:0x09])+1) + bitmap[0][0x09:]

			diskimg['diskimg'][20][2-1] = bitmap[0]
			diskimg['diskimg'][20][3-1] = bitmap[1]
			diskimg['bitmap'] = bitmap

			# Chainage
			cat = diskimg['diskimg'][P_last][S_last-1]
			cat = chr(P) + chr(S) + cat[2:]
			diskimg['diskimg'][P_last][S_last-1] = cat

			diskimg['directory'] = diskimg['diskimg'][20][4-1]

			# Nouveau secteur du catalogue
			cat = chr(0x00) +chr(0) + chr(0x10) + chr(0x00)* 253

			# Ajout de l'entrée
			entry_offset = 16+0*16
			cat = cat[:entry_offset] + new_entry + cat[entry_offset+16:]
			diskimg['diskimg'][P][S-1] = cat

			print dump(diskimg['diskimg'][P][S-1])
			return diskimg


	def find_directory_entry(self, filename):
		print '*** find_directory_entry(%s)' % filename

		diskimg = self.diskimg

		# Lecture premier secteur du catalogue S:0 P:20 S:4

		P=20
		S=4
		ok = False

		while P != 0x00 and S != 0x00 and ok == False:
			# print "Lecture: P=%d, S=%d" % (P, S)
			cat = diskimg['diskimg'][P][S-1]
			# print dump(cat)

			# Chainage vers le catalogue suivant: 00 00 si dernier secteur
			P_next = ord(cat[0])
			S_next = ord(cat[1])

			entry_offset_max = ord(cat[2])
			if entry_offset_max == 0:
				# Le catalogue est plein
				entry_offset_max = 256

			for entry_offset in range(0x10, entry_offset_max, 0x10):
				entry = '%s.%s' % (cat[entry_offset:entry_offset+9], cat[entry_offset+9:entry_offset+12])
				# print '**** test %s' % entry
				if filename == entry:
					ok = True
					break

			if ok == False:
				P = P_next
				S = S_next

		if ok == True:
			# print '**** trouvé en T=%d, S=%d, offset=%d' % (P,S,entry_offset)
			return ([P,S,entry_offset])

		return False

	def del_directory_entry(self, diskimg, file):
		print '*** del_directory_entry'

	def add_file(self, file):
		diskimg = self.diskimg

		nbsector = int(ceil(float(file['size'])/float(self.sectorsize)))
		nbfcb = 1

		# On force le nom du fichier en majuscule
		file['filename'] = file['filename'].upper()

		#
		# Optimisation possible:
		#	Vérifier qu'il reste assez de secteurs disponibles en regardant dans la bitmap[0]
		#
		print '***add_file (%s): filename: %s, start: %04X, size: %d (%d secteurs), type: %s' % (__name__, file['filename'], file['start'], file['size'], nbsector, file['content_type'])

		bitmap = diskimg['bitmap']

		[fcb_track, fcb_sector] = self.find_free_sector(bitmap)

		if fcb_track == -1:
			return -errno.ENOSPC

		sedoric_fcb_track = fcb_track
		if fcb_track >= self.tracks:
			sedoric_fcb_track += 128 - self.tracks

		print "FCB Track: %d, Sector: %d" % (sedoric_fcb_track, fcb_sector)

		bitmap = self.set_bitmap_sector_used(bitmap, fcb_track, fcb_sector)

		# Un FCB ne peut decrire qu'un fichier de 122 secteurs pour le premier et 127 pour les suivants
		fcb = [0x00] * 256
		fcb[0x00:0x02] = [0x00,0x00] # Pas de chainage
		fcb[0x02:0x03] = [0xff] # Premier FCB

		content_type = file['content_type']

		type = 0x00
		if content_type == 'Direct':
			type = 0x08
		elif content_type == 'Sequentiel':
			type = 0x10
		elif content_type == 'Windows':
			type = 0x20 | 0x40
		elif content_type == 'data' or content_type == 'asm':
			type = 0x40
		elif content_type == 'basic':
			type = 0x80

		fcb[0x03:0x04] = [type] # Type du fichier
		file_end = file['start'] + file['size'] -1
		fcb[0x04:0x06] = [file['start'] & 0x00ff, file['start'] >> 8]
		fcb[0x06:0x08] = [file_end & 0x00ff, file_end >> 8]
		fcb[0x08:0x0A] = [0x00, 0x00] # Adresse de demarrage si Autostart
		fcb[0x0A:0x0C] = [nbsector & 0x00ff, nbsector >> 8] # Taille en secteurs

		file['track'] = sedoric_fcb_track
		file['sector'] = fcb_sector

		i = 0
		while i < nbsector:
			[file_track, file_sector] = self.find_free_sector(bitmap)

			if file_track == -1:
				return -errno.ENOSPC

			sedoric_file_track = file_track
			if file_track >= self.tracks:
				sedoric_file_track += 128 - self.tracks

			print "***add_file (%s): File T= %d, S= %d" % (__name__, sedoric_file_track, file_sector)

			bitmap = self.set_bitmap_sector_used(bitmap, file_track, file_sector)
			sector = file['file'][i*self.sectorsize:(i+1)*self.sectorsize]
			if len(sector) == self.sectorsize:
				diskimg['diskimg'][file_track][file_sector-1] = sector
			else:
				diskimg['diskimg'][file_track][file_sector-1] = sector + diskimg['diskimg'][file_track][file_sector-1][len(sector):]

			# 122 pour le premier FCB, 127 pour les suivants
			# Offset + 0x0c pour le premier FCB, +0x02 pour les suivants
			# TODO: Gérer les FCB > 1
			fcb_offset = (i % 122)*2
			fcb[0x0c+fcb_offset:0x0e+fcb_offset] = [sedoric_file_track, file_sector]

			i += 1
			if i%122 == 0:
				nbfcb += 1
				P = fcb_track
				S = fcb_sector
				[fcb_track, fcb_sector] = self.find_free_sector(bitmap)

				if fcb_track == -1:
					return -errno.ENOSPC

				sedoric_fcb_track = fcb_track
				if fcb_track >= self.tracks:
					sedoric_fcb_track += 128 - self.tracks

				print "FCB extension Track: %d, Sector: %d" % (sedoric_fcb_track, fcb_sector)
				bitmap = self.set_bitmap_sector_used(bitmap, fcb_track, fcb_sector)

				fcb[0:2] = [sedoric_fcb_track, fcb_sector]
				diskimg['diskimg'][P][S-1] = ''.join([chr(x) for x in fcb])
				print dump(diskimg['diskimg'][P][S-1])

				diskimg['diskimg'][20][2-1] = bitmap[0]
				diskimg['diskimg'][20][3-1] = bitmap[1]
				diskimg['bitmap'] = bitmap

				fcb = [0x00] * 256
				fcb[0x00:0x02] = [0x00,0x00] # Pas de chainage

		diskimg['diskimg'][20][2-1] = bitmap[0]
		diskimg['diskimg'][20][3-1] = bitmap[1]
		diskimg['bitmap'] = bitmap
		diskimg['diskimg'][fcb_track][fcb_sector-1] = ''.join([chr(x) for x in fcb])

		print '***add_file (%s): Last FCB: T=%d, S=%d' % (__name__, sedoric_fcb_track, fcb_sector)
		print dump(''.join([chr(x) for x in fcb]))

		# Ajoute le nombre de FCB à la taille du fichier
		file['size'] += self.sectorsize * nbfcb

		diskimg = self.add_directory_entry(diskimg, file)
		if diskimg != False:
			self.diskimg = diskimg
			return True

		else:
			print '***add_file (%s): "%s" directory full => rollback' % (__name__, file['filename'])
			return -errno.ENOSPC

	def unlink(self, file):
		print '*** unlink'
		return -errno.ENOSYS

	def rename(self, oldPath, newPath):
		print '*** rename(%s,%s)' % (oldPath, newPath)

		ret = self.find_directory_entry(oldPath)
		if ret == False:
			return -errno.ENOENT

		filename = os.path.splitext(newPath)
		newPath = '%-9s.%-3s' % (filename[0],filename[1][1:4])

		if self.find_directory_entry(newPath) != False:
			return -errno.EEXIST

		P=ret[0]
		S=ret[1]
		entry_offset = ret[2]
		newPath = '%-9s%-3s' % (filename[0],filename[1][1:4])
		cat = self.diskimg['diskimg'][P][S-1]
		cat = cat[0:entry_offset]+newPath+cat[entry_offset+12:]
		self.diskimg['diskimg'][P][S-1] = cat

		print '**** Apres le rename'
		print dump(cat)

		return True

	def loaddisk(self):
		print '*** loaddisk'
		self.diskimg = {'diskimg': [], 'bitmap': '', 'directory': ''}
		diskimg = []

		for P in range(0, self.tracks * self.sides):
			diskimg.append([])

			track = self.read_track(P,0)

			for S in range(1, self.sectors +1):
				# Calcul de l'offset du secteur (+1 pour sauter l'ID)
				offset = track['sectors'][S]['data_ptr'] +1
				sector = track['raw'][offset:offset+256]

				diskimg[P].append(sector)

		bitmap = [diskimg[20][2-1], diskimg[20][3-1]]
		directory = diskimg[20][4-1]
		self.diskimg = {'diskimg': diskimg, 'bitmap': bitmap, 'directory': directory}

		print dump(directory)

	def newdisk(self,filename,diskname, diskimg):
		print '*** newdisk [INUTILISE]'
		header = chr(0) * 256

		fd = open(filename,'wb')
		fd.write(header)
		bitmap = [ord(x) for x in diskimg['bitmap']]

		for head in range(0,self.sides):
			for cyl in range(0,self.tracks):
				self.init_track()
				# buffer = [0x6C] * 256
				for sect in range(1,self.sectors+1):
					buffer = [ord(x) for x in diskimg['diskimg'][cyl*(head+1)][sect-1]]
					self.store_sector(buffer,cyl, head, sect, 1)

				self.flush_track(fd)

		self.flush_diskid(fd)

		fd.close()


	def read_diskname(self):
		P = 20
		S = 1
		track = self.read_track(P,0)

		# Calcul de l'offset du secteur (+1 pour sauter l'ID)
		offset = track['sectors'][S]['data_ptr'] +1
		cat = track['raw'][offset:offset+256]

		self.diskname = cat[9:30]
		# print dump(cat)

		P = 0
		S = 2
		track = self.read_track(P,0)
		offset = track['sectors'][S]['data_ptr'] +1
		cat = track['raw'][offset:offset+256]

		if ord(cat[22]) == 0:
			self.disktype = 'Master'
		elif ord(cat[22]) == 1:
			self.disktype = 'Slave'
		else:
			self.disktype = cat[22]

		return self.diskname

	def read_dir(self):
		self.dirents = self.SEDORIC_cat()
		return self.dirents


	def read_file(self, filename):
		return self.SEDORIC_read_file(filename)


	def _cat(self):
		if len(self.dirents) == 0:
			self.read_dir()

		for filename in sorted(self.dirents.keys()):
			print 'S:%01d P:%02d S:%02d %c %s %c %3d (%s)' % (
					self.dirents[filename]['side'],
					self.dirents[filename]['track'],
					self.dirents[filename]['sector'],
					self.dirents[filename]['lock'],
					filename,
					self.dirents[filename]['type'],
					self.dirents[filename]['size'],
					self.dirents[filename]['content_type'])

	def display_bitmap(self):
		P = 20
		S = 2

		track = self.read_track(P,0)
		offset = track['sectors'][S]['data_ptr'] +1
		raw = track['raw'][offset:offset+256]
		print dump(raw)

		S = 3
		offset = track['sectors'][S]['data_ptr'] +1
		raw2 = track['raw'][offset:offset+256]

		# Premier secteur BitMap
		#
		# Octets 00-01: FF 00 (cf sed à nu pp493)
		# 02-03: nombre de secteurs libres
		# 04-05: nombre de fichiers
		# 06   : nombre de pistes par face
		# 07   : nombre de secteurs par piste
		# 08   : nombre de secteurs du directory
		# 09   : idem 06 avec b7=0 pour simple face et b7=1 pour double face
		# 0A   : #$00: Master, #$01: Slave, #$47: Game
		# 0B-0F: #$00 inutilisés
		# 10-FF: Bitmap (b0: secteur1, b1: secteur1,...)

		Smax = struct.unpack('<H', raw2[0x02:0x04])[0]
		ST =  ord(raw[0x07:0x08])
		print 'Free sectors : %d / %d' % (struct.unpack('<H',raw[0x02:0x04])[0], Smax)
		print 'Files        : %d' % (struct.unpack('<H',raw[0x04:0x06])[0])
		print 'Tracks/Side  : %d' % (ord(raw[0x06:0x07]))
		print 'Sectors/Track: %d' % (ST)
		print 'Directory    : %d' % (ord(raw[0x08:0x09]))
		print 'Type         : %s' % (ord(raw[0x0A:0x0B]))
		print 'Side(s)      : %X' % (1+(ord(raw[0x09:0x0A])>>7))

		out = []
		for P in range(0, self.tracks):
			out.append('Track %02d: ' % P)

		bitmap = ''
		P = 0
		S = 0
		for offset in range(0x10, 0xff):

			if S < Smax:
				for i in range(0,8):

					if S < Smax:
						P = S / ST

						# print S, P, i
						if P >= self.tracks and S % ST == 0:
							out[P % self.tracks] += ' : '

						if ord(raw[offset:offset+1]) & 2**i == 2**i:
							out[P % self.tracks] += '. '
						else:
							out[P % self.tracks] += '* '

						S = S + 1

		# Second secteur BitMap
		#
		# 00:0F: Identique premier secteur sauf 02-03: Nombre total de secteurs
		# 10-FF: Bitmap suite

		for offset in range(0x10, 0xff):

			if S < Smax:
				for i in range(0,8):

					if S < Smax:
						P = S / ST

						if P >= self.tracks and S % ST == 0:
							out[P % self.tracks] += ' : '

						if ord(raw2[offset:offset+1]) & 2**i == 2**i:
							out[P % self.tracks] += '. '
						else:
							out[P % self.tracks] += '* '

						S = S + 1

		return out


	def SEDORIC_cat(self):
		dirents = {}

		# Recuperation du type de disque
		P = 20
		S = 2

		track = self.read_track(P,0)

		offset = track['sectors'][S]['data_ptr'] +1
		cat = track['raw'][offset:offset+256]

		if ord(cat[0]) != 0xff or ord(cat[1]) != 0x00:
			print "Erreur disque incorrect"

		free_sectors = struct.unpack('<H',cat[02:04])[0]
		files = struct.unpack('<H',cat[04:06])[0]
		tracks = ord(cat[6])
		sectors = ord(cat[7])
		dir_sectors = ord(cat[8])
		sides = 1
		sides_txt = 'S'
		if (ord(cat[9]) == tracks + 0x80):
			sides = 2
			sides_txt = 'D'

		disktype = ord(cat[10])
		if disktype == 0x00:
			disktype = 'Master'
		elif disktype == 0x01:
			disktype = 'Slave'
		else:
			disktype = chr(disktype)

		# print '***%d sectors free (%c/%d/%d) %d files (%s)' % (free_sectors, sides_txt, tracks, sectors, files, disktype)

		# Lecture premier secteur du catalogue S:0 P:20 S:4

		P=20
		S = 4
		while P+S != 0x00:
			#track = self.read_track(P,0)
			track = self.read_track(P & 0x7f, (P & 0x80) >> 7)

			offset = track['sectors'][S]['data_ptr'] +1
			cat = track['raw'][offset:offset+256]
			# print dump(cat)

			# Chainage vers le catalogue suivant
			P = ord(cat[0])
			S = ord(cat[1])
			entry_free = ord(cat[2])
			# print 'P:%d S:%d (first free entry: %d)' %(P, S, entry_free)

			for i in range(0,15):
				entry_offset = 16+i*16
				entry = SEDORIC_DirEntry(self, cat[entry_offset:entry_offset+16])
				if len(entry) >0:
					dirents[entry.keys()[0]] = entry.values()[0]

		return dirents

	def SEDORIC_read_file(self, filename):
		file = ''
		start = -1
		size = 0
		nb_sector = 0
		last_track_read = -1

		if self.dirents.has_key(filename):
			P_FCB = self.dirents[filename]['track']
			S_FCB = self.dirents[filename]['sector']
		
			# print '\n***read_file: %s (T: %d, S: %d)' % (filename, P_FCB, S_FCB)

			while (P_FCB + S_FCB) != 0x00:
				if P_FCB != last_track_read:
					#track = self.read_track(P_FCB,0)
					track = self.read_track(P_FCB & 0x7f, (P_FCB & 0x80) >> 7)
					last_track_read = P_FCB
				#else:
				#	print '***read_file: track already read (H: %d, T: %d, S:%d)' % ((P_FCB & 0x80) >> 7, P_FCB & 0x7f, S_FCB)

				offset = track['sectors'][S_FCB]['data_ptr'] +1
				cat = track['raw'][offset:offset+256]
				# print  map (lambda s: hex(s), struct.unpack('256B',cat))
				# print dump(cat)

				# Chainage vers le FCB suivant
				P_FCB = ord(cat[0])
				S_FCB = ord(cat[1])
				FCB01 = ord(cat[2])
				# Si 1er FCB: FCB01 == 0xff
				# Si il y a un FCB chaine, 02-... liste des secteurs suivants
				# (structure simplifiee)
				# print 'P:%d S:%d' %(P_FCB, S_FCB)

				print 'Fichier              : ', filename
				print 'FCB01                : %02X' % FCB01

				if (FCB01 == 0xff):
					# Uniquement pour le premier FCB
					type = ord(cat[3])
					start = struct.unpack('<H',cat[4:6])[0]
					end = struct.unpack('<H',cat[6:8])[0]
					exec_addr = struct.unpack('<H',cat[8:10])[0]
					sector_count = struct.unpack('<H', cat[10:12])[0]

					type_text = []
					if type & 0x01 == 0x01:
							type_text.append('Autoexec')
					if type & 0x08 == 0x08:
							type_text.append('Direct')
					if type & 0x10 == 0x10:
							type_text.append('Sequentiel')
					if type & 0x20 == 0x20:
							type_text.append('Windows')
					if type & 0x40 == 0x40:
							type_text.append('Data')
					if type & 0x80 == 0x80:
							type_text.append('Basic')

					# start = Adresse de debut ou nombre de fiches pour fichier a acces direct
					# end  = Adresse de fin ou longueur d'une fiche pour fichier a acces direct
					if type & 0x08 == 0x08:
						record_number = start
						record_size = end
						start = record_size
						size = record_number * record_size
						print 'Nombre de fiches     : ', record_number
						print 'Longueur d une fiche : ', record_size

					else:
						size = end - start +1
						print 'Adresse de chargement: ', hex(start)
						print 'Adresse de fin       : ', hex(end)

					print 'Taille               : ', size
					print 'Type                 :  %x (%s)' % (type, ','.join(type_text))
					print 'Addresse Execution   : ', hex(exec_addr)
					print 'Nombre de secteurs   : ', sector_count
					print
					n = 0x0c

				else:
					n = 2

				P = 0
				S = 0
				while (n <= 254) and (nb_sector < sector_count):
					P = ord(cat[n])
					S = ord(cat[n+1])
					n += 2

					if P + S != 0x00 and nb_sector < sector_count:
						nb_sector += 1
						if P != last_track_read:
							# print 'Lecture P:%d S:%d' % (P,S)
							track = self.read_track(P & 0x7f, (P & 0x80) >> 7)
							last_track_read = P
						#else:
						#	print '***read_file: track already read (H: %d, T: %d, S:%d)' % ((P & 0x80) >> 7, P & 0x7f, S)

						offset = track['sectors'][S]['data_ptr'] +1
						# print dump(track['raw'][offset:offset+256])
						file += track['raw'][offset:offset+256]

		return {'file': file[0:size], 'start': start, 'size': size}



def CreateDisk():

	diskimg = oricdsk()
	diskimg.sides= 2
	diskimg.tracks = 41
	diskimg.sectors = 17
	diskimg.geometry = 1
	diskimg.signature = 'MFM_DISK'
	diskimg.crc = 0
	diskimg.trackbuf = []
	diskimg.ptr_track = 0

	diskimg.newdisk('test.dsk','EMPTY')


def main():
	print sys.argv[1]

	fs = sedoric()
	fs.source = sys.argv[1]
	test = 0

	try:
		fs.source = os.path.abspath(fs.source)

		with open(fs.source,'rb') as f:
			fs.signature = f.read(8)
			if fs.signature != 'MFM_DISK':
				print "Erreur signature '%s' incorrecte pour %s" % (fs.signature, fs.source)
				sys.exit(1)

			track = fs.read_track(0,0)
			offset = track['sectors'][1]['data_ptr'] +1
			dos = track['raw'][offset:offset+256][24:32].rstrip()
			# dos = track['sectors'][0][24:32].rstrip()

			if dos in ['XL DOS', 'SEDORIC', 'RADOS', 'ORICDOS']:
				fs.dos = dos
			else:
				fs.dos = 'FTDOS'

			fs.read_diskname()

			fs.sectors = len(track['sectors'])
			fs.offset = 0x100
			fs.sides = struct.unpack("<L", f.read(4))[0]
			fs.tracks = struct.unpack("<L", f.read(4))[0]
			fs.geometry = struct.unpack("<L",f.read(4))[0]

			print 'Signature: ', fs.signature
			print 'DOS      : ', fs.dos
			print 'Faces    : ', fs.sides
			print 'Pistes   : ', fs.tracks
			print 'Secteurs : ', fs.sectors
			print 'Geometrie: ', fs.geometry
			print 'Offset   : ', fs.offset
			print ''
			print '   VOLUME : %s (%s)' % (fs.diskname, fs.disktype)
			print ''

		f.close()

		if fs.dos == 'SEDORIC':

			print 'DOS      : %s' % (dos)

			# fs.display_bitmap()

			cat = fs.read_dir()

			#cat = fs.read_file('COPY    .CMD')['file']
			#print dump(cat)

			#P = 20
			#track = fs.read_track(P,0)
			#for S in range(1,fs.sectors+1):
			#	offset = track['sectors'][S]['data_ptr'] +1
			#	cat = track['raw'][offset:offset+256]
			#	l = len(cat)
			#	# print  map (lambda s: hex(s), struct.unpack('%dB' % l,cat[0:l]))
			#	print 'P:%d S:%d' % (P, S)
			#	print dump(cat)
                
			# pprint(cat)
			fs._cat()

			for fn in cat.keys():
				print
				raw = fs.read_file(fn)
				pprint(raw)

	except AttributeError, e:
		print "Erreur", e
		sys.exit(1)

if __name__ == '__main__':
	main()

# __init__()


