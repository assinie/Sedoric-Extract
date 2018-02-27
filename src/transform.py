#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# vim: set ts=4 ai :
#
# $Id$
# $Author$
# $Date$
# $Revision$
#
#------------------------------------------------------------------------------

__plugin_name__ = 'sedoric'
__version__ = 0.1
__description__ = "Gestion des images Sedoric"
__plugin_type__ = "transform"

ORIC_SEDROIC_VERSION = '0.1'

from utils import dump, bin2float

#import time

#import stat    # for file properties
#import os      # for filesystem modes (O_RDONLY, etc)
#import errno   # for error number codes (ENOENT, etc)
               # - note: these must be returned as negatives

#import getpass
#import sys
import struct


def __init_plugin__():
		print "%s.__init_plugin__()" % __name__

def __setup__():
		return transform()


class transform():

	def lscreen(self, filename, dirent):
		file = dirent['content']['file']

		fileText = ''

		# 0: black
		# 1: red
		# 2: green
		# 3: yellow
		# 4: blue
		# 5: magenta
		# 6: cyan
		# 7: white

		if len(file) < 40*28:
			return fileText

		# print len(file)

		for i in range(0,28):
			for j in range(0,40):
				c = ord(file[i*40+j])

				if c>= 0x10 and c <= 0x17:
					bg = chr(27)+'[1;'+str(c-16+40)+'m'
					char = bg + ' '
				elif c >= 0 and c <= 0x07:
					fg = chr(27)+'[1;'+str(c+30)+'m'
					char = fg + ' '
				elif c >= 0x08 and c <= 0x0b:
					# Affichage fixe
					char = chr(27)+'[25m '
				elif c >= 0x0c and c <= 0x0f:
					# Affichage clignotant
					char = chr(27)+'[5m '

				# Specifique Sedoric
				elif c == ord('`'):
					# (c)
					char = chr(184)
				elif c == ord('@'):
					char = 'à'
				elif c == ord('{'):
					char = 'é'
				elif c == ord('}'):
					char = 'è'
				elif c == ord('~'):
					char = 'ê'
				elif c == ord('|'):
					char = 'ù'
				elif c == ord('\\'):
					char = 'ç'
				elif c == 0x7f:
					char = chr(27)+'[7m '+ chr(27) + '[0m' + bg + fg

				else:
					char = chr(c)

				fileText += char

			fileText += chr(27) + '[0m'+"\n"

		return fileText

	def Windows(self, filename, dirent):
		file = dirent['content']['file']

		fileText = ''

		# 0: black
		# 1: red
		# 2: green
		# 3: yellow
		# 4: blue
		# 5: magenta
		# 6: cyan
		# 7: white

		for i in range(0,len(file)/40):
			for j in range(0,40):
				c = ord(file[i*40+j])

				if c>= 0x10 and c <= 0x17:
					bg = chr(27)+'[1;'+str(c-16+40)+'m'
					char = bg + ' '
				elif c >= 0 and c <= 0x07:
					fg = chr(27)+'[1;'+str(c+30)+'m'
					char = fg + ' '
				elif c >= 0x08 and c <= 0x0b:
					# Affichage fixe
					char = chr(27)+'[25m '
				elif c >= 0x0c and c <= 0x0f:
					# Affichage clignotant
					char = chr(27)+'[5m '

				# Specifique Sedoric
				elif c == ord('`'):
					# (c)
					char = chr(184)
				elif c == ord('@'):
					char = 'à'
				elif c == ord('{'):
					char = 'é'
				elif c == ord('}'):
					char = 'è'
				elif c == ord('~'):
					char = 'ê'
				elif c == ord('|'):
					char = 'ù'
				elif c == ord('\\'):
					char = 'ç'
				elif c == 0x7f:
					char = chr(27)+'[7m '+ chr(27) + '[0m' + bg + fg

				else:
					char = chr(c)

				fileText += char

			fileText += chr(27) + '[0m'+"\n"

		return fileText

	def data(self, filename, dirent):
		file = dirent['content']['file']
		offset = dirent['content']['start']

		if offset == 0xbb80 and len(file) == 1120:
			return self.lscreen(filename, dirent)

		return dump(file, offset)

	def Direct(self, filename, dirent):
		src = dirent['content']['file']
		length = dirent['content']['start']

		fileText = ''
		nb = 0

		while src:
			record,src = src[:length],src[length:]
			i = 0
			fileText += '#%d\n' % nb
			while i < len(record):
				delim = ord(record[i])
				field_len = ord(record[i+1])
				field = record[i+2:i+2+field_len]
				i += 2 +field_len
				fileText += field + '\n'

			fileText += '-----------------\n'
			nb += 1

		return  fileText
