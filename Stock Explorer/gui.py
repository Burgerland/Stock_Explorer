import psycopg2
import Tkinter as tk
import ttk
from operator import itemgetter
from Tkinter import *
from ttk import *


#connect to postgres
try:
	try:
		conn = psycopg2.connect("dbname='sandp500' user='postgres' host='localhost' password='password'")
	except:
		print "please run setup.py"
		exit()

	cur = conn.cursor()
	cur.execute("SELECT * FROM good_stocks")
	stocks = [r[0] for r in cur.fetchall()]
except:
	print cur.statusmessage
	print "can't connect to database"
	exit()


#set up dates
end = "'2018-02-07'"
start_dates = ["'2018-01-08'", "'2017-11-07'",
	"'2017-08-07'", "'2017-02-07'",
	"'2016-02-08'", "'2013-02-08'"]

#set up bases
base_entries = ["open", "high", "low", "close", "volume"]

#comparators used
functions = ["MAX", "MIN", "DESC" , "ASC" , ">", "<"]

#function called by button, fetches and displays results
def update_Display():
	#clear old results
	result.delete(1,'end')
	error.delete(0,'end')

	#gets and displays high/low values
	if sort.current() < 2:
		results = get_value(base_entries[base.current()],
				functions[sort.current()],
				start_dates[time.current()])
		value_print(results)

	#gets and displays high gains/losses
	elif sort.current() < 4:
		results = get_gains(base_entries[base.current()],
				functions[sort.current()],
				start_dates[time.current()])
		gains_print(results)

	#gets and displays high percentage gain/loss
	else:
		results = get_percent(base_entries[base.current()],
				functions[sort.current()],
				start_dates[time.current()])
		percent_print(results)
	return

#returns the rows sorted by highest value based on column
def get_value(based, func, start):
	results = []
	#for every stock
	for stock in stocks:
		#find the highest value going back to the start date
		search_string = ("SELECT * FROM " + stock + " WHERE " + based + "=" +
				"(SELECT " + func + "(" + based + ") FROM "+ stock + 
				" WHERE (date > " + start + " AND date < " + end + "))")

		
		cur.execute(search_string)

		#place result into list
		result = cur.fetchone()
		results.append(result)
	
	#determine index to search on
	if based == "open":
		index = 1
	elif based == "high":
		index = 2
	elif based == "low":
		index = 3
	elif based == "close":
		index = 4
	elif based == "volume":
		index = 5

	#search for min or max values
	if func == "MAX":
		results.sort(key=itemgetter(index))
	elif func == "MIN":
		results.sort(key=itemgetter(index), reverse=TRUE)

	return results

#gets the stocks with the highest gains or losses
def get_gains(based, func, start):
	#stores the results
	results = []

	#create a temporary table to collect data
	cur.execute("CREATE TABLE temp ("
		"open NUMERIC(10,2), " +
		"high NUMERIC(10,2), " +
		"low NUMERIC(10,2), "  +
		"close NUMERIC(10,2), "+
		"volume INTEGER, " +
		"name TEXT PRIMARY KEY)")
	
	#for every stock
	for stock in stocks:
		#get todays data
		cur.execute("SELECT * FROM " + stock + " WHERE date = " + end)
		final = cur.fetchone()

		#get past data
		cur.execute("SELECT * FROM " + stock + " WHERE date = " + start)
		initial = cur.fetchone()
		
		#insert a row with the difference into the temporary table
		try:
			cur.execute("INSERT INTO temp VALUES(CAST(" +
				str(final[1] - initial[1]) + " AS NUMERIC(10,2)), CAST(" +
				str(final[2] - initial[2]) + " AS NUMERIC(10,2)), CAST(" +
				str(final[4] - initial[3]) + " AS NUMERIC(10,2)), CAST(" +
				str(final[4] - initial[4]) + " AS NUMERIC(10,2)), CAST(" +
				str(final[5] - initial[5]) + " AS INTEGER), " +
				"'" +stock + "')")
		except:
			#handle errors
			error.insert(1,"couldn't get data for " + stock)
		
	#get results
	cur.execute("SELECT * FROM temp")
	results = cur.fetchall()

	#determine index for sorting
	if based == "open":
		index = 0
	elif based == "high":
		index = 1
	elif based == "low":
		index = 2
	elif based == "close":
		index = 3
	elif based == "volume":
		index = 4

	#sort results depending on user input
	if func == "DESC":
		results.sort(key=itemgetter(index))
	elif func == "ASC":
		results.sort(key=itemgetter(index), reverse=TRUE)

	#drop temporary table
	cur.execute("DROP TABLE temp")	

	return results

#not working, I think it is a type issue
def get_percent(based, func, start):
	results = []

	#determing which index of the tuple to work with
	if based == "open":
		index = 0
	elif based == "high":
		index = 1
	elif based == "low":
		index = 2
	elif based == "close":
		index = 3
	elif based == "volume":
		index = 4
	
	#for all stocks in database
	for stock in stocks:
		try:
			#get today's data
			cur.execute("SELECT * FROM " + stock + " WHERE date = " + end)
			final = cur.fetchone()

			#get past data
			cur.execute("SELECT * FROM " + stock + " WHERE date = " + start)
			initial = cur.fetchone()

			#result increase/loss = 100 *(final-initial)/initial)
			#ex:    100% increase = 100 * ((180 - 90) / 90)
			#formatted to precision 3			 
			op = ('{:.3f}'.format(100*	((final[1]-initial[1]) / initial[1])	))
			hi = ('{:.3f}'.format(100*	((final[2]-initial[2]) / initial[2])	))
			lo = ('{:.3f}'.format(100*	((final[3]-initial[3]) / initial[3])	))
			cl = ('{:.3f}'.format(100*	((final[4]-initial[4]) / initial[4])	))
			vl = ('{:.3f}'.format(100*	((final[5]-initial[5]) / initial[5])	))
			st = ("'" +stock + "')")
			#only store on decrease if checking loss
			if((final[index] < initial[index]) & (func == "<")):
				results.append((op, hi, lo, cl, vl, st))
			#only store on increase if checking gain
			if((final[index] > initial[index]) & (func == ">")):
				results.append((op, hi, lo, cl, vl, st))
		except:
			#print to the error messages
			error.insert(1, "couldn't get data for " + stock)

	#sort results
	if func == ">":
		results.sort(key=itemgetter(index))
	elif func == "<":
		results.sort(key=itemgetter(index), reverse=TRUE)

	return results

#print functions called when checking percent gain/loss
def percent_print(results):
	#add results to listbox
	#print ten items
	for i in range(2,12):
		#get max item off top of sorted list
		item = results.pop()
		#convert tuple to list
		s = []
		for element in item:
			convert = str(element)
			s.append(convert)

		#format output for columns
		for j in range(0,4):
			s[j] = "{}%".format(s[j])
			s[j] = "{:>{width}}|".format(s[j], width = (20-len(s[j])))
		s[4] = "{:>{width}}|".format(s[4], width = (20-len(s[4])))
		s[5] = "  {:<}".format(s[5])	
		line = "|                "+s[0] + s[1] + s[2] + s[3] + s[4] + s[5]
		#insert into listboxt
		result.insert(i, line)
	return

#print function called when checking numeric gain/loss
#same as percent print, but adds the dollar sign instead of a percent symbol
def gains_print(results):
	for i in range(2,12):
		item = results.pop()
		s = []
		for element in item:
			convert = str(element)
			s.append(convert)

		#format output for columns
		for j in range(0,4):
			s[j] = "${}".format(s[j])
			s[j] = "{:>{width}}|".format(s[j], width = (20-len(s[j])))
		s[4] = "{:>{width}}|".format(s[4], width = (20-len(s[4])))
		s[5] = "  {:<}".format(s[5])	
		line = "|                  "+s[0] + s[1] + s[2] + s[3] + s[4] + s[5]
		result.insert(i, line)
	return


#same as gain_print, but includes the date field to format and print
def value_print(results):
	#add results to listbox
	for i in range(2, 12):
		item = results.pop()
		s = []
		for element in item:
			convert = str(element)
			s.append(convert)

		#format output for columns
		s[0] = "{:>{width}}|".format(s[0], width = (20-len(s[0])))
		for j in range(1,5):
			s[j] = "${}".format(s[j])
			s[j] = "{:>{width}}|".format(s[j], width = (20-len(s[j])))
		s[5] = "{:>{width}}|".format(s[5], width = (20-len(s[5])))
		s[6] = "  {:<}".format(s[6])	
		line = s[0] + s[1] + s[2] + s[3] + s[4] + s[5] + s[6]
		result.insert(i, line)
	
	return

#frame declaration
app = tk.Tk() 
app.title('Stock Exchange')
app.geometry('600x600')

#Sort-by menu
sortLabel = tk.Label(app, text = "Sort By:")
sortLabel.place(x=10, y=10)
sort = ttk.Combobox(app, values=['Highest Value', 'Lowest Value',
	                            'Biggest Gains', 'Biggest Losses',
	                            'Biggest % Gain', 'Biggest % Losses'])
sort.place(x=30, y=30)
sort.current(2)

#Based-on menu
baseLabel = tk.Label(app, text = "Based on: ")
baseLabel.place(x=10, y = 50)
base = ttk.Combobox(app, values=['Open', 'High', 'Low', 'Close', 'Volume'])
base.place(x=30, y = 70)
base.current(0)

#time menu
timeLabel = tk.Label(app, text = "Over period:")
timeLabel.place(x=10, y=90)
time = ttk.Combobox(app, values =["1 month", "3 months", "6 months",
	                          "1 year", "2 years", "5 years"])

time.place(x=30, y=110)
time.current(0)

#results display
resultLabel = tk.Label(app, text = "Results:")
resultLabel.place(x=10, y=180)
result = tk.Listbox(app, height = 11, width = 80)
result.place(x=10, y = 200)
result.insert(1, "     Date      |      Open     |      High     |      Low      |     Close     |    Volume    |  Name")


#error display
scrollbar = Scrollbar(app, orient=VERTICAL)
errorLabel = tk.Label(app, text = "Results:")
errorLabel.place(x=10, y=180)
error = tk.Listbox(app, height = 5, width = 70, yscrollcommand=scrollbar.set)
scrollbar.config(command=error.yview)
scrollbar.pack(side=RIGHT, fill=Y)
error.place(x=10, y = 500)

#run button
runBut = tk.Button(app, text = "RUN", fg="blue", 
		command=lambda: update_Display())

runBut.place(x=10, y=130)

#quit button
quitBut = tk.Button(app, text = "QUIT", fg="red", command = quit)
quitBut.place(x=80, y= 130)

#main process
app.mainloop()




