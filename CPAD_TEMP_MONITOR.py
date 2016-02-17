import os
import sys
import string
import serial
import time

#TODO: 1) ODBC module to link to SQL or MDB table for data storage
#      2) Error handling and reporting. Will be run as service unattended.


CPAD_LOG_FILE_DIR="C:\\CPAD_LOG\\"
CPAD_LOG_FILE_NAME="CPAD_LOG.TXT"

CPAD_ERROR_LOG_FILE_DIR=CPAD_LOG_FILE_DIR
CPAD_ERROR_LOG_FILE_NAME="CPAD_ERROR_LOG.TXT"

CPAD_ERROR_COUNT=0

#T1 = low temperature (freezer) sensor
#T2 = room temperature sensor
#T3 = Nucleus temperature sensor
CPAD_SENSOR_T1 = "T1"
CPAD_SENSOR_T2 = "T2"
CPAD_SENSOR_T3 = "T3"

# COM Port settings (USB > Serial FTDI driver)
PORT_NUM=3
PORT_BAUD=2400

# Opcode for heartbeat beacon - ignore
PKT_OPC_BEACON=5

# Opcode for temperature data - process
PKT_OPC_XTENDED=31

# Read buffer array
ReadArr=[0x00]*256

def InitCOMPort():

        try:
                ser = serial.Serial(PORT_NUM-1, baudrate=PORT_BAUD)
                return ser

        except serial.serialutil.SerialException:
                return 0


# Function gets next byte from cPad port and returns it
def ReadNextNum():

        global CPAD_ERROR_COUNT

        try:
                ch = list(ser.read(1))[0]
                return ch

        except serial.serialutil.SerialException:

                if ser:
                        print("serial port exists")

                if CPAD_ERROR_COUNT == 0:

                        WriteDataToErrorLog(CPAD_ERROR_LOG_FILE_DIR,CPAD_ERROR_LOG_FILE_NAME,str("COM Port read failed"))
                        CPAD_ERROR_COUNT = 1

        except:

                WriteDataToErrorLog(CPAD_ERROR_LOG_FILE_DIR,CPAD_ERROR_LOG_FILE_NAME,str("General error"))


def WriteCPadDataToLog(TargetPath,TargetFile,ParsedData):

        try:

                #NOTE:  Sensor Name: ParsedData[0]
                #       Temp: ParsedData[1]

                #Write temperature + time and date to log file
                with open(TargetPath+TargetFile,'a') as DataFile:


                        # Only write sensor values as comma-delimited. System messages will be processed differently.
                        if ParsedData[0] in (CPAD_SENSOR_T1,CPAD_SENSOR_T2,CPAD_SENSOR_T3):

                                #TargetFile.write("Sensor,")
                                DataFile.write(ParsedData[0] + ',')

                                #TargetFile.write("Date,")
                                DataFile.write(time.strftime("%x") + ',')

                                #TargetFile.write("Time,")
                                DataFile.write(time.strftime("%X") + ',')

                                #TargetFile.write("Temp,")
                                DataFile.write(ParsedData[1] + '\n')

                        else:
                                WriteDataToErrorLog(CPAD_ERROR_LOG_FILE_DIR,CPAD_ERROR_LOG_FILE_NAME,str(ParsedData[0] + ParsedData[0] + '\n'))

        except IOError:
                pass


def WriteDataToErrorLog(TargetPath,TargetFile,ErrorMessage):

        try:
                with open(TargetPath+TargetFile,'a') as DataFile:
                         DataFile.write(time.strftime("%X") + ":" + time.strftime("%x") + ":" + ErrorMessage + '\n')

        except IOError:

                pass

ser=InitCOMPort()

if (ser != 0):

        ReadIndex = 0

        #Loop continuosly while data is read and logged
        while 1:

                ReadIndex += 1

                #Throw away first six bytes in message (not required)
                if ReadIndex >6:

                        #Reset counter for throwaway bytes
                        ReadIndex = 0

                        #Get Opcode value, 1st after throwaway bytes
                        Opcode  = ReadNextNum()

                        #ASCII message incoming
                        if Opcode == PKT_OPC_XTENDED:

                                #Byte after Opcode is byte count for ASCII message.
                                DataSize=ReadNextNum()+1

                                #Prepare to read ASCII bytes
                                DataIndex=0

                                #Temp storage for ASCII message
                                DataString=""

                                #Read the message
                                while DataIndex < DataSize-1:

                                        NextByte=ReadNextNum()
                                        DataString=DataString + chr(NextByte)

                                        DataIndex+= 1

                                #Split into string array to separate sensor name and temperature value strings
                                ParsedData = DataString.split()

                                WriteCPadDataToLog(CPAD_LOG_FILE_DIR,CPAD_LOG_FILE_NAME,ParsedData)

else:
       WriteDataToErrorLog(CPAD_ERROR_LOG_FILE_DIR,CPAD_ERROR_LOG_FILE_NAME,str("COM Port failed to initialize"))

