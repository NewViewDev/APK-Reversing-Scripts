#!/usr/bin/env python
import os
import sys
import argparse
import subprocess
import xml.etree.ElementTree as xmlParser

parser = argparse.ArgumentParser(description='****This script is meant to be run while inside a decompiled android apk folder that was decompiled using apktool.****')

parser.add_argument('-c', help='compile, sign, align and save apk to dist', nargs='?', const=os.getcwd())
parser.add_argument('-i', help='install app to connected device via adb', action='store_true')
# parser.add_argument('-r', help='run app on connected device via adb', action='store_true')
parser.add_argument('-q', help='do nothing and quit', action='store_true')

args = parser.parse_args()

if args.q == True:
    exit(0)

rootDir = os.getcwd()

if args.c is not None:
    rootDir = os.path.abspath(args.c)

if not os.path.exists(rootDir):
    sys.exit("Invalid path. Exiting.")

apkName = os.path.split(rootDir)[-1]
filePath = os.path.join(rootDir, 'dist', apkName)

def statusAlert(text):
    print("\n" + f"************ {text.upper()} ************" + "\n")

def compileAPK():
    #Compile to apk with parent dir name using APKtool. Apk will appear in dist
    try:
        subprocess.run(f"apktool b --use-aapt2 ./ -o {filePath}.apk", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            sys.exit("apktool compilation failure!\n")

    statusAlert("Apktool success")
    
    

    #Get debug signing key
    keyPath = ""
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        keyPath = os.path.expanduser("~/.android/debug.keystore")
    elif sys.platform.startswith('win'):
        keyPath = os.path.expanduser("~user\.android\debug.keystore")

    #Create debug signing keys if they do not exist
    if not os.path.exists(keyPath):
        create = input("\nNo debug keystore detected at common paths. Create one? (y/n): ")
        print("\n")
        if len(create) == 1 and create == 'y':
            try:
                subprocess.run(f"keytool -genkey -v -keystore {keyPath} -storepass android -alias androiddebugkey -keypass android -keyalg RSA -keysize 2048 -validity 10000", shell=True, check=True)
            except subprocess.CalledProcessError as e:
                sys.exit("Failed to generate debug.keystore\n")
        else:
            sys.exit("No known key. Exiting\n")

        statusAlert("Keygen success")
    
    #Zipalign compiled apk
    try:
        subprocess.run(f"zipalign -p -f 4 {filePath}.apk {filePath}Align.apk", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit("Align Failed.\n")

    statusAlert("Zipalign Success")

    # Sign using the new apksigner
    # ****** Must be done after zipalign instead of before like jarsigner ******
    try:
        subprocess.run(f"apksigner sign --ks-pass pass:android --ks {keyPath} {filePath}Align.apk", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit("Failed to sign file.\n")

    statusAlert("file sign success")

    # Verify that signature is valid
    subprocess.run(f"apksigner verify --print-certs {filePath}Align.apk", shell=True)
    statusAlert("Apk Complete")
    print("\n")
    #Remove Unaligned apk
    os.remove(f"{filePath}.apk")

#Return package name and activities
#CURRENTLY JUST RETURNS NAME
def getPackageInfo():
    manifestTree = xmlParser.parse(os.path.join(rootDir, "AndroidManifest.xml"))
    packageName = manifestTree.getroot().get("package")
    return packageName

def install():
    runTarget = os.path.join(rootDir, "dist", f"{apkName}Align.apk")

    #Install aligned apk to connected phone
    try:
        subprocess.run(f"adb install {runTarget}", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit("Failed to install file to device.\n")

    statusAlert("Install Success")

def run():
    #Parse AppManifest to get package to run the correct app on device
    packageName = getPackageInfo()

    # if notinstalled, offer to install
    try:
        subprocess.check_output(f"adb shell pm path {packageName}", shell=True)
    except subprocess.CalledProcessError as e:
        print(e.output)
        shouldInstall = input("\nThis package was not found on device. Run install command? (y/n): ")
        if len(shouldInstall) == 1 and shouldInstall == 'y':
            install()
        else:
            sys.exit("Please verify that the package is installed before running.")

    #Simulate tap to launch app
    # subprocess.run(f"adb shell am start -D -n {packageName}/{activity}", shell=True)

if len(sys.argv) == 1 or args.c is not None:
    compileAPK()
if args.i is True:
    install()
if args.r is True:
    run()