#!/usr/bin/env python

import json, sys
import urllib2
import rfc822, datetime, time
import os

from optparse import OptionParser, OptionGroup

DOWNLOAD_URL = 'downloadUrl'
PACKAGE = 'package'
VERSION_CODE = 'versionCode'
CHANGELOG = 'changelog'

APK_CONTENT_TYPE = 'application/vnd.android.package-archive'

class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"

class VersionListException(Exception):
    pass

class VersionList:
    """AppUpdateChecker JSON file generator / updater

    This creates and updates the JSON file read by AppUpdateChecker, as well as allows
    a file to be verified to ensure that it's constructed properly.
    """
    versions = None
    package = None

    def __init__(self, json_file=None):
        self.json_file = json_file
        if json_file:
            self.json = json.load(json_file)
            self.parse()

    def parse(self):
        if not self.json_file:
            return

        if type(self.json) != dict:
            return
        self.versions = dict(self.json)
        if PACKAGE in self.versions:
            self.package = self.versions[PACKAGE]
            del self.versions[PACKAGE]

    def verify(self, online=False):
        """Returns a tuple of verification, error message
        
        Raises VersionListException if the list hasn't been loaded"""

        if not self.json_file:
            raise VersionListException("must load a version list file first")

        ver = self.versions
        if type(ver) != dict:
            return (False,"Document is not a JSON object")

        if not self.package:
            return (False,"missing %s key" % PACKAGE)
        if DOWNLOAD_URL not in self.package:
            return (False,"missing %s key in %s object" % (DOWNLOAD_URL, PACKAGE))
        
        for code, info in ver.iteritems():
            if type(info) != dict:
                return (False,"value for version '%s' is not a JSON object" % code)
            if type(ver[code][VERSION_CODE]) != int:
                return (False,"version code in key %s of version '%s' is not an int" % (VERSION_CODE, code))
            if type(ver[code][CHANGELOG]) != list:
                return (False, "key %s in version '%s' is not a list" % (CHANGELOG, code))

        if online:
            return self.verify_online()

        return (True, None)

    def download_url(self):
        return self.package[DOWNLOAD_URL]

    def version_latest(self):
        ver = self.versions_sorted()[-1]
        return (ver, self.versions[ver])

    def versions_sorted(self):
        """Retrieves a sorted list of all the version names, sorted by version code
        
        Raises VersionListException if the list hasn't been loaded"""
        if not self.json_file:
            raise VersionListException("must load a version list file first")

        return sorted(self.versions, key=lambda ver: self.versions[ver][VERSION_CODE])

    def verify_online(self):
        url = self.download_url()

        res = urllib2.urlopen(HeadRequest(url))

        if res.code != 200:
            return (False, "%d %s" % (res.code, res.msg))

        sys.stderr.writelines("HEAD %s returned %d %s\n" % (url, res.code, res.msg))

        content_type = res.headers['content-type']
        if APK_CONTENT_TYPE != content_type:
            sys.stderr.writelines("warning: content type returned by %s should be %s, not %s\n" % (url, APK_CONTENT_TYPE, content_type))

        last_modified = res.headers['last-modified']
        if last_modified:
            last_modified = datetime.datetime.fromtimestamp(time.mktime(rfc822.parsedate(last_modified)))
        sys.stderr.writelines("last modified %s\n" % last_modified)

        size = res.headers['content-length']
        if size < 4000:
            return (False, "content length of %s was less than 4k." % url)

        res.close()

        return (True, None)

    def write_json(self, out):
        j = dict(self.versions)
        j[PACKAGE] = self.package
        json.dump(j, out, indent=2)

    def add_release(self, ver_code, ver_name, changelog=[]):
        if not self.versions:
            self.versions = {}
        if ver_name in self.versions.keys():
            raise VersionListException("version '%s' already exists" % ver_name)
        self.versions[ver_name] = {VERSION_CODE: int(ver_code), CHANGELOG: changelog}
        

if __name__=='__main__':
    parser = OptionParser(usage="usage: %prog [-f JSON_FILE] [options] COMMAND [args]",
            description="Generate or update a static json AppUpdateChecker file."
            "\t\t\t\tCOMMAND is one of:\t\t\t\t\t\t\t\t"
            "verify\t\t\t\t\t\tverify the given JSON_FILE"
            "\t\t\t\trelease\tCODE NAME 'CHANGELOG' ['CHANGELOG']\t\tadds a new release")


    parser.add_option("-f", "--file", dest="filename",
            help="read/write version information to FILE", metavar="FILE")

    parser.add_option("-d", "--verify-download", dest="online", action="store_true",
            help="when verifying, perform a HEAD request on the download URL to ensure it is valid")

    cmds = OptionGroup(parser, "Commands", "Commands have 0 or more arguments test")

    parser.add_option_group(cmds)

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    cmd = args[0]

    if 'verify' == cmd:
        if options.filename:
            inpt = open(options.filename)
        else:
            inpt = sys.stdin
        ver = VersionList(inpt)
        (res, err) = ver.verify(online=options.online)
        if res:
            print "verification succeeded: no errors found"
            latest, latest_info = ver.version_latest()
            print "Latest version is %s (%d)" % (latest, latest_info[VERSION_CODE])
        else:
            print "verification failed: %s" % err
        
    elif 'release' == cmd:
        if len(args) < 3:
            parser.print_help()
            sys.exit(1)

        if options.filename:
            try:
                inpt = open(options.filename)
            except IOError as e:
                # this is not ideal according to http://docs.python.org/howto/doanddont.html
                # but there's no good way to determine if it's a "file not found" or other error
                # based on the exception alone
                if not os.path.exists(options.filename):
                    inpt = None
                else:
                    raise e

            ver = VersionList(inpt)
            if inpt:
                ver.verify()
            
        else:
            ver = VersionList(sys.stdin)
            ver.verify()

        ver_code = args[1]
        ver_name = args[2]
        changelog = args[3:]
        try:
            ver.add_release(ver_code, ver_name, changelog)
            if options.filename:
                out = open(options.filename, 'w')
            ver.write_json(out)
        except VersionListException as e:
            sys.stderr.writelines("%s\n" % e)

