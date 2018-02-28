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
__description__ = "Extract files from Sedoric disk image"
__plugin_type__ = 'OS'
__version__ = '0.4'

ORIC_SEDORIC_VERSION = '0.4'

from utils import dump
from transform import transform

from pprint import pprint

#import time

#import stat    # for file properties
import os      # for filesystem modes (O_RDONLY, etc)
#import errno   # for error number codes (ENOENT, etc)
               # - note: these must be returned as negatives

#from math import ceil
#import getpass
import sys
import struct

import argparse
import fnmatch

def SEDORIC_DirEntry(self, entry):
	# name = entry[0:12]
	name = entry[0:9] + '.' + entry[9:12]
	stripped_name = entry[0:9].rstrip()
	stripped_ext = entry[9:12].rstrip()
	if stripped_ext > '':
		stripped_name = stripped_name + '.' + stripped_ext

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

		return {name: {'stripped_name': stripped_name, 'side': side, 'track': P_FCB, 'sector': S_FCB, 'lock': lock, 'type': type, 'size': size, 'content_type': content_type}}

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
			print 'S:%01d P:%03d S:%02d        %c %s %3d   %02X (%s)' % (
					self.dirents[filename]['side'],
					self.dirents[filename]['track'],
					self.dirents[filename]['sector'],
					self.dirents[filename]['lock'],
					filename,
					self.dirents[filename]['size'],
					self.dirents[filename]['type'],
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


def main(diskname, pattern):
	fs = sedoric()
	fs.source = diskname
	pattern = pattern.upper()

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

			# fs.display_bitmap()

			cat = fs.read_dir()
			# pprint(cat)

			fs._cat()

			for fn in cat.keys():
				if fnmatch.fnmatch(cat[fn]['stripped_name'],pattern):
					print
					raw = fs.read_file(fn)
					pprint(raw)

	except IOError, e:
		print "Erreur", e
		sys.exit(1)




if __name__ == '__main__':
	# parser = argparse.ArgumentParser(prog='sedoric', description='Extract files from sedoric image disk', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser = argparse.ArgumentParser(description = __description__ , formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	# parser.add_argument('diskname', type=argparse.FileType('rb'), help='Disk image file')
	parser.add_argument('diskname', type=str, help='Disk image file')
	parser.add_argument('file', type=str, nargs='*', metavar='file', default=['*.*'], help='file(s) to extract')
	# parser.add_argument('--output', '-o', type=argparse.FileType('wb'), default=sys.stdout, help='MAP filename')
	parser.add_argument('--output', '-o', type=argparse.FileType('wb'), default=None, help='MAP filename')
	parser.add_argument('--version', '-v', action='version', version= '%%(prog)s v%s' % __version__)

	args = parser.parse_args()

	main(args.diskname, args.file[0])

