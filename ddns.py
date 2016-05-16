import logging
import os
import requests
import time

# Constants (provided by Google Domains)
uid = ""
pwd = ""
host = ""

# Logging 
BASE = os.getcwd()
hist = os.path.join(BASE, "last.ip")
logf = os.path.join(BASE, "gddns.log")

# Setup logger
logging.basicConfig(filename=logf, level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S%p :')
logging.getLogger("requests").setLevel(logging.WARNING)

# Return our last IP from history file. If there is no history file,
# return 0.0.0.0
def getlastip():
    try:
        with open(hist, "r") as old:
            lastip = old.read()
        logging.debug("Last IP Read from history file: " + lastip)
        return lastip
    except:
        lastip = "0.0.0.0"
        with open(hist, "w") as old:
            old.write(lastip)
        logging.info("No history file found -- inserting '0.0.0.0'")
        return lastip

def checkipupdate(ip):    
    # Get Public IP (retry if failed)
    status = "0"
    while status != "200":
        headers = {"User-Agent": "DDNS Updater"}
        getip = requests.get("http://api.ipify.org", headers=headers)
        if getip.status_code == 200:
            logging.debug("api.ipify.org returned status code: 200")
            status = "200"  
            newip = getip.text
            if newip == ip:
                # If our IP's are the same, don't beacon out to Google.
                return "wait"
            else:
                # We want to save the new IP to the history file
                with open(hist, "w") as new:
                    new.write(newip)
        
            headers = {"User-Agent": "Google DDNS Updater"}
            ddns = requests.get("https://domains.google.com/nic/update?hostname="
                                + host + "&myip=" + newip,
                                headers=headers, auth=(uid,pwd))
            if ddns.status_code == 200:
                data = ddns.text
                cmd = data.split()
                if cmd[0] == "good":
                    logging.info("IP Updated: " + str(cmd[1]))
                if cmd[0] == "nochg":
                    logging.warn("Google reported the same IP as previously "
                                 "reported. Are we incorrectly resending?")
                if cmd[0] == "nohost":
                    logging.error("The hostname does not exist or does not have "
                                  "DDNS enabled.")
                if cmd[0] == "badauth":
                    logging.error("The username/password combination is invalid.")
                if cmd[0] == "notfqdn":
                    logging.error("The supplied hostname is not a valid FQDN.")
                if cmd[0] == "badagent":
                    logging.error("The DDNS client is making bad requests. Ensure "
                                  "the user agent is set in the request and that "
                                  " you're only attempt to set and IPv4 address.")
                if cmd[0] == "abuse":
                    logging.error("DDNS access for the hostname has been blocked "
                                  "due to failure to interpret previous responses "
                                  "correctly.")
                if cmd[0] == "911":
                    logging.error("An internal error has occured on Google's "
                                  "servers.")
                return cmd[0]
            else:
                logging.error("domains.google.com returned status code: " +
                              str(ddns.status_code))
                return "retry"
            
        else:
            logging.error("api.ipify.org returned status code: " +
                          str(getip.status_code))
            time.sleep(5)

logging.info("Starting Google DDNS Client")
# Check every minute for a new IP and exit if we run into any issues.
while True:
    check = getlastip()
    run = checkipupdate(check)
    if run == "wait" or run == "retry" or run == "good":
        time.sleep(60)
    else:
        exit()
