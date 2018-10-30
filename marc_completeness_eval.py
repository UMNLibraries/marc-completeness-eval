'''
This script scores each record in either all MARC binary files in a directory, or a single
file input by the user based on the presence or absence of several elements, and 
calculates mean and standard deviation across all record scores in a file. Outputs: 
one .csv file per MARC file evaluated.
'''

import os
import re
import pandas as pd
from pymarc import MARCReader, MARCWriter, Record


def rec_eval(file):

	with open(file,'rb') as f:

		reader = MARCReader(f)

		record_dict = {}

		rec_count = 0

		for rec in reader:
			
			#get record elements for completness evaluation
			rec_id = rec.get_fields('001')
			field_008 = rec.get_fields('008')
			isbn = rec.get_fields('020')
			rec_source = rec.get_fields('040')
			classif = rec.get_fields('050', '060', '090')
			authors = rec.get_fields('100', '110', '111')
			title = rec.get_fields('245')
			alt_titles = rec.get_fields('246')
			edition = rec.get_fields('250')
			imprint = rec.get_fields('260', '264')
			descr = rec.get_fields('300')
			toc = rec.get_fields('505')
			abstract = rec.get_fields('520')
			subjects = rec.get_fields('600', '610', '611', '630',
				'650', '651', '653')
			contribs = rec.get_fields('700', '710', '711', '720')
			series = rec.get_fields('440', '490', '800', '810', '830')

			rec_qualities = {}

			#extract value of 001 field
			record_id = str(rec_id[0]).lstrip('=001  ')

			#add simple count to dict for some elements
			rec_qualities['isbn_count'] = len(isbn)
			rec_qualities['authors'] = len(authors)
			rec_qualities['alt_titles'] = len(alt_titles)
			rec_qualities['edition'] = len(edition)
			rec_qualities['contribs'] = len(contribs)
			rec_qualities['series'] = len(series)

			#check for toc and abstract
			if toc and abstract:
				rec_qualities['toc_abstract'] = 2
			elif toc or abstract:
				rec_qualities['toc_abstract'] = 1
			else:
				rec_qualities['toc_abstract'] = 0

			#get dates from 008 and 26X if they exist
			date_008 = re.findall('^.{13}([0-9]{2}[0-9u]{2}).*$', str(field_008[0]))
			rec_qualities['date_008'] = len(date_008)
			if not date_008:
				date_008 = [1111]
			
			date_imprint = ['0']
			rec_qualities['date_26X'] = 0
			if imprint:
				subf_c_26X = [field.get_subfields('c') for field in imprint]
				try:
					date_imprint_list = re.findall('^.*(\d{4}).*$', str(subf_c_26X[0]))
					date_imprint[0] = date_imprint_list[0]
					rec_qualities['date_26X'] = 1
				except IndexError:
					date_imprint = ['0']

			try:
				date_008_int = int(date_008[0])
			except ValueError:
				date_008_int = 1111

			#evaluate whether 008 and 26X dates match
			if date_008_int == int(date_imprint[0]):
				rec_qualities['dates_matched'] = 1
			else:
				rec_qualities['dates_matched'] = 0

			#check for LC or NLM classification
			if classif:
				rec_qualities['classification'] = 1
			else:
				rec_qualities['classification'] = 0

			#parse and count subject fields based on indicators and vocabulary codes
			lcsh_count = 0
			mesh_count = 0
			fast_count = 0
			othersub_count = 0
			lcsh_re = re.compile('^.{7}0.*$')
			mesh_re = re.compile('^.{7}2.*$')
			fast_re = re.compile('^.{7}7.*2fast.*$')
			for subj in subjects:
				if lcsh_re.match(str(subj)):
					lcsh_count += 1
				elif mesh_re.match(str(subj)):
					mesh_count += 1
				elif fast_re.match(str(subj)):
					fast_count += 1
				else:
					othersub_count += 1
			if lcsh_count < 10:
				rec_qualities['subjects_lcsh'] = lcsh_count
			else:
				rec_qualities['subjects_lcsh'] = 10
			if mesh_count < 10:
				rec_qualities['subjects_mesh'] = mesh_count
			else:
				rec_qualities['subjects_mesh'] = 10
			if fast_count < 10:
				rec_qualities['subjects_fast'] = fast_count
			else:	
				rec_qualities['subjects_fast'] = 10
			if othersub_count < 5:
				rec_qualities['subjects_other'] = othersub_count
			else:
				rec_qualities['subjects_other'] = 5

			#check if rec describes resource as online
			online_rsrc_re = re.compile('^.*online.resource.*$')
			online_008_re = re.compile('^.{29}o.*$')
			for field in descr:
				subf_a_300 = field.get_subfields('a')
				if online_rsrc_re.match(str(subf_a_300)) and online_008_re.match(str(field_008[0])):
					rec_qualities['descr'] = 2
				elif online_rsrc_re.match(str(subf_a_300)) or online_008_re.match(str(field_008[0])):
					rec_qualities['descr'] = 1
				else:
					rec_qualities['descr'] = 0

			#check if resource language code exists
			rsrc_lang_re = re.compile('^.{41}[a-z]{3}.*$')
			if rsrc_lang_re.match(str(field_008[0])):
				rec_qualities['rsrc_lang'] = 1
			else:
				rec_qualities['rsrc_lang'] = 0

			#check if country code exists
			ctry_code_re = re.compile('^.{21}([a-z]{2})|([a-z]{3}).*$')
			if ctry_code_re.match(str(field_008[0])):
				rec_qualities['ctry_code'] = 1
			else:
				rec_qualities['ctry_code'] = 0

			#check language of cataloging and explicit rda status
			cat_lang_re = re.compile('^.*eng.*$')
			rda_re = re.compile('^.*erda.*$')
			for field in rec_source:
				subf_b_040 = field.get_subfields('b')
				if subf_b_040 and not cat_lang_re.match(str(subf_b_040)):
					rec_qualities['cat_lang'] = 0
				else:
					rec_qualities['cat_lang'] = 1
				if rda_re.match(str(field)):
					rec_qualities['rda'] = 1
				else:
					rec_qualities['rda'] = 0

			rec_score = 0
			for k, v in rec_qualities.items():
				rec_score = rec_score + v
			rec_qualities['total_rec_score'] = rec_score

			record_dict[record_id] = rec_qualities

			rec_count += 1

	return record_dict, rec_count

			
def record_dict_to_csv(record_dict, record_count, fpref):
	with open(fpref + '_completeness.csv', 'w') as out:

		#make dataframe from record_dict and replace NaN values
		df = pd.DataFrame.from_dict(record_dict, orient='index')
		df = df.fillna(value=0)

		#calculate mean and standard deviation
		mean_rec_score = df['total_rec_score'].mean()
		std_dev = df['total_rec_score'].std()

		#glom record count, mean, and stdev onto record_dict dataframe and reformat for eye-readability
		df_mean = df.set_value('Mean Record Score', 'mean', mean_rec_score)
		df_calcs = df_mean.set_value('Standard Deviation', 'stdev', std_dev)
		df_calcs = df_calcs.set_value('Record Count', 'count', record_count)
		df_calcs = df_calcs[['mean', 'stdev', 'count', 'total_rec_score', 'isbn_count', 'cat_lang', 'rsrc_lang','rda', 'classification', 'authors','alt_titles', 'edition', 'toc_abstract','contribs', 'series', 'ctry_code', 'date_008', 'date_26X', 'dates_matched','descr', 'subjects_lcsh','subjects_mesh', 'subjects_fast', 'subjects_other']]
		df_calcs = df_calcs.sort_values(['mean', 'stdev', 'count'])
		df_calcs.to_csv(out)
	
	return df


def main():
	
	#ask user which files to evaluate
	getfiles = input("Evaluate all .mrc files in directory y/n?")
	if getfiles == 'y':
		files = [f for f in os.listdir() if re.match(r'.+\.mrc', f)]
	else:
		files = []
		file = input("Enter the .mrc filename to evaluate: ")
		files.append(file)

	#function calls
	for file in files:
		fpref, fsuf = file.split('.')
		record_dict, record_count = rec_eval(file)
		record_dict_to_csv(record_dict, record_count, fpref)

if __name__ == "__main__":
	main()
