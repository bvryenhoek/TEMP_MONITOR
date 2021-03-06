import os
import sys
import string
import serial
import time
import pypyodbc

# ----------------------------------------------------------------------------
# TODO:
# 1) ODBC module to link to SQL or MDB table for data storage
# 2) Error handling and reporting. Will be run as service unattended.
# ----------------------------------------------------------------------------

CPAD_LOG_FILE_DIR = "C:\\CPAD_LOG\\"
CPAD_LOG_FILE_NAME = "CPAD_LOG.TXT"

CPAD_ERROR_LOG_FILE_DIR = CPAD_LOG_FILE_DIR
CPAD_ERROR_LOG_FILE_NAME = "CPAD_ERROR_LOG.TXT"

CPAD_ERROR_COUNT = 0

# T1 = low temperature (freezer) sensor
# T2 = room temperature sensor
# T3 = Nucleus temperature sensor
CPAD_SENSOR_T1 = "T1"
CPAD_SENSOR_T2 = "T2"
CPAD_SENSOR_T3 = "T3"

# COM Port settings (USB > Serial FTDI driver)
PORT_NUM = 3
PORT_BAUD = 2400

# Opcode for heartbeat beacon - ignore
PKT_OPC_BEACON = 5

# Opcode for temperature data - process
PKT_OPC_XTENDED = 31

# Read buffer array
ReadArr = [0x00] * 256


def init_com_port():
	try:
		ser = serial.Serial(PORT_NUM - 1, baudrate=PORT_BAUD)
		return ser

	except serial.serialutil.SerialException:
		return 0


# Function gets next byte from cPad port and returns it
def read_next_num():
	global CPAD_ERROR_COUNT

	try:
		ch = list(ser.read(1))[0]
		return ch

	except serial.serialutil.SerialException:

		if ser:
			print("serial port exists")

		if CPAD_ERROR_COUNT == 0:
			write_data_to_errorlog(CPAD_ERROR_LOG_FILE_DIR, CPAD_ERROR_LOG_FILE_NAME, str("COM Port read failed"))
			CPAD_ERROR_COUNT = 1

	except:

		write_data_to_errorlog(CPAD_ERROR_LOG_FILE_DIR, CPAD_ERROR_LOG_FILE_NAME, str("General error"))


def write_cpad_data_to_log(targetpath, targetfile, parseddata):
	try:

		# NOTE:Sensor Name: ParsedData[0]
		# Temp: ParsedData[1]

		# Write temperature + time and date to log file
		with open(targetpath + targetfile, 'a') as DataFile:

			# Only write sensor values as comma-delimited. System messages will be processed differently.
			if parseddata[0] in (CPAD_SENSOR_T1, CPAD_SENSOR_T2, CPAD_SENSOR_T3):

				# TargetFile.write("Sensor,")
				DataFile.write(parseddata[0] + ',')

				# TargetFile.write("Date,")
				DataFile.write(time.strftime("%x") + ',')

				# TargetFile.write("Time,")
				DataFile.write(time.strftime("%X") + ',')

				# TargetFile.write("Temp,")
				DataFile.write(ParsedData[1] + '\n')

			else:
				write_data_to_errorlog(CPAD_ERROR_LOG_FILE_DIR, CPAD_ERROR_LOG_FILE_NAME,
									str(parseddata[0] + parseddata[0] + '\n'))

	except IOError:
		pass

def write_data_to_errorlog(targetpath, targetfile, errormessage):
	try:
		with open(targetpath + targetfile, 'a') as DataFile:
			DataFile.write(time.strftime("%X") + ":" + time.strftime("%x") + ":" + errormessage + '\n')

	except IOError:

		pass

ser = init_com_port()

if ser != 0:

	ReadIndex = 0

	# Loop continuously while data is read and logged
	while 1:

		ReadIndex += 1

		# Throw away first six bytes in message (not required)
		if ReadIndex > 6:

			# Reset counter for throwaway bytes
			ReadIndex = 0

			# Get Opcode value, 1st after throwaway bytes
			Opcode = read_next_num()

			# ASCII message incoming
			if Opcode == PKT_OPC_XTENDED:

				# Byte after Opcode is byte count for ASCII message.
				DataSize = read_next_num() + 1

				# Prepare to read ASCII bytes
				DataIndex = 0

				# Temp storage for ASCII message
				DataString = ""

				# Read the message
				while DataIndex < DataSize - 1:
					NextByte = read_next_num()
					DataString += chr(NextByte)

					DataIndex += 1

				# Split into string array to separate sensor name and temperature value strings
				ParsedData = DataString.split()

				write_cpad_data_to_log(CPAD_LOG_FILE_DIR, CPAD_LOG_FILE_NAME, ParsedData)

else:
	write_data_to_errorlog(CPAD_ERROR_LOG_FILE_DIR, CPAD_ERROR_LOG_FILE_NAME, str("COM Port failed to initialize"))
