App Update Checker
==================

A simple non-Market way to keep your app updated.

All it requires to set up is a URL pointing to a JSON document describing your
app's changes.

It will compare its version code (from the manifest file) to the versions
listed in the JSON.  If there are newer version(s), it will provide the
changelog between the installed version and the latest version. The updater
checks against the versionCode, but displays the versionName.

While you can create your own OnAppUpdateListener to listen for new updates,
OnUpdateDialog is a handy implementation that displays a Dialog with a bulleted
list and a button to do the upgrade.

The JSON format looks like this:

    {
        "package": {
            "downloadUrl": "http://coolapp.example.com/myapp.apk"
        },

        "0.2": {
        "versionCode": 2,
        "changelog": ["New automatic update checker", "Improved template interactions"]
        },
        "0.1": {
        "versionCode": 1,
        "changelog": ["fixed crash"]
        }
    }

License
=======

AppUpdateChecker  
Copyright (C) 2011 [MIT Mobile Experience Lab][mel]

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

[mel]: http://mobile.mit.edu/
