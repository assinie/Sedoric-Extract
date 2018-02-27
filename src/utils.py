#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# vim: set ts=4 ai :
#
# $Id: utils.py $
# $Author: assinie <github@assinie.info> $
# $Date: 2018-02-27 $
# $Revision: 0.1 $
#
#------------------------------------------------------------------------------


#
#	Ok pour SEDORIC2, Pb avec SEDORIC3, a voir...
#

ORIC_UTILS_VERSION = '0.1'


FILTER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

def dump(src, offset=0, length=16):
	N=0; result=''
	while src:
		s,src = src[:length],src[length:]
		hexa = ' '.join(["%02X"%ord(x) for x in s])
		s = s.translate(FILTER)
		result += "%04X   %-*s   %s\n" % (N+offset, length*3, hexa, s)
		N+=length
	return result

def bin2float(b):

	# Pour eviter un calcul inutile qui donne 1.4693679385278594e-39
	# a la place de 0...
	if b[0]+b[1]+b[2]+b[3]+b[4] == 0:
		return 0

	exposant = b[0] - 0x80
	signe = 1-2*(b[1] >= 0x80)
	mantisse = 0.0

	b[1] |= 0x80

 	for i in range(1,5):
		for j in range(0,8):
			if b[i] & 2**(7-j) == 2**(7-j):
				mantisse += 2**(-((i-1)*8+j+1))


	# print 'Exposant = %d, Signe Mantise = %d, Mantise =%f' % (exposant, signe, mantisse)
	# print 'Valeur=', signe*mantisse*2**exposant

	return signe*mantisse*2**exposant


