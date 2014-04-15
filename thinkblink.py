#!/usr/bin/python3

from os.path import expanduser
from collections import OrderedDict
from multiprocessing import Process, Lock
import sys
import argparse
import configparser
import time


parser = argparse.ArgumentParser(description='Configures and invokes blinking thinklight')
parser.add_argument('-g', '--generate', help='Generate default configuration', action='store_true')
parser.add_argument('-l', '--list',     help='Lists saved flags', action='store_true')
parser.add_argument('-v', '--verbose',  help='Be verbose', action='store_true')
flag_args = parser.add_mutually_exclusive_group()
flag_args.add_argument('-s', '--set',    metavar='<flag>', help='Set flag (start blinking) this is the default flag and can be omitted')
flag_args.add_argument('-u', '--unset',  metavar='<flag>', help='Unset flag (stop blinking)')
flag_args.add_argument('-t', '--toggle', metavar='<flag>', help='Toggle flag')
flag_args.add_argument('-a', '--add',    metavar='<flag>', help='Add flag in last position (most blinks)')
flag_args.add_argument('-f', '--first',  metavar='<flag>', help='Add flag in first position (one blink, all other flags get bumped up)')
flag_args.add_argument('-d', '--delete', metavar='<flag>', help='Delete flag (all flags below will blink one time fewer)')
parser.add_argument('<flag>', nargs='?', help='Sets flag, same as --set')
args = parser.parse_args()


def make_default_config(config_file):
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str # Makes the config case sensitive
    config.add_section('files')
    config.set('files', '# The "blink" file is the target, by default it is the brightness file for the keyboard light on thinkpads.')
    config.set('files', 'blink', '/sys/class/leds/tpacpi::thinklight/brightness')
    config.set('files', '# The "stat" file will keep track of what is expected in the "blink" file. Changing the file without using this script will cause the status not to match and trigger it to unset a raised flag. (On a thinkpad you can toggle the keyboard light though a Fn key combination.)')
    config.set('files', 'status', expanduser('~') + '/' + '.thinkblink.stat')
    config.add_section('values')
    config.set('values', '# These values will be written to "blink" file:')
    config.set('values', 'on', '255')
    config.set('values', 'off', '0')
    config.add_section('flags')
    config.set('flags', '# The first flag will toggle the light once, the second twice, and so on. Probably best arranged from most common to least common')
    config.set('flags', 'default', None)
    with open(config_file, 'w') as f: config.write(f)
    return


def read_config(config_file):
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)
        if not config.sections():
            raise IOError
    except IOError:
        print('Could not read configuration file:')
        print(config_file)
        print('Back it up and try the --generate option')
        sys.exit(1)
    # Add newlines to values
    for key in config['values'].keys(): config['values'][key] = config['values'][key] + '\n'
    return config


def set_flags(config):
    return [x for x in config['flags'].keys() if config['flags'][x]]


def toggle_flag(flag):
    if flag: return None
    else: return '1'


def toggle_light(files, values):
    for filename in files.values():
        content = read_file(filename)
        if content == values['on']:
            write_file(filename, values['off'])
        if content == values['off']:
            write_file(filename, values['on'])


def unexpected_diff(files):
    content = list(map(read_file, files.values()))
    return not all(x == content[0] for x in content)


def sync(files):
    write_file(files['status'], read_file(files['blink']))


def read_file(filename):
    with open(filename, 'r') as f: return f.read()


def write_file(filename, content):
    with open(filename, 'w') as f: f.write(content)


def main():
    config_file = expanduser('~') + '/' + '.thinkblink.conf'

    run_loop = False
    
    if args.generate:
        make_default_config(config_file)
        print('Generated default configuration')
        sys.exit()

    config = read_config(config_file)

    if len(set_flags(config)) > 0:
        if args.verbose: print('A blinker process should already be running')
        sys.exit()

    if args.__getattribute__('<flag>'):
        config['flags'][args.__getattribute__('<flag>')] = '1'
    if args.add:
        config['flags'][args.add] = None
    if args.first:
        config['flags'][args.first] = None
        temp = OrderedDict(config['flags'])
        temp.move_to_end(args.first, last=False)
        config['flags'] = temp
    if args.delete:
        config['flags'].pop(args.delete)
    if args.set:
        config['flags'][args.set] = '1'
    if args.unset:
        config['flags'][args.unset] = None
    if args.toggle:
        config['flags'][args.toggle] = toggle_flag(config['flags'][args.toggle])
    with open(config_file, 'w') as f: config.write(f)
    
    if args.list:
        for i, flag in enumerate(map(str, config['flags'].keys())):
            print(flag + '{end}'.format(end=' (' + str(i+1) + ')' if args.verbose else ''))

    if len(set_flags(config)):
        sync(config['files'])
    while len(set_flags(config)):
        start_over = False
        for flag in set_flags(config):
            l = list(config['flags'].keys()).index(flag) + 1
            for i in range(l):
                if unexpected_diff(config['files']):
                    sync(config['files'])
                    start_over = True
                    top_flag = set_flags(config)[-1]
                    config['flags'][top_flag] = toggle_flag(config['flags'][top_flag])
                    with open(config_file, 'w') as f: config.write(f)
                    break
                else:
                    toggle_light(config['files'], config['values'])
                    if i != l-1: time.sleep(0.25)
            if(start_over): break
            time.sleep(0.75)
        config = read_config(config_file)


if __name__ == "__main__":
    main()
