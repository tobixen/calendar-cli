import logging
import json
import yaml
from fnmatch import fnmatch

def interactive_config(args, config, remaining_argv):
    import readline

    new_config = False
    section = 'default'
    backup = {}
    modified = False

    print("Welcome to the interactive calendar configuration mode")
    print("Warning - untested code ahead, raise issues at t-calendar-cli@tobixen.no or the github issue tracker")
    print("It might be a good idea to read the documentation in parallel if running this for your first time")
    if not config or not hasattr(config, 'keys'):
        config = {}
        print("No valid existing configuration found")
        new_config = True
    if config:
        print("The following sections have been found: ")
        print("\n".join(config.keys()))
        if args.config_section and args.config_section != 'default':
            section = args.config_section
        else:
            ## TODO: tab completion
            section = raw_input("Chose one of those, or a new name / no name for a new configuration section: ")
        if section in config:
            backup = config[section].copy()
        print("Using section " + section)
    else:
        section = 'default'

    if not section in config:
        config[section] = {}

    for config_key in ('caldav_url', 'calendar_url', 'caldav_user', 'caldav_pass', 'caldav_proxy', 'ssl_verify_cert', 'language', 'timezone', 'inherits'):

        if config_key == 'caldav_pass':
            print("Config option caldav_pass - old value: **HIDDEN**")
            value = getpass(prompt="Enter new value (or just enter to keep the old): ")
        else:
            print("Config option %s - old value: %s" % (config_key, config[section].get(config_key, '(None)')))
            value = raw_input("Enter new value (or just enter to keep the old): ")

        if value:
            config[section][config_key] = value
            modified = True

    if not modified:
        print("No configuration changes have been done")
    else:
        state = 'start'
        while state == 'start':
            options = []
            if section:
                options.append(('save', 'save configuration into section %s' % section))
            if backup or not section:
                options.append(('save_other', 'add this new configuration into a new section in the configuration file'))
            if remaining_argv:
                options.append(('use', 'use this configuration without saving'))
            options.append(('abort', 'abort without saving'))
            print("CONFIGURATION DONE ...")
            for o in options:
                print("Type %s if you want to %s" % o)
            cmd = raw_input("Enter a command: ")
            if cmd in ('use', 'abort'):
                state = 'done'
            if cmd in ('save', 'save_other'):
                if cmd == 'save_other':
                    new_section = raw_input("New config section name: ")
                    config[new_section] = config[section]
                    if backup:
                        config[section] = backup
                    else:
                        del config[section]
                    section = new_section
                try:
                    if os.path.isfile(args.config_file):
                        os.rename(args.config_file, "%s.%s.bak" % (args.config_file, int(time.time())))
                    with open(args.config_file, 'w') as outfile:
                        json.dump(config, outfile, indent=4)
                except Exception as e:
                    print(e)
                else:
                    print("Saved config")
                    state = 'done'

    if args.config_section == 'default' and section != 'default':
        config['default'] = config[section]
    return config

## TODO TODO TODO - write test code for all the corner cases
## TODO TODO TODO - write documentation of config format
def expand_config_section(config, section='default', blacklist=None):
    """
    In the "normal" case, will return [ section ]
    
    We allow:
    
    * * includes all sections in config file
    * "Meta"-sections in the config file with the keyword "contains" followed by a list of section names
    * Recursive "meta"-sections
    * Glob patterns (work_* for all sections starting with work_)
    * Glob patterns in "meta"-sections
    """
    ## Optimizating for a special case.  The results should be the same without this optimization.
    if section == '*':
        return [x for x in config if not config[x].get('disable', False)]

    ## If it's not a glob-pattern ...
    if set(section).isdisjoint(set('[*?')):
        ## If it's referring to a "meta section" with the "contains" keyword
        if 'contains' in config[section]:
            results = set()
            if not blacklist:
                blacklist = set()
            blacklist.add(section)
            for subsection in config[section]['contains']:
                if not subsection in results and not subsection in blacklist:
                    for recursivesubsection in expand_config_section(config, subsection, blacklist):
                        results.add(recursivesubsection)
            return results
        else:
            ## Disabled sections should be ignored
            if config.get('section', {}).get('disable', False):
                return []
            
            ## NORMAL CASE - return [ section ]
            return [ section ]
    ## section name is a glob pattern
    matching_sections = [x for x in config if fnmatch(x, section)]
    results = set()
    for s in matching_sections:
        if set(s).isdisjoint(set('[*?')):
            results.update(expand_config_section(config, s))
        else:
            ## Section names shouldn't contain []?* ... but in case they do ... don't recurse
            results.add(s)
    return results

def config_section(config, section='default'):
    if section in config and 'inherits' in config[section]:
        ret = config_section(config, config[section]['inherits'])
    else:
        ret = {}
    if section in config:
        ret.update(config[section])
    return ret

def read_config(fn, interactive_error=False):
    ## This can probably be refactored into fewer lines ...
    try:
        try:
            with open(fn, 'rb') as config_file:
                return json.load(config_file)
        except json.decoder.JSONDecodeError:
            try:
                with open(fn, 'rb') as config_file:
                    return yaml.load(config_file, yaml.Loader)
            except yaml.scanner.ScannerError:
                logging.error("config file exists but is neither valid json nor yaml.  Check the syntax.")

    except FileNotFoundError:
        ## File not found
        logging.info("no config file found")
    except ValueError:
        if interactive_error:
            logging.error("error in config file.  Be aware that the interactive configuration will ignore and overwrite the current broken config file", exc_info=True)
        else:
            logging.error("error in config file.  It will be ignored", exc_info=True)
    return {}
