import glob, serial, time, signal, sys, json, click
from datetime import datetime
import random
import requests
from socketIO_client import SocketIO, LoggingNamespace
from config import *
from termcolor import colored
import asyncio
import _thread as thread


class SerialMonitor:
    socketCon = None
    serialCon = None
    server_settings = None

    #---------------------------------------------------------------------------
    # Helper functions to colour text output to command line
    #---------------------------------------------------------------------------

    def concat_args(self, *arg):
        s = ""
        for a in arg:
            s = s + " " + str(a)
        return s

    def titlemsg(self, *arg):
        print(colored(self.concat_args(*arg), 'yellow'))

    def errmsg(self, *arg):
        print(colored(self.concat_args(*arg), 'red'))

    def infomsg(self, *arg):
        print(colored(self.concat_args(*arg), 'blue'))

    def optionmsg(self, *arg):
        print(colored(self.concat_args(*arg), 'blue'))

    def jsonmsg(self, *arg):
        print(colored(self.concat_args(*arg), 'cyan'))

    def receive_message(self, *args):
        jsonstr = json.dumps(args[0]['data'])
        self.serialCon.write(str.encode(jsonstr))
        print('receive_message')

    #---------------------------------------------------------------------------
    # Socket listener and Emitter
    #---------------------------------------------------------------------------

    @asyncio.coroutine
    def websocket_listener(self):
        def run(*args):
            self.socketCon.on('feedback', self.receive_message)
            self.socketCon.wait()
        thread.start_new_thread(run, ())


    # Program loop which reads the serial port and pushes valid Json to Web socket
    @asyncio.coroutine
    def websocket_emitter(self):
        # Read Serial loop
        while True:
            yield None
            # Read form serial port
            if self.socketCon is not None:
                if self.serialCon is not None:
                    jsonStr = self.read_serial()
                else:
                    self.errmsg("Serial not open yet")
                    time.sleep(5)
                    continue
                # Send data to web socket
                if jsonStr is not None:
                    self.jsonmsg(jsonStr)
                    self.socketCon.emit('from_serial_monitor', jsonStr)

            # Read from test data generator
            else:
                self.errmsg("Web socket not open yet")
            # Sleep for sample interval
            time.sleep(SAMPLE_INTERVAL / 1000)

    # Read in a line, check that is decodes as JSON and then forward to web socket
    def read_serial(self):
        try:
            serialLine = self.serialCon.readline().decode()
        except UnicodeDecodeError:
            self.errmsg("invalid Serial string")
            return None
        except serial.serialutil.SerialException as e:
            self.errmsg("Serial connection failed, pausing for 5 seconds then will try again")
            self.config_serial(False)
            time.sleep(5)
            return None
        try:
            return json.loads(serialLine)
        except ValueError:
            self.errmsg("invalid Json string")
            return None


    #---------------------------------------------------------------------------
    # Detect when script terminated and close socket
    #---------------------------------------------------------------------------

    def signal_handler(self, given_signal):
        if self.serialCon is not None:
            try:
                self.serialCon.close()
            except serial.serialutil.SerialException:
                pass

        self.infomsg('Closing connections...')
        if self.socketCon is not None:
            self.socketCon.disconnect()

        self.infomsg('Exited')
        sys.exit(0)

    #---------------------------------------------------------------------------
    # List all available serial ports
    #---------------------------------------------------------------------------

    def list_serial_ports(self):
        # Find ports
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')
        # Test all discovered ports and only return those where a connection could be established
        result = []
        for port in ports:
            if self.test_port(port):
                result.append(port)
        return result

    # Test if a connection to a port can be established
    def test_port(self, port):
        try:
            s = serial.Serial(port)
            s.close()
            return True
        except (OSError):
            return False

    # Manual input for port
    def manual_port_picker(self, ports):
        # Print option
        port_number = 1
        for port in ports:
            self.optionmsg(port_number, port)
            port_number+=1
        self.optionmsg('R', "Refresh")
        self.optionmsg('E', "Exit")

        # Wait for answer
        while True:
            try:
                answer = input('Please select a port: ')
                if answer.lower() == 'e':
                    sys.exit(0)
                if answer.lower() == 'r':
                    ports = self.list_serial_ports()
                    return self.manual_port_picker(ports)

                return ports[int(answer)-1]
            except (IndexError, UnicodeDecodeError, ValueError):
                self.errmsg('Invalid choice please try again.')

    # Automatic port picker
    def auto_port_picket(self, ports):
        port_number = 1
        for port in ports:
            port_number += 1
            if 'usbmodem' in port or 'wchusbserial1420' in port:
                self.infomsg("Auto selected: ", port)
                return port

    #---------------------------------------------------------------------------
    # Test for web server
    #---------------------------------------------------------------------------

    def test_for_webserver(self):
        url = self.server_settings['protocol'] + "://" + self.server_settings['host']+":"+str(self.server_settings['port'])
        self.infomsg('Testing connection to: ', url)
        try:
            r = requests.get(url)
        except requests.exceptions.ConnectionError:
            return False

        if r.status_code == 200:
            return True
        else:
            return False

    #---------------------------------------------------------------------------
    # Configure web socket
    #---------------------------------------------------------------------------

    def config_websocket(self):
        # Test web server exists
        server_exists = self.test_for_webserver()
        if not server_exists:
            self.errmsg("Failed to connect to web server, is it running?")
            sys.exit(0)
        # Connect to web socket
        self.infomsg('Connecting to socket')
        self.socketCon = SocketIO('localhost', self.server_settings['port'])
        while not self.socketCon.connected:
            self.infomsg("Waiting for connection")
            time.sleep(CONNECTION_WAIT)


    #---------------------------------------------------------------------------
    # Configure Serial connection
    #---------------------------------------------------------------------------

    def config_serial(self, autooff):
        # List ports
        ports = self.list_serial_ports()
        port = None

        # Auto pick a port
        if not autooff:
            port = self.auto_port_picket(ports)

        # If no port auto picked or auto pick off then manual pick
        if port is None:
            port = self.manual_port_picker(ports)

        # Serial
        self.infomsg('Connecting to serial port')
        self.serialCon = serial.Serial(port, SERIAL_RATE, timeout=CONNECTION_TIMEOUT)
        while not self.serialCon.isOpen():
            self.infomsg("waiting for connection")
            time.sleep(CONNECTION_WAIT)


    #---------------------------------------------------------------------------
    # Main function called when script executed
    #---------------------------------------------------------------------------

    def __init__(self, autooff, test, servermode):

        self.titlemsg(">>>> Serial Port Monitor <<<<")
        self.server_settings = WEB_SERVER

        # Config websocket and serial
        self.config_websocket()
        self.config_serial(autooff)

        # Start
        self.infomsg('Starting...')

        # Run the listener and emitter asyncronously
        t1 = asyncio.async(self.websocket_listener())
        t2 = asyncio.async(self.websocket_emitter())
        loop = asyncio.get_event_loop()
        loop.run_forever()


# -----------------------------------------------------------------------------

@click.command()
@click.option('--autooff', is_flag=True, default=False, help='Turn off auto port selection')
@click.option('--test', default=0, help='Generate Test Data')
@click.option('--prod', is_flag=True, default=False, help='Switch to production mode')
def main(autooff, test, prod):
    if not prod:
        servermode = 'local'
    else:
        servermode = 'prod'
    sm = SerialMonitor(autooff, test, servermode)
    signal.signal(signal.SIGINT, sm.signal_handler)

if __name__ == '__main__':
    main()

# -----------------------------------------------------------------------------
