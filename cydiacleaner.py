#!/usr/bin/python
"""
Script used to validate package-installed apt repo files on Jailbroken
iPhones. Only requires Python to run. Tested and verified on both iOS 
3.x and 4.x.
"""
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
import shutil
import socket
import sys
import urllib2

# Set to True for debugging/development
# Not in main since we want this global across all 
# functions without passing it to each one.
debug = False

def isValidURL(url='', userAgent='isValidURL'):
    """
    Function to check if a given HTTP/FTP URL is valid.
    Returns True/False.
    """
    if url == '':
        return False
    
    req = urllib2.Request(url=url, headers={'User-Agent': userAgent})
    try:
        urllib2.urlopen(req)
    except:
        return False

    return True

def isValidHostname(host=''):
    """
    Function to validate if a given hostname is valid. Used 
    to find bad hostnames that timeout. Returns True/False
    """
    if host == '':
        return False
    
    try:
        socket.gethostbyname(host)
    except:
        return False

    return True

def serviceOnline(url=''):
    """
    Function to validate if a service is actually online and 
    accepting connections. Only accepts FTP and HTTP connections.
    """
    if url == '':
        return False

    # Pull service and hostname out
    try:
        service = url.split(':')[0]
        hostname = url.split('/')[2]
    except:
        return False

    # Find our service port
    if service == 'ftp':
        port = 21
    elif service == 'http':
        port = 80
    else:
        return False

    # Try to connect to the service
    connInfo = ( hostname, port )
    ourSocket = socket.socket()

    try:
        ourSocket.connect(connInfo)
    except:
        ourSocket.close()
        return False
    
    ourSocket.close()
    return True

def echo(message=''):
    """
    Function to emulate echo -en type functionality since
    print acts weird at times and py3k changes print as well.
    """
    if message == '':
        return False

    sys.stdout.write(message)
    sys.stdout.flush()
    return True

def findRepoFiles(folder='', exclusions=None):
    """
    Function to search a folder for repo files. If given any exclusions, 
    will remove them from the list (exclusion should be a list).
    """
    if folder == '':
        return None

    # Find our files.
    if os.path.isdir(folder):
        results = os.listdir(folder)
    # Make sure our folder is actually there.
    else:
        sys.stderr.write("Our repo folder %s is missing.\n" % (folder,))
        sys.exit(1)

    # Remove any exclusions
    if exclusions:
        for exclusion in exclusions:
            if exclusion in results:
                results.remove(exclusion)

    # We only want *.list
    for result in results:
        ourExt = os.path.splitext(result)[-1]
        if ourExt != '.list':
            results.remove(result)

    return results

def findRepos(folder='', files=[]):
    """
    Function to pull the apt repos out of a list of files from a given folder.
    """
    results = []
    if folder == '':
        return None

    for ourFile in files:
        # Open the file and save it to a list
        data = open(folder + ourFile, 'r')
        result = data.readlines()
        data.close()
        # Split our string by spaces
        for line in result:
            ourValues = line.split()
            # Make sure we don't have a blank line
            if len(ourValues) > 0:
                # Validate the line and get our info
                if ourValues[0] == 'deb':
                    results.append([ ourFile, ourValues[1], ourValues[2] ])
    return results

def checkRepos(ourList=[], returnBad=False, returnGood=False,
               userAgent='checkRepos'):
    """
    Function to verify if a list of repos are valid.
    Expects a lists of lists, with each child list having:
    [ Filename, Repo, Dist ]
    Will return either good or bad repos, based on what is 
    passed (returnBad=True or returnGood=True)
    """
    if ourList == [] or returnBad is False and returnGood is False:
        return None
            
    mirrorFiles = ( 'Release.gpg', 'en.bz2', 'Release', 'Packages.bz2',
            'Packages.gz', 'Packages' )
    result = []
    
    # Done for formatting.
    if debug: echo("\n")

    for item in ourList:
        # Aliases are good.
        #filename = item[0] - We don't actually use this. Just for reference.
        repo = item[1]
        dist = item[2]
        hostname = repo.split('/')[2]
        # All repos are false until proven otherwise
        validRepo = False

        # Make sure it resolves. Saves time instead of urllib2 doing this.
        if debug:
            echo("\nChecking if %s resolves to an IP..." % (hostname,))
        if isValidHostname(hostname):
            if debug:
                echo("\tyes\nChecking if %s is online..." % (repo,))
            if serviceOnline(repo):
                if debug:
                    echo("\tyes\n")

                # Check the base repo for our files
                for ourFile in mirrorFiles:
                    link = repo + ourFile
                    if debug:
                        echo("Checking if %s is there..." % (link,))
                    if isValidURL(link, userAgent):
                        if debug:
                            echo("\tyes\n")
                        validRepo = True
                        if returnGood:
                            result.append(item)
                        break
                    else:
                        if debug:
                            echo("\tno\n")

                # Now check the dist folder
                if not validRepo:
                    for ourFile in mirrorFiles:
                        # If ./ is given for dist, it's not used.
                        if dist == "./":
                            break
                        link = "%sdists/%s/%s" % (repo, dist, ourFile)
                        if debug:
                            echo("Checking if %s is there..." % (link,))
                        if isValidURL(link, userAgent):
                            if debug:
                                echo("\tyes\n")
                            validRepo = True
                            if returnGood:
                                result.append(item)
                            break
                        else:
                            if debug:
                                echo("\tno\n")

                # Last chance, done for iphonehe since their repo is weird.
                # This checks the root of the hostname for the files.
                if not validRepo:
                    for ourFile in mirrorFiles:
                        link = "http://%s/%s" % (hostname, ourFile)
                        if debug:
                            echo("Checking if %s is there..." % (link,))
                        if isValidURL(link, userAgent):
                            if debug:
                                echo("\tyes\n")
                            validRepo = True
                            if returnGood:
                                result.append(item)
                            break
                        else:
                            if debug:
                                echo("\tno\n")

                # If STILL not valid, all aboard the failboat.
                if not validRepo:
                    if debug:
                        echo("This repo has failed all file checks.\n")
                    if returnBad:
                        item.append("Not a valid repository.")
                        result.append(item)
            else:
                if debug:
                    echo("\tno\n")
                if returnBad:
                    item.append("Service not online.")
                    result.append(item)
        else:
            if debug:
                echo("\tno\n")
            if returnBad:
                item.append('Hostname does not resolve.')
                result.append(item)
    return result


############
### MAIN ###
############

def main():
    """
    The main function for Cydia Cleaner.
    """
    # Variables we need
    done = "All finished! This iPhone is now squeaky clean! =)\n"
    exclusion = [ 'cydia.list' ]
    ourSocketTimeout = 3
    repoFolder = "/etc/apt/sources.list.d/"
    retiredFolder = repoFolder + "retired/"
    rev = "1.32"
    script = os.path.basename(sys.argv[0])
    userAgent = script + " " + rev
    
    # Used for development
    if debug:
        repoFolder = "repos/"
        retiredFolder = repoFolder + "retired/"
   
    # Must be root to run this script.
    if os.getuid() != 0:
        sys.stderr.write("This program must be run as root.\n")
        sys.exit(1)

    # Ensure our repo folder exists
    if not os.path.isdir(repoFolder):
        sys.stderr.write("Our repo folder %s is missing.\n" % (repoFolder,))
        sys.exit(1)

    # Ensure we have network connectivity
    if not serviceOnline('http://www.google.com/'):
        sys.stderr.write("We have no network connectivity! Exiting.")
        sys.exit(1)

    # If this is our first time, create our retired folder
    if not os.path.isdir(retiredFolder):
        echo("No retired folder present, creating...")
        os.mkdir(retiredFolder)
        echo("done.\n")

    # Time to build our list of repos with the info we need
    repoFiles = findRepoFiles(repoFolder, exclusion)
    repoList = findRepos(repoFolder, repoFiles)
    repoNumber = len(repoList)
    
    # Make sure we found at least 1 repo
    if repoNumber < 1:
        sys.stderr.write("Unable to find our repos! Something is wrong.\n")
        sys.exit(1)

    # Set our socket timeout
    socket.setdefaulttimeout(ourSocketTimeout)

    # Now that we have our repo list. Time to start testing things!
    echo("Beginning scan of all %d repositories, "
    "get some coffee..." % (repoNumber,))
    # Find our failed repos
    failedRepos = checkRepos(repoList, returnBad=True, userAgent=userAgent)
    # Done scanning repos
    echo("done!\n")
    # Check how many bad repos we found.
    failedNumber = len(failedRepos)
    # If we found nothing, all is well
    if failedNumber == 0:
        echo("No repos failed! All is well.\n\n")
        failedFiles = None
        
    else:
        # If we're still here, we have broken repos.
        # Not needed for function, but dang it I love grammar.
        failedFiles = []
        if failedNumber == 1:
            echo("\nWe have found 1 bad repo.\n")
            echo("Here is the offending repo:\n")
        else:
            echo("\nWe have found %d bad repos.\n" % (failedNumber,))
            echo("Here are the following offending repos:\n")
    
        for item in failedRepos:
            # Aliases are good.
            filename = item[0]
            repo = item[1]
            hostname = repo.split('/')[2]
            error = item[-1]
            echo("\nHostname:\t" + hostname)
            echo("\nFull Repo:\t" + repo)
            echo("\nFilename:\t" + filename)
            echo("\nRepo Error:\t" + error + "\n")
    
        # Retire our bad repos
        echo("\n")
        # Make note of what's failed
        for item in failedRepos:
            filename = item[0]
            failedFiles.append(filename)
            liveFile = repoFolder + filename
            retiredFile = retiredFolder + filename
            echo("Retiring %s..." % (filename,))
            shutil.move(liveFile, retiredFile)
            echo("done.\n")
        echo("All invalid repositories have been retired.\n")

    # Now, let's scan our retired folder.
    echo("Now finding previous retired repos...")
    retiredFiles = findRepoFiles(retiredFolder, failedFiles)
    retiredList = findRepos(retiredFolder, retiredFiles)
    retiredNum = len(retiredList)
    echo("done.\n")
    # If we found nothing new, then nothing to scan over.
    if retiredNum < 1:
        echo("No new retired repo files to validate.\n\n" + done)
        sys.exit(0)

    # If we're still here, scan what we found
    echo("Beginning scan of all %d previously retired repositories, "
    "get s'mo coffee..." % (retiredNum,))
    revivedRepos = checkRepos(retiredList, returnGood=True, userAgent=userAgent)
    echo("done!\n")

    # See if we found anything back
    revivedNumber = len(revivedRepos)    
    if revivedNumber < 1:
        echo("No previously retired repos are back online yet.\n\n" + done)
        sys.exit(0)
    if revivedNumber == 1:
        echo("Found 1 repo that is back from the dead!\n")
    else:
        echo("Found %d repos that are back from the dead!\n" % (revivedNumber,))

    for item in revivedRepos:
        # Now, move our files back in
        filename = item[0]
        liveFile = repoFolder + filename
        retiredFile = retiredFolder + filename
        echo("Reviving %s..." % (filename,))
        shutil.move(retiredFile, liveFile)
        echo("done.\n")
    
    # All done
    if revivedNumber == 1:
        echo("Successfully revived 1 repository.\n\n")
    else:
        echo("Successfully revived %d repositories.\n\n" % (revivedNumber,))

    # All done
    echo(done)
    sys.exit(0)

# And run main
if __name__ == "__main__":
    main()
