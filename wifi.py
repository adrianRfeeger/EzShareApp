import subprocess
import logging

logger = logging.getLogger(__name__)

def connect_to_wifi(ezShare):
    get_interface_cmd = 'networksetup -listallhardwareports'
    try:
        get_interface_result = subprocess.run(get_interface_cmd,
                                              shell=True,
                                              capture_output=True,
                                              text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'Error getting Wi-Fi interface name. Return code: {e.returncode}, error: {e.stderr}') from e

    interface_lines = get_interface_result.stdout.split('\n')
    for index, line in enumerate(interface_lines):
        if 'Wi-Fi' in line:
            ezShare.interface_name = interface_lines[index + 1].split(':')[1].strip()
            break
    if not ezShare.interface_name:
        raise RuntimeError('No Wi-Fi interface found')

    connect_cmd = f'networksetup -setairportnetwork {ezShare.interface_name} "{ezShare.ssid}" "{ezShare.psk}"'
    try:
        connect_result = subprocess.run(connect_cmd, shell=True,
                                        capture_output=True,
                                        text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'Error connecting to {ezShare.ssid}. Return code: {e.returncode}, error: {e.stderr}') from e
    if 'Failed' in connect_result.stdout:
        raise RuntimeError(f'Error connecting to {ezShare.ssid}. Error: {connect_result.stdout}')
    ezShare.connection_id = ezShare.ssid
    ezShare.connected = True

def wifi_connected(ezShare):
    return ezShare.connected

def disconnect_from_wifi(ezShare):
    if ezShare.connection_id:
        ezShare.print(f'Disconnecting from {ezShare.connection_id}...')

        ezShare.print(f'Removing profile for {ezShare.connection_id}...')
        profile_cmd = f'networksetup -removepreferredwirelessnetwork {ezShare.interface_name} "{ezShare.connection_id}"'
        try:
            subprocess.run(profile_cmd, shell=True,
                           capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'Error removing network profile for {ezShare.ssid}. Return code: {e.returncode}, error: {e.stderr}') from e
        try:
            subprocess.run(f'networksetup -setairportpower {ezShare.interface_name} off',
                           shell=True, check=True)
            logger.info('Wi-Fi interface %s turned off', ezShare.interface_name)
            subprocess.run(f'networksetup -setairportpower {ezShare.interface_name} on',
                           shell=True, check=True)
            logger.info('Wi-Fi interface %s turned on', ezShare.interface_name)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'Error toggling Wi-Fi interface power. Return code: {e.returncode}, error: {e.stderr}') from e
        finally:
            ezShare.connected = False
            ezShare.connection_id = None
