# -*- coding: utf-8 -*-

import json
import sqlite3
import re

def esami_output(item, sessions):

	output = "*Insegnamento:* " + item["insegnamento"]
	output += "\n*Docenti:* " + item["docenti"]

	for session in sessions:
		appeals = item[session]
		if appeals:
			appeals = str(appeals)			
			appeals = re.sub(r"(?P<ora>([01]?\d|2[0-3]):[0-5][0-9])(?P<parola>\w)", r"\g<ora> - \g<parola>", appeals) #aggiunge un - per separare orario e luogo dell'esame
			appeals = appeals.split("', '") #separa i vari appelli della sessione
			for i, appeal in enumerate(appeals):
				appeals[i] = re.sub(r"[\['\]]", "", appeal) #elimina eventuali caratteri [ ' ] rimasti
			if "".join(appeals) != "":
				output += "\n*" + session.title() + ":*\n" + "\n".join(appeals)

	output += "\n*CDL:* " + item["cdl"]
	output += "\n*Anno:* " + item["anno"] + "\n"

	return output

def esami_condition(items, field, value, session = False):
	output = set()

	if field == "anno":
		years = {
			"primo": "1° anno",
			"secondo": "2° anno",
			"terzo": "3° anno"
		}
		value = years[value]

	if session:
		for item in items:
			if ([appeal for appeal in item[value] if appeal]):
				output.add(esami_output(item, [value]))
	else:
		for item in items:
			if(value in item[field].lower()):
				output.add(esami_output(item, ("prima", "seconda", "terza", "straordinaria")))

	return output

def check_output(output):
	if len(output):
		output_str = '\n'.join(list(output))
		output_str += "\nRisultati trovati: " + str(len(output))
	else:
		output_str = "Nessun risultato trovato :(\n"

	return output_str

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def esami_cmd(args):
	output_str = "Inserisci un parametro valido\n"

	if args:
		output = set()

		conn = sqlite3.connect('data/DMI_DB.db')
		conn.row_factory = dict_factory
		cur = conn.cursor()
		cur.execute("SELECT * FROM exams")
		items = cur.fetchall()
		conn.close()

		# Clear arguments - Trasform all to lower case - Remove word 'anno', 'sessione'
		args = [x.lower() for x in args if len(x) > 2]
		if 'anno' in args:
			args.remove('anno')

		if 'sessione' in args:
			args.remove('sessione')

		# Study case
		if len(args) == 1:

			if args[0] in ("primo", "secondo", "terzo"):
				output = esami_condition(items, "anno", args[0])

			elif args[0] in ("prima", "seconda", "terza", "straordinaria"):
				output = esami_condition(items, "sessione", args[0], True)

			elif [item["insegnamento"].lower().find(args[0]) for item in items]:
				output = esami_condition(items, "insegnamento", args[0])

			output_str = check_output(output)

		elif len(args) > 1:

			# Create an array of session and years if in arguments
			sessions = list(set(args).intersection(("prima", "seconda", "terza", "straordinaria")))
			years = list(set(args).intersection(("primo", "secondo", "terzo")))

			_years = {
				"primo": "1° anno",
				"secondo": "2° anno",
				"terzo": "3° anno"
			}
			for i in range(len(years)):
				years[i] = _years[years[i]]

			if sessions and years:
				for item in items:
					if (item["anno"] in years) and ([session for session in sessions if [appeal for appeal in item[session] if appeal]]):
						output.add(esami_output(item, sessions))

			elif sessions and not years:
				# If years array is empty and session not, the other word are subjects
				subjects = [arg for arg in args if arg not in(sessions)]

				if subjects:
					for item in items:
						for subject in subjects:
							if [session for session in sessions if [appeal for appeal in item[session] if appeal]] and subject in item["insegnamento"].lower():
								output.add(esami_output(item, sessions))

			elif not sessions and not years:
				for arg in args:
					output = output.union(esami_condition(items, "insegnamento", arg))

			output_str = check_output(output)
	else:
		output_str = "Inserisci almeno uno dei seguenti parametri: giorno, materia, sessione (prima, seconda, terza, straordinaria)."

	return output_str
