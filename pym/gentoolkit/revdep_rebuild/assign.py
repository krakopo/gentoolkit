#!/usr/bin/python

"""Assign module
Functions used for determining the package the broken lib belongs to.
"""

from __future__ import print_function

import os
import re

import portage
from portage import portdb
from portage.output import bold, red, yellow

# Make all str conversions unicode
try:
	str = unicode
except NameError:
	pass

def assign_packages(broken, logger, settings):
	''' Finds and returns packages that owns files placed in broken.
		Broken is list of files
	'''
	assigned_pkgs = set()
	assigned_filenames = set()
	for group in os.listdir(settings['PKG_DIR']):
		grppath = settings['PKG_DIR'] + group
		if not os.path.isdir(grppath):
			continue
		for pkg in os.listdir(grppath):
			pkgpath = settings['PKG_DIR'] + group + '/' + pkg
			if not os.path.isdir(pkgpath):
				continue
			f = pkgpath + '/CONTENTS'
			if os.path.exists(f):
				try:
					with open(f, 'r') as cnt:
						for line in cnt.readlines():
							m = re.match('^obj (/[^ ]+)', line)
							if m is not None:
								m = m.group(1)
								if m in broken:
									found = group+'/'+pkg
									assigned_pkgs.add(found)
									assigned_filenames.add(m)
									logger.info('\t' + m + ' -> ' + bold(found))
				except Exception as e:
					logger.warn(red(' !! Failed to read ' + f))
					logger.warn(red(' !! Error was:' + str(e)))

	broken_filenames = set(broken)
	orphaned = broken_filenames.difference(assigned_filenames)

	return (assigned_pkgs, orphaned)


def get_best_match(cpv, cp, logger):
	"""Tries to find another version of the pkg with the same slot
	as the deprecated installed version.  Failing that attempt to get any version
	of the same app

	@param cpv: string
	@param cp: string
	@rtype tuple: ([cpv,...], SLOT)
	"""

	slot = portage.db[portage.root]["vartree"].dbapi.aux_get(cpv, ["SLOT"])
	logger.warn(yellow('Warning: ebuild "' + cpv + '" not found.'))
	logger.info('Looking for %s:%s' %(cp, slot))
	try:
		match = portdb.match('%s:%s' %(cp, slot))
	except portage.exception.InvalidAtom:
		match = None

	if not match:
		logger.warn(red('!!') + ' ' + yellow(
			'Could not find ebuild for %s:%s' %(cp, slot)))
		slot = ['']
		match = portdb.match(cp)
		if not match:
			logger.warn(red('!!') + ' ' +
				yellow('Could not find ebuild for ' + cp))
	return match, slot


def get_slotted_cps(cpvs, logger):
	"""Uses portage to reduce the cpv list into a cp:slot list and returns it
	"""
	from portage.versions import catpkgsplit
	from portage import portdb

	cps = []
	for cpv in cpvs:
		parts = catpkgsplit(cpv)
		cp = parts[0] + '/' + parts[1]
		try:
			slot = portdb.aux_get(cpv, ["SLOT"])
		except KeyError:
			match, slot = get_best_match(cpv, cp, logger)
			if not match:
				logger.warn(red("Installed package: "
					"%s is no longer available" %cp))
				continue

		if slot[0]:
			cps.append(cp + ":" + slot[0])
		else:
			cps.append(cp)

	return cps



if __name__ == '__main__':
	print('Nothing to call here')