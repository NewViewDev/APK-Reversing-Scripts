#!/usr/bin/env python
import os
import sys
import argparse
import subprocess
import xml.etree.ElementTree as xmlParser

parser = argparse.ArgumentParser(description='****This script is meant to be run while inside a decompiled android apk folder that was decompiled using apktool.****')

parser.add_argument('-c', help='compile, sign, align and save apk to dist', nargs='?', default=os.getcwd(), const=os.getcwd())
parser.add_argument('-r', help='install and run app', action='store_true')
parser.add_argument('-q', help='do nothing and quit', action='store_true')

args = parser.parse_args()

if args.q == True:
    exit(0)

#Get info for shell command run dirs and filenames
cwd = args.c
if not os.path.exists(cwd):
    print("Invalid path. Exiting.")

dirName = os.path.basename(cwd)

def statusAlert(text):
    print("\n" + f"************ {text.upper()} ************" + "\n")

def compileAPK():
    #Compile to apk with parent dir name. Apk will appear in dist
    print("\n")
    try:
        subprocess.run(f"apktool b --use-aapt2 ./ -o ./dist/{dirName}.apk", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            sys.exit("apktool compilation failure!\n")

    statusAlert("Apktool success")
    
    os.chdir("./dist")

    # Sign using newer apksigner
    # ****** Must be done after zipalign instead of before like jarsigner ******
    keyPath = ""
    if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
        keyPath = os.path.expanduser("~/.android/debug.keystore")
    elif sys.platform.startswith('win'):
        keyPath = os.path.expanduser("~user\.android\debug.keystore")

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
    
    try:
        subprocess.run(f"apksigner sign --ks-pass pass:android --ks {keyPath} {dirName}.apk", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit("Failed to sign file.\n")

    statusAlert("file sign success")

    subprocess.run(f"apksigner verify --print-certs {dirName}.apk", shell=True)

    #Align compiled apk
    try:
        subprocess.run(f"zipalign -p -f 4 {dirName}.apk {dirName}Align.apk", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit("Align Failed.\n")

    statusAlert("Zipalign Success")
    


    

    #Remove Unaligned apk
    os.remove(f"./{dirName}.apk")

def run():
    #Parse AppManifest to get package to run app on device
    manifestTree = xmlParser.parse(cwd + "\\AndroidManifest.xml")
    packageName = manifestTree.getroot().get("package")
    
    if os.path.basename(os.getcwd()) != "dist":
        os.chdir("./dist")

    #Install aligned apk to connected phone
    subprocess.run(f"adb install .\\{dirName}Align.apk", shell=True, check="True")

    #Simulate tap to launch app
    # subprocess.run(f"adb shell am start -D -n {packageName}/{activity}", shell=True)

if args.c is not None:
    compileAPK()
if args.r is True:
    run()